/**
 * Project: QuakeGuard - Professional Seismic Node
 * Version: 2.1.0
 * Target Hardware: ESP32-C3 SuperMini + ADXL345 + NEO-6M (JLCPCB)
 * Author: GiZano
 *
 * CHANGELOG:
 * - v2.1.0: End-to-end latency tracking, ESP32 free heap monitoring, RSSI
 * and GNSS satellite count telemetry exposed for Grafana Observability.
 */

#include <Adafruit_ADXL345_U.h>
#include <Adafruit_Sensor.h>
#include <Arduino.h>
#include <ArduinoJson.h>
#include <HTTPClient.h>
#include <Preferences.h>
#include <PubSubClient.h>
#include <WiFi.h>
#include <WiFiManager.h>
#include <Wire.h>
#include <time.h>

// --- Cryptographic Libraries (MbedTLS) ---
#include "Calibration.h"
#include "DetectionCore.h"
#include "GnssModule.h"
#include "SerialFallback.h"
#include "mbedtls/ctr_drbg.h"
#include "mbedtls/ecdsa.h"
#include "mbedtls/entropy.h"
#include "mbedtls/error.h"
#include "mbedtls/pk.h"
#include <array>
#include <chrono>
#include <vector>

// --------------------------------------------------------------------------
// FIRMWARE VERSION (printed at boot for field identification)
// --------------------------------------------------------------------------
constexpr const char* FIRMWARE_VERSION = "2.1.0";

// --------------------------------------------------------------------------
// HARDWARE & SERVER CONFIGURATION
// --------------------------------------------------------------------------
constexpr int I2C_SDA_PIN = 7;
constexpr int I2C_SCL_PIN = 8;
constexpr int I2C_CLOCK_SPEED = 100000;

constexpr int LED_BLUE_PIN =
    10; // connection state: double->wifi, single->server, solid->connected
constexpr int LED_RED_PIN = 3; // quake detected: on 3 s
constexpr int BOOT_BUTTON_PIN = 9;  // GPIO 0 — BOOT button (active LOW)
constexpr unsigned long RESET_HOLD_MS = 5000;  // 5 seconds hold to trigger factory reset

#ifndef SERVER_HOST
#define SERVER_HOST "your-tunnel-id.trycloudflare.com"
#endif
#ifndef SERVER_PORT
#define SERVER_PORT 80
#endif
#ifndef SERVER_PROTOCOL
#define SERVER_PROTOCOL "https"
#endif
#ifndef SERVER_PATH
#define SERVER_PATH "/readings/"
#endif
#ifndef SERVER_REGISTER_PATH
#define SERVER_REGISTER_PATH "/devices/register"
#endif
#ifndef MQTT_BROKER_HOST
#error "MQTT_BROKER_HOST is missing! Add it to esp32_config.env"
#endif
#ifndef MQTT_BROKER_PORT
#define MQTT_BROKER_PORT 8883
#endif
#ifndef MQTT_USERNAME
#error "MQTT_USERNAME is missing! Add it to esp32_config.env"
#endif
#ifndef MQTT_PASSWORD
#error "MQTT_PASSWORD is missing! Add it to esp32_config.env"
#endif

#ifndef SERIAL_FALLBACK_ENABLED
#define SERIAL_FALLBACK_ENABLED 1
#endif
#ifndef SERIAL_FALLBACK_MARKER
#define SERIAL_FALLBACK_MARKER "[QG:FB]"
#endif

#ifndef ENROLLMENT_TOKEN
#ifndef __INTELLISENSE__
                               // 1. If the REAL compiler doesn't see the token,
                               // crash the build to protect us!
#error                                                                         \
    "CRITICAL BUILD ERROR: ENROLLMENT_TOKEN is missing! Add it to esp32_config.env"
#else
                               // 2. If VSCode's UI is looking at the file, give
                               // it a fake token so it stops crying on line
                               // 168!
#define ENROLLMENT_TOKEN "vscode_dummy_token"
#endif
#endif

// Global Dynamic Sensor ID
static int globalSensorID = 0;
Adafruit_ADXL345_Unified accel = Adafruit_ADXL345_Unified(12345);

// LED state (v2.0.0) — blue dimmed via PWM, red 3 s pulse
static volatile unsigned long g_redLedOffAt = 0; // NOSONAR
static constexpr int BLUE_BRIGHT =
    100; // 0-255, ~40% to slightly dim the blue LED (was 255)

inline void triggerQuakeLed() {
  digitalWrite(LED_RED_PIN, HIGH);
  Serial.println("[LED] Red ON (quake) for 3 s");
  g_redLedOffAt = millis() + 3000;
}

inline void updateConnectionLed(bool wifiConnected, bool serverConnected) {
  // Red LED auto-off
  if (g_redLedOffAt != 0 && (long)(millis() - g_redLedOffAt) >= 0) {
    digitalWrite(LED_RED_PIN, LOW);
    g_redLedOffAt = 0;
    Serial.println("[LED] Red OFF");
  }
  // Blue LED: PWM dimmed (analogWrite) — double blink WiFi, single blink
  // server, solid connected
  if (!wifiConnected) {
    unsigned long phase = millis() % 1000;
    bool on = (phase < 100) || (phase >= 200 && phase < 300);
    analogWrite(LED_BLUE_PIN, on ? BLUE_BRIGHT : 0);
  } else if (!serverConnected) {
    unsigned long phase = millis() % 1000;
    bool on = (phase < 200);
    analogWrite(LED_BLUE_PIN, on ? BLUE_BRIGHT : 0);
  } else {
    analogWrite(LED_BLUE_PIN, BLUE_BRIGHT);
  }
}

// Boot self-test: blink both LEDs to verify wiring (red active-HIGH:
// GPIO3->R3->D3->GND)
inline void ledBootTest() {
  Serial.println("[LED] Boot test: blue + red");
  for (int i = 0; i < 2; i++) {
    digitalWrite(LED_BLUE_PIN, HIGH); // full bright for test
    digitalWrite(LED_RED_PIN, HIGH);
    delay(250);
    digitalWrite(LED_BLUE_PIN, LOW);
    digitalWrite(LED_RED_PIN, LOW);
    delay(250);
  }
  // leave both off, updateConnectionLed will drive blue from now on
  analogWrite(LED_BLUE_PIN, 0);
}

// --------------------------------------------------------------------------
// RTOS & DSP DEFINITIONS
// --------------------------------------------------------------------------
QueueHandle_t eventQueue;

struct SeismicEvent {
  float magnitude;
  unsigned long event_millis;
};

constexpr float TRIGGER_RATIO = 1.8f;
constexpr float NOISE_FLOOR = 0.04f;
constexpr float HPF_ALPHA = 0.9f;

// Bounded in-memory retention for events with no delivery path.
constexpr size_t RETENTION_CAPACITY = 100;

// --------------------------------------------------------------------------
// CRYPTO SUBSYSTEM
// --------------------------------------------------------------------------
static Preferences preferences;

class CryptoContext {
  mbedtls_entropy_context entropy_;
  mbedtls_ctr_drbg_context ctr_drbg_;
  mbedtls_pk_context pk_context_;

public:
  void init();
  void getPublicKeyHex(char *out_hex_key, size_t out_max_len);
  void signMessage(const char *message, char *out_hex_sig, size_t out_max_len);
};

CryptoContext &crypto() {
  static CryptoContext c;
  return c;
}

void CryptoContext::init() {
  mbedtls_entropy_init(&entropy_);
  mbedtls_ctr_drbg_init(&ctr_drbg_);
  mbedtls_pk_init(&pk_context_);

  constexpr const char pers[] = "quake_guard_signer";
  mbedtls_ctr_drbg_seed(&ctr_drbg_, mbedtls_entropy_func, &entropy_,
                        (const unsigned char *)pers, sizeof(pers) - 1);

  preferences.begin("quake-keys", false);

  if (!preferences.isKey("priv_key")) {
    Serial.println("[SEC] Generating New ECDSA Key Pair...");
    mbedtls_pk_setup(&pk_context_, mbedtls_pk_info_from_type(MBEDTLS_PK_ECKEY));
    mbedtls_ecp_gen_key(MBEDTLS_ECP_DP_SECP256R1, mbedtls_pk_ec(pk_context_),
                        mbedtls_ctr_drbg_random, &ctr_drbg_);
    std::array<unsigned char, 128> priv_buf;
    int ret = mbedtls_pk_write_key_der(&pk_context_, priv_buf.data(),
                                       priv_buf.size());
    preferences.putBytes("priv_key", priv_buf.data() + priv_buf.size() - ret,
                         ret);
    Serial.println("[SEC] Keys Generated.");
  } else {
    Serial.println("[SEC] Loading Existing Keys...");
    size_t len = preferences.getBytesLength("priv_key");
    std::vector<uint8_t> buf(len);
    preferences.getBytes("priv_key", buf.data(), len);
    mbedtls_pk_parse_key(&pk_context_, buf.data(), len, NULL, 0);
  }
}

void CryptoContext::getPublicKeyHex(char *out_hex_key, size_t out_max_len) {
  std::array<unsigned char, 128> pub_buf;
  int ret =
      mbedtls_pk_write_pubkey_der(&pk_context_, pub_buf.data(), pub_buf.size());
  int len = ret;
  int start_index = pub_buf.size() - len;

  if (out_max_len > static_cast<size_t>(len * 2)) {
    for (int i = 0; i < len; i++) {
      snprintf(out_hex_key + (i * 2), out_max_len - (i * 2), "%02x", // NOSONAR
               pub_buf[start_index + i]);
    }
  } else if (out_max_len > 0) {
    out_hex_key[0] = '\0';
  }
}

void CryptoContext::signMessage(const char *message, char *out_hex_sig,
                                size_t out_max_len) {
  std::array<unsigned char, 32> hash;
  std::array<unsigned char, MBEDTLS_ECDSA_MAX_LEN> sig;
  size_t sig_len = 0;
  mbedtls_md_context_t ctx;
  mbedtls_md_init(&ctx);
  mbedtls_md_setup(&ctx, mbedtls_md_info_from_type(MBEDTLS_MD_SHA256), 0);
  mbedtls_md_starts(&ctx);
  mbedtls_md_update(&ctx, (const unsigned char *)message, strlen(message)); // NOSONAR
  mbedtls_md_finish(&ctx, hash.data());
  mbedtls_md_free(&ctx);
  mbedtls_pk_sign(&pk_context_, MBEDTLS_MD_SHA256, hash.data(), 0, sig.data(),
                  &sig_len, mbedtls_ctr_drbg_random, &ctr_drbg_);

  if (out_max_len > sig_len * 2) {
    for (size_t i = 0; i < sig_len; i++) {
      snprintf(out_hex_sig + (i * 2), out_max_len - (i * 2), "%02x", // NOSONAR
               sig[i]);
    }
  } else if (out_max_len > 0) {
    out_hex_sig[0] = '\0';
  }
}

// --------------------------------------------------------------------------
// PROVISIONING LOGIC
// --------------------------------------------------------------------------
bool performProvisioning() {
  Serial.println("\n[PROV] Starting Device Handshake...");
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[PROV] Error: No WiFi connection.");
    return false;
  }

  HTTPClient http;
  WiFiClientSecure secureClient;
  secureClient.setInsecure(); // Bypass Root CA validation for Let's Encrypt
                              // (Tailscale/Cloudflare)

  // SERVER_HOST may be configured with or without a leading scheme; normalize
  // it so a "https://host" value cannot produce "https://https://host". The
  // actual request protocol comes from SERVER_PROTOCOL below.
  auto host = String(SERVER_HOST);
  auto scheme = host.indexOf("://");
  if (scheme != -1) {
    host.remove(0, scheme + 3);
  }

  String url = String(SERVER_PROTOCOL) + "://" + host;
  int serverPort = SERVER_PORT;
  if (serverPort != 80 && serverPort != 443) {
    url += ":" + String(serverPort);
  }
  url += SERVER_REGISTER_PATH;

  Serial.printf("[PROV] Connecting to: %s\n", url.c_str());

  if (url.startsWith("https")) {
    http.begin(secureClient, url);
  } else {
    http.begin(url);
  }
  http.addHeader("Content-Type", "application/json");
  http.addHeader("ngrok-skip-browser-warning", "true");
  http.setTimeout(15000);

  JsonDocument doc;
  std::array<char, 256> pub_hex;
  crypto().getPublicKeyHex(pub_hex.data(), pub_hex.size());
  doc["public_key_hex"] = pub_hex.data();
  doc["mac_address"] = WiFi.macAddress();
  doc["enrollment_token"] = ENROLLMENT_TOKEN;

#ifdef GNSS_ENABLED
  // GNSS-ready: report the real fix when available, else the last-known fix
  // persisted in NVS. If neither exists, use fallback coords from .env
  // (indoor testing) or omit -> backend assigns "Unknown Region".
  GnssFix fix;
  if (gnss().getFix(fix)) {
    doc["latitude"] = fix.latitude;
    doc["longitude"] = fix.longitude;
    Serial.printf("[PROV] Sending fix: %.5f, %.5f (from %s)\n", fix.latitude,
                  fix.longitude, fix.from_storage ? "NVS" : "GNSS");
  } else {
#ifdef GNSS_FALLBACK_LAT
    doc["latitude"] = GNSS_FALLBACK_LAT;
    doc["longitude"] = GNSS_FALLBACK_LON;
    Serial.printf(
        "[PROV] Using fallback coords: %.5f, %.5f (GNSS no-fix, indoor)\n",
        (double)GNSS_FALLBACK_LAT, (double)GNSS_FALLBACK_LON);
#else
    Serial.println("[PROV] No GNSS fix available: omitting coordinates");
#endif
  }
#else
#ifdef GNSS_FALLBACK_LAT
  doc["latitude"] = GNSS_FALLBACK_LAT;
  doc["longitude"] = GNSS_FALLBACK_LON;
  Serial.printf("[PROV] GNSS disabled, using ENV fallback coords: %.5f, %.5f\n",
                (double)GNSS_FALLBACK_LAT, (double)GNSS_FALLBACK_LON);
#else
  Serial.println("[PROV] GNSS disabled: omitting coordinates (backend assigns "
                 "Unknown Region)");
#endif
#endif

  String requestBody;
  serializeJson(doc, requestBody);

  int httpResponseCode = http.POST(requestBody);

  if (httpResponseCode == 200 || httpResponseCode == 201) {
    String response = http.getString();
    JsonDocument resDoc;
    deserializeJson(resDoc, response);

    int newID = resDoc["sensor_id"];
    if (newID > 0) {
      preferences.begin("quake-config", false);
      preferences.putInt("sensor_id", newID);
      preferences.end();
      globalSensorID = newID;
      Serial.printf("[PROV] SUCCESS! Assigned Sensor ID: %d\n", globalSensorID);
      Serial.printf("[PROV] Public key: %s\n", pub_hex.data());
      http.end();
      return true;
    }
  } else {
    Serial.printf("[PROV] Registration Failed. HTTP Code: %d\n",
                  httpResponseCode);
  }
  http.end();
  return false;
}

// --------------------------------------------------------------------------
// TASK 1: SENSOR ACQUISITION
// --------------------------------------------------------------------------
void sensorTask(void *pvParameters) { // NOSONAR
  sensors_event_t event;

  // Pure-C++ STA/LTA core, shared with the host SIL validation (same source).
  SeismicDetector detector(HPF_ALPHA, TRIGGER_RATIO, NOISE_FLOOR);

  Serial.println("[SENSOR] Task Active. Stabilizing and filling buffers...");

  TickType_t xLastWakeTime = xTaskGetTickCount();
  const TickType_t xFrequency = pdMS_TO_TICKS(10); // Exactly 100Hz

  for (;;) {
    vTaskDelayUntil(&xLastWakeTime, xFrequency);
    accel.getEvent(&event);
    float raw_mag = SeismicDetector::norm3(
        event.acceleration.x, event.acceleration.y, event.acceleration.z);

    // Clock-injected: the detector receives the same millis() the firmware
    // would use.
    if (detector.push(raw_mag, millis())) {
      Serial.printf("[SENSOR] EARTHQUAKE! Ratio: %.2f (Mag: %.3f G)\n",
                    detector.lastRatio(), detector.lastSTA());
      // The backend expects the physical PGA (m/s^2 or Gs) for the magnitude
      // calculation, not the STA/LTA trigger ratio!
      SeismicEvent evt = {detector.lastSTA(), millis()};
      xQueueSend(eventQueue, &evt, 0);
    }
  }
}

// --------------------------------------------------------------------------
// TASK 2: NETWORK DISPATCH (MQTT + USB SERIAL FALLBACK)
// --------------------------------------------------------------------------
static void deliverEvent(PubSubClient &mqttClient, DeliveryPath path, int val,
                         time_t evt_time, const char *sig,
                         long long evt_time_ms = 0);

#if SERIAL_FALLBACK_ENABLED
static void drainRetention(RetentionRing<RETENTION_CAPACITY> &retention,
                           PubSubClient &mqttClient, bool mqttUp, bool usbHost,
                           bool timeValid, time_t epochAtSync,
                           unsigned long millisAtSync) {
  if (retention.empty() || !timeValid)
    return;
  DeliveryPath path =
      decidePath(mqttUp && timeValid, usbHost,
                 timeValid); // NOSONAR(cpp:S5811) - using enum requires C++20
  if (path != DeliveryPath::MQTT && path != DeliveryPath::SERIAL_CDC)
    return;
  SerialEvent retainedEvt;
  while (retention.pop(retainedEvt)) {
    time_t report_time = epochAtSync + (millis() - millisAtSync) / 1000;
    std::array<char, 64> payload;
    snprintf(payload.data(), payload.size(), "%d:%ld", retainedEvt.value, // NOSONAR
             (long)report_time);
    std::array<char, MBEDTLS_ECDSA_MAX_LEN * 2 + 1> sig;
    crypto().signMessage(payload.data(), sig.data(), sig.size());
    long long report_time_ms =
        ((long long)epochAtSync * 1000) + (millis() - millisAtSync);
    deliverEvent(mqttClient, path, retainedEvt.value, report_time, sig.data(),
                 report_time_ms);
    triggerQuakeLed();
  }
}
#endif

static void deliverEvent(PubSubClient &mqttClient, DeliveryPath path, int val,
                         time_t evt_time, const char *sig,
                         long long evt_time_ms) {
  int free_heap = ESP.getFreeHeap();
  int rssi = WiFi.RSSI();
  int gnss_satellites = 0;
#ifdef GNSS_ENABLED
  gnss_satellites = gnss().getSatellites();
#endif

  if (path == DeliveryPath::MQTT) { // NOSONAR(cpp:S5811)
    JsonDocument doc;
    doc["value"] = val;
    doc["sensor_id"] = globalSensorID;
    doc["device_timestamp"] = evt_time;
    if (evt_time_ms > 0)
      doc["device_timestamp_ms"] = evt_time_ms;
    doc["signature_hex"] = sig;

    // System Telemetry (v2.1.0 Grafana)
    doc["free_heap"] = free_heap;
    doc["rssi"] = rssi;
#ifdef GNSS_ENABLED
    doc["gnss_satellites"] = gnss_satellites;
#endif

    std::array<char, 512> json;
    serializeJson(doc, json.data(), json.size());

    // FIRE AND FORGET! Milliseconds instead of HTTP round-trips!
    if (mqttClient.publish("quakeguard/telemetry", json.data())) {
      Serial.println("[NET] MQTT Publish OK.");
    } else {
      Serial.println("[NET] MQTT Publish FAILED.");
    }
  } else {
    // USB serial fallback: machine-readable frame on the CDC port.
    Serial.print(buildSerialFrame(SERIAL_FALLBACK_MARKER, val, globalSensorID,
                                  (long)evt_time, sig, evt_time_ms, free_heap,
                                  rssi, gnss_satellites)
                     .c_str());
    Serial.println();
    Serial.println("[NET] Serial Fallback Publish OK.");
  }
}

void networkTask(void *pvParameters) { // NOSONAR
  WiFiClient espClientPlain;
  WiFiClientSecure espClientSecure;
  espClientSecure.setInsecure();
  
  Client* baseClient = (MQTT_BROKER_PORT == 8883) ? (Client*)&espClientSecure : (Client*)&espClientPlain;
  PubSubClient mqttClient(*baseClient);

  mqttClient.setServer(MQTT_BROKER_HOST, MQTT_BROKER_PORT);
  mqttClient.setBufferSize(1024);

  // NTP sync happens opportunistically; event dispatch never blocks on it.
  configTime(0, 0, "pool.ntp.org", "time.nist.gov");

#if SERIAL_FALLBACK_ENABLED
  // Software clock anchored at the first successful NTP sync, so retained
  // events keep a valid wall time even after WiFi drops.
  time_t epochAtSync = 0;
  unsigned long millisAtSync = 0;
  bool timeValid = false;

  RetentionRing<RETENTION_CAPACITY> retention;
#endif

  SeismicEvent receivedEvt;
  unsigned long lastMqttAttempt = 0;
  int reconnectAttempts = 0;
  unsigned long backoffDelay = 0;

  for (;;) {
    mqttClient.loop(); // Process incoming keepalives

    // Opportunistic MQTT (re)connection, throttled with Exponential Backoff
    bool mqttUp = mqttClient.connected();
    // Blue LED: double blink WiFi, single blink server, solid connected (also
    // handles red auto-off)
    updateConnectionLed(WiFi.status() == WL_CONNECTED, mqttUp);
    if (!mqttUp && WiFi.status() == WL_CONNECTED &&
        (millis() - lastMqttAttempt > backoffDelay)) {
      lastMqttAttempt = millis();
      std::array<char, 64> clientId;
      snprintf(clientId.data(), clientId.size(), "QuakeGuard-%s", // NOSONAR
               WiFi.macAddress().c_str());
      if (mqttClient.connect(clientId.data(), MQTT_USERNAME, MQTT_PASSWORD)) {
        Serial.println("[NET] MQTT Reconnected.");
        mqttUp = true;
        reconnectAttempts = 0;
        backoffDelay = 0; // immediate next check
      } else {
        reconnectAttempts++;
        int exp_limit = reconnectAttempts > 5 ? 5 : reconnectAttempts;
        unsigned long baseDelay = 5000 * (1 << exp_limit);
        backoffDelay =
            baseDelay +
            random(0, 3000); // Truncated Exponential Backoff + Jitter
        Serial.printf("[NET] MQTT Connect failed. Backoff: %lu ms\n",
                      backoffDelay);
      }
    }

#if SERIAL_FALLBACK_ENABLED
    if (!timeValid) {
      auto now = std::chrono::system_clock::now();
      time_t t = std::chrono::system_clock::to_time_t(now);
      if (t > 1600000000) {
        epochAtSync = t;
        millisAtSync = millis();
        timeValid = true;
        Serial.println("[NET] NTP time synchronized.");
      }
    }

#ifdef GNSS_ENABLED
    if (timeValid && gnss().hasPpsFix()) {
      // PPS discipline: the PPS pulse marks exactly the top of the second.
      // We can realign our millisAtSync to the last PPS pulse to achieve ms
      // precision.
      static unsigned long lastDisciplinedPps = 0;
      unsigned long ppsMs = gnss().getLastPpsMs();
      if (ppsMs != lastDisciplinedPps) {
        // Determine which second this PPS corresponds to by rounding to nearest
        // second
        time_t ppsEpoch = epochAtSync + (ppsMs - millisAtSync + 500) / 1000;
        epochAtSync = ppsEpoch;
        millisAtSync = ppsMs;
        lastDisciplinedPps = ppsMs;
      }
    }
#endif

    bool usbHost =
        Serial.isConnected(); // HWCDC: true only with a real USB host

    // Drain retained events to a path that just became available. Events
    // are re-signed with the current wall time (reporting time) so the
    // backend's +/-300 s replay window accepts the retransmission.
    drainRetention(retention, mqttClient, mqttUp, usbHost, timeValid,
                   epochAtSync, millisAtSync);
#endif

    // Wait for a seismic event from the queue (up to 100 ms).
    if (xQueueReceive(eventQueue, &receivedEvt, pdMS_TO_TICKS(100)) == pdTRUE) {
      if (globalSensorID == 0)
        continue; // Unregistered

      const std::chrono::system_clock::time_point now_chrono =
          std::chrono::system_clock::now();
      unsigned long age_ms = millis() - receivedEvt.event_millis;
      time_t evt_time = std::chrono::system_clock::to_time_t(
          now_chrono - std::chrono::milliseconds(age_ms));
      long long evt_time_ms =
          std::chrono::duration_cast<std::chrono::milliseconds>(
              (now_chrono - std::chrono::milliseconds(age_ms))
                  .time_since_epoch())
              .count();

      auto val = static_cast<int>(receivedEvt.magnitude * 100);
      std::array<char, 64> payload;
      snprintf(payload.data(), payload.size(), "%d:%ld", val, (long)evt_time); // NOSONAR
      std::array<char, MBEDTLS_ECDSA_MAX_LEN * 2 + 1> sig;
      crypto().signMessage(payload.data(), sig.data(), sig.size());

#if SERIAL_FALLBACK_ENABLED
      {
        DeliveryPath path = decidePath(mqttUp && timeValid, usbHost, timeValid);
        switch (path) { // NOSONAR(cpp:S5811) - using enum requires C++20, ESP32
                        // gnu++11
        case DeliveryPath::MQTT:
        case DeliveryPath::SERIAL_CDC:
          deliverEvent(mqttClient, path, val, evt_time, sig.data(), evt_time_ms);
          triggerQuakeLed();
          break;
        case DeliveryPath::RETAIN:
          retention.push({val, static_cast<long>(evt_time)});
          Serial.println("[NET] No delivery path: event retained in ring.");
          break;
        }
      }
#else
      deliverEvent(mqttClient, DeliveryPath::MQTT, val, evt_time, sig.data(),
                   evt_time_ms); // NOSONAR(cpp:S5811)
      triggerQuakeLed();
#endif
    }
  }
}

// --------------------------------------------------------------------------
// TASK 3 (OPTIONAL): GNSS ACQUISITION
// --------------------------------------------------------------------------
#ifdef GNSS_ENABLED
void gnssTask(void *pvParameters) { // NOSONAR
  gnss().begin();
  for (;;) {
    gnss().loop();
    vTaskDelay(pdMS_TO_TICKS(50));
  }
}
#endif

// --------------------------------------------------------------------------
// TASK 4: FACTORY RESET MONITOR (BOOT BUTTON GPIO 0)
// --------------------------------------------------------------------------
void resetTask(void *pvParameters) { // NOSONAR
  pinMode(BOOT_BUTTON_PIN, INPUT_PULLUP);
  for (;;) {
    vTaskDelay(pdMS_TO_TICKS(100));
    if (digitalRead(BOOT_BUTTON_PIN) != LOW) {
      continue;
    }
    unsigned long pressStart = millis();
    while (digitalRead(BOOT_BUTTON_PIN) == LOW) {
      if ((millis() - pressStart) >= RESET_HOLD_MS) {
        Serial.println("[RESET] BOOT button held >5s — Factory Reset!");
        Serial.println("[RESET] Clearing WiFi credentials and sensor config...");
        WiFiManager wm;
        wm.resetSettings();
        preferences.begin("quake-config", false);
        preferences.remove("sensor_id");
        preferences.end();
        Serial.println("[RESET] Done. Rebooting into AP mode...");
        delay(500);
        ESP.restart();
      }
      vTaskDelay(pdMS_TO_TICKS(50));
    }
  }
}

// --------------------------------------------------------------------------
// MAIN ENTRY POINTS
// --------------------------------------------------------------------------
void setup() {
  Serial.begin(115200);
  delay(2000);

  // LEDs: blue (10) connection state, red (3) quake indicator
  pinMode(LED_BLUE_PIN, OUTPUT);
  pinMode(LED_RED_PIN, OUTPUT);
  digitalWrite(LED_BLUE_PIN, LOW);
  digitalWrite(LED_RED_PIN, LOW);
  ledBootTest(); // verify wiring: 2x blink both LEDs

  Serial.printf("\n\n[BOOT] QuakeGuard v%s\n", FIRMWARE_VERSION);

  crypto().init();

  preferences.begin("quake-config", false);
  globalSensorID = preferences.getInt("sensor_id", 0);
  preferences.end();

  if (globalSensorID > 0) {
    Serial.printf("[BOOT] Device Registered. ID: %d\n", globalSensorID);
  } else {
    Serial.println("[BOOT] Device UNREGISTERED. Entering Provisioning Mode...");
  }

  WiFiManager wm;
  wm.setConfigPortalTimeout(180);

  // Genera la Public Key per mostrarla a schermo nel Captive Portal
  std::array<char, 128> pub_hex;
  crypto().getPublicKeyHex(pub_hex.data(), pub_hex.size());
  
  String customHtml = 
    "<div style='margin-top:20px; padding:15px; border-radius:8px; background:#f8f9fa; border:1px solid #dee2e6; text-align:center; font-family:sans-serif;'>"
    "  <h2 style='color:#333; margin-top:0;'>Benvenuto in QuakeGuard!</h2>"
    "  <p style='color:#555;'>Per configurare questo nodo, scarica prima l'app mobile ufficiale.</p>"
    "  <a href='https://github.com/GiZano/QuakeGuard/releases/latest/download/quakeguard.apk' "
    "     style='display:inline-block; padding:12px 24px; background:#0d6efd; color:#fff; text-decoration:none; border-radius:50px; font-weight:bold; margin-bottom:15px;'>"
    "     &#x1F4F1; Scarica l'App (APK)"
    "  </a>"
    "  <p style='font-size:0.9em; color:#666; margin-bottom:5px;'>Copia questa Public Key e incollala nell'app in fase di Enrollment:</p>"
    "  <div style='background:#e9ecef; padding:10px; border-radius:4px; font-family:monospace; word-break:break-all; font-weight:bold; color:#d63384; font-size:1.1em;'>"
    + String(pub_hex.data()) + 
    "  </div>"
    "</div><hr/>";
    
  WiFiManagerParameter custom_element(customHtml.c_str());
  wm.addParameter(&custom_element);

  Serial.println("[NET] Initializing WiFiManager Captive Portal...");
  if (!wm.autoConnect("QuakeGuard-Setup")) {
    Serial.println("[NET] WiFi Failed. Offline Mode.");
  } else {
    Serial.println("[NET] WiFi Connected.");
    if (globalSensorID == 0) {
      performProvisioning();
    }
  }

  Wire.setPins(I2C_SDA_PIN, I2C_SCL_PIN);
  Wire.begin();
  Wire.setClock(I2C_CLOCK_SPEED);
  delay(100);

  // ADXL345 init with retry — JLCPCB J3 on GPIO 7/8, allow cold-boot settling
  bool adxlOk = false;
  for (int attempt = 0; attempt < 3; attempt++) {
    if (accel.begin(0x53) || accel.begin(0x1D)) {
      adxlOk = true;
      break;
    }
    Serial.printf("[SENSOR] ADXL init failed, retry %d/3...\n", attempt + 1);
    // blink red rapidly to signal I2C issue
    for (int i = 0; i < 3; i++) {
      digitalWrite(LED_RED_PIN, HIGH);
      delay(80);
      digitalWrite(LED_RED_PIN, LOW);
      delay(80);
    }
    delay(500);
  }
  if (!adxlOk) {
    Serial.println("[FATAL] Sensor Hardware Error — check J3 wiring, 3.3V, SDA "
                   "7/SCL 8, or try re-seating ADXL module.");
    // do not halt forever: keep networkTask alive so blue LED and provisioning
    // can be observed
    digitalWrite(LED_RED_PIN, HIGH); // solid red = sensor fault
    // still create tasks, sensorTask will keep reporting error via Serial
  } else {
    accel.setDataRate(ADXL345_DATARATE_100_HZ);
    accel.setRange(ADXL345_RANGE_16_G);
    calibrateADXL345(accel);
  }

  eventQueue = xQueueCreate(20, sizeof(SeismicEvent));
  xTaskCreate(sensorTask, "SensorTask", 8192, NULL, 5, NULL);
  xTaskCreate(networkTask, "NetworkTask", 8192, NULL, 1, NULL);
#ifdef GNSS_ENABLED
  xTaskCreate(gnssTask, "GnssTask", 8192, NULL, 2, NULL);
#endif

  xTaskCreate(resetTask, "ResetTask", 4096, NULL, 1, NULL);

  Serial.println("[SYS] System Running.");
}

void loop() { vTaskDelete(NULL); }
