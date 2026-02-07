/**
 * Project: QuakeGuard - Electro-Domestic Earthquake Alarm System
 * Version: 3.0.0-MASTER
 * Target Hardware: ESP32-C3 SuperMini + ADXL345
 * Author: GiZano
 *
 * Description:
 * Production-ready firmware for seismic event detection.
 * Integrates real-time signal processing (STA/LTA) with cryptographic payload signing.
 *
 * Key Technical Features:
 * - Hardware: I2C bus forced on GPIO 7 (SDA) and 8 (SCL) with dynamic object allocation.
 * - DSP: High-Pass Filter + Noise Gate + Signal Dropout Protection.
 * - Security: NIST256p ECDSA signature generation for data integrity.
 * - Connectivity: JSON over HTTP POST with NTP synchronization.
 */

#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_ADXL345_U.h>
#include <WiFi.h>
#include <ArduinoJson.h>
#include <Preferences.h>
#include <time.h>

// Cryptographic Libraries (MbedTLS)
#include "mbedtls/entropy.h"
#include "mbedtls/ctr_drbg.h"
#include "mbedtls/ecdsa.h"
#include "mbedtls/pk.h"
#include "mbedtls/error.h"

// --------------------------------------------------------------------------
// HARDWARE PIN DEFINITIONS (ESP32-C3 SuperMini)
// --------------------------------------------------------------------------
// Verified pinout for this specific hardware revision.
#define I2C_SDA_PIN 7
#define I2C_SCL_PIN 8

// Global Sensor Pointer
// Initialized to NULL. Instantiated dynamically in setup() to prevent 
// static initialization race conditions with the I2C bus.
Adafruit_ADXL345_Unified *accel = NULL;

// --------------------------------------------------------------------------
// NETWORK & SERVER CONFIGURATION
// --------------------------------------------------------------------------
#ifndef WIFI_SSID
  #define WIFI_SSID "YOUR_WIFI_SSID" // <--- UPDATE THIS
#endif
#ifndef WIFI_PASS
  #define WIFI_PASS "YOUR_WIFI_PASS" // <--- UPDATE THIS
#endif
#ifndef SERVER_HOST
  #define SERVER_HOST "192.168.1.50" // <--- UPDATE YOUR SERVER IP
#endif
#ifndef SERVER_PORT
  #define SERVER_PORT 8000
#endif
#ifndef SERVER_PATH
  #define SERVER_PATH "/measurements/"
#endif
#ifndef SENSOR_ID
  #define SENSOR_ID 101
#endif

// Constant mapping for type safety
const char* WIFI_SSID_CONF     = WIFI_SSID;
const char* WIFI_PASS_CONF     = WIFI_PASS;
const char* SERVER_HOST_CONF   = SERVER_HOST;
const int   SERVER_PORT_CONF   = SERVER_PORT;
const char* SERVER_PATH_CONF   = SERVER_PATH;
const int   SENSOR_ID_CONF     = SENSOR_ID;

// --------------------------------------------------------------------------
// RTOS HANDLES & DATA STRUCTURES
// --------------------------------------------------------------------------
QueueHandle_t eventQueue;

struct SeismicEvent {
    float magnitude;            // Computed STA/LTA Ratio
    unsigned long event_millis; // System timestamp at trigger time
};

// --------------------------------------------------------------------------
// DSP ALGORITHM PARAMETERS
// --------------------------------------------------------------------------
const float ALPHA_LTA     = 0.05f; // Long Term Average smoothing factor
const float ALPHA_STA     = 0.40f; // Short Term Average smoothing factor
const float TRIGGER_RATIO = 1.8f;  // Threshold ratio for alarm triggering
const float NOISE_FLOOR   = 0.04f; // Minimum G-force to consider valid signal (Noise Gate)

// --------------------------------------------------------------------------
// CRYPTOGRAPHY SUBSYSTEM
// --------------------------------------------------------------------------
Preferences preferences;
mbedtls_entropy_context entropy;
mbedtls_ctr_drbg_context ctr_drbg;
mbedtls_pk_context pk_context;

/**
 * @brief Initializes MbedTLS context and manages Device Identity.
 * Generates a new ECDSA (SECP256R1) Key Pair if not present in Non-Volatile Storage.
 */
void initCrypto() {
    mbedtls_entropy_init(&entropy);
    mbedtls_ctr_drbg_init(&ctr_drbg);
    mbedtls_pk_init(&pk_context);

    const char *pers = "quake_guard_signer";
    mbedtls_ctr_drbg_seed(&ctr_drbg, mbedtls_entropy_func, &entropy, (const unsigned char *)pers, strlen(pers));

    preferences.begin("quake-keys", false);

    if (!preferences.isKey("priv_key")) {
        Serial.println("[SEC] Generating New ECDSA Key Pair...");
        
        mbedtls_pk_setup(&pk_context, mbedtls_pk_info_from_type(MBEDTLS_PK_ECKEY));
        mbedtls_ecp_gen_key(MBEDTLS_ECP_DP_SECP256R1, mbedtls_pk_ec(pk_context), mbedtls_ctr_drbg_random, &ctr_drbg);

        unsigned char priv_buf[128];
        int ret = mbedtls_pk_write_key_der(&pk_context, priv_buf, sizeof(priv_buf));
        int key_len = ret;

        preferences.putBytes("priv_key", priv_buf + sizeof(priv_buf) - key_len, key_len);
        Serial.println("[SEC] Keys Generated and Saved to NVS.");
    } else {
        Serial.println("[SEC] Loading Existing Keys from NVS...");
        size_t len = preferences.getBytesLength("priv_key");
        uint8_t buf[len];
        preferences.getBytes("priv_key", buf, len);

        mbedtls_pk_parse_key(&pk_context, buf, len, NULL, 0);
    }

    // Export Public Key for Server Provisioning
    unsigned char pub_buf[128];
    int ret_pub = mbedtls_pk_write_pubkey_der(&pk_context, pub_buf, sizeof(pub_buf));
    int pub_len = ret_pub;

    Serial.print("[SEC] DEVICE PUBLIC KEY (HEX): ");
    for(int i = sizeof(pub_buf) - pub_len; i < sizeof(pub_buf); i++) {
        Serial.printf("%02x", pub_buf[i]);
    }
    Serial.println();
}

/**
 * @brief Signs a payload string using the device's Private Key.
 * @param message Input string to sign.
 * @return Hexadecimal string of the ECDSA signature.
 */
String signMessage(String message) {
    unsigned char hash[32];
    unsigned char sig[MBEDTLS_ECDSA_MAX_LEN];
    size_t sig_len = 0;

    // SHA-256 Hashing
    mbedtls_md_context_t ctx;
    mbedtls_md_init(&ctx);
    mbedtls_md_setup(&ctx, mbedtls_md_info_from_type(MBEDTLS_MD_SHA256), 0);
    mbedtls_md_starts(&ctx);
    mbedtls_md_update(&ctx, (const unsigned char*)message.c_str(), message.length());
    mbedtls_md_finish(&ctx, hash);
    mbedtls_md_free(&ctx);

    // ECDSA Signing
    mbedtls_pk_sign(&pk_context, MBEDTLS_MD_SHA256, hash, 0, sig, &sig_len, mbedtls_ctr_drbg_random, &ctr_drbg);

    // Hex Encoding
    String hexSig = "";
    for(size_t i = 0; i < sig_len; i++) {
        char buf[3];
        sprintf(buf, "%02x", sig[i]);
        hexSig += buf;
    }
    return hexSig;
}

// --------------------------------------------------------------------------
// TASK: SENSOR ACQUISITION & PROCESSING
// --------------------------------------------------------------------------
void sensorTask(void *pvParameters) {
    float lta = 0.0f;
    float sta = 0.0f;
    float prev_raw_mag = 9.81f; // Assumes 1G start
    float filtered_mag = 0.0f;
    sensors_event_t event;
    
    // Block until the sensor object is allocated in setup()
    while (accel == NULL) {
        vTaskDelay(pdMS_TO_TICKS(100));
    }

    Serial.println("[SENSOR] Task Active. Beginning Stabilization Phase...");

    // Initial Stabilization Loop (Populate Filters)
    for(int i=0; i<20; i++) { 
        if(accel->getEvent(&event)) { 
             float mag = sqrt(pow(event.acceleration.x, 2) + pow(event.acceleration.y, 2) + pow(event.acceleration.z, 2));
             lta = mag; 
             sta = mag; 
             prev_raw_mag = mag;
        }
        vTaskDelay(pdMS_TO_TICKS(50)); 
    }
    Serial.println("[SENSOR] Ready for detection.");

    TickType_t xLastWakeTime = xTaskGetTickCount();
    const TickType_t xFrequency = pdMS_TO_TICKS(10); // 100Hz Sampling Rate
    bool inAlarm = false;
    unsigned long alarmStart = 0;

    for(;;) {
        // Enforce strict timing
        vTaskDelayUntil(&xLastWakeTime, xFrequency);
        
        // Retrieve Data (Access via pointer)
        if (!accel->getEvent(&event)) {
            continue; 
        }

        float raw_mag = sqrt(pow(event.acceleration.x, 2) + pow(event.acceleration.y, 2) + pow(event.acceleration.z, 2));

        // --- SIGNAL DROPOUT PROTECTION ---
        // If magnitude drops below 2.0 m/s^2 (~0.2G), it indicates a wiring failure or I2C bus error.
        // We discard this frame to prevent the High Pass Filter from creating a false spike.
        if (raw_mag < 2.0f) {
            continue; 
        }
        
        // Digital High Pass Filter (Removes Gravity component)
        filtered_mag = 0.9f * (filtered_mag + raw_mag - prev_raw_mag);
        prev_raw_mag = raw_mag;
        float abs_signal = abs(filtered_mag);

        // --- NOISE GATE ---
        // Zero out signals below the hardware noise floor to prevent STA/LTA drift.
        if (abs_signal < NOISE_FLOOR) {
            abs_signal = 0.0f;
        }

        // STA/LTA Algorithm Update
        lta = (ALPHA_LTA * abs_signal) + ((1.0f - ALPHA_LTA) * lta);
        sta = (ALPHA_STA * abs_signal) + ((1.0f - ALPHA_STA) * sta);
        
        // Safety floor for LTA to avoid division by zero or extreme ratios
        if (lta < 0.05f) lta = 0.05f; 
        
        float ratio = sta / lta;

        // TRIGGER LOGIC
        // Condition 1: Ratio exceeds threshold.
        // Condition 2: Actual signal intensity exceeds noise floor (Real event verification).
        if (ratio >= TRIGGER_RATIO && sta > NOISE_FLOOR && !inAlarm) {
            Serial.printf("[SENSOR] EARTHQUAKE DETECTED! Ratio: %.2f (Mag: %.3f G)\n", ratio, sta);
            
            SeismicEvent evt; 
            evt.magnitude = ratio; 
            evt.event_millis = millis();
            xQueueSend(eventQueue, &evt, 0);
            
            inAlarm = true; 
            alarmStart = millis();
        }

        // Alarm Cooldown (5 Seconds)
        if (inAlarm && (millis() - alarmStart > 5000)) {
            inAlarm = false;
        }
    }
}

// --------------------------------------------------------------------------
// TASK: NETWORK DISPATCHER
// --------------------------------------------------------------------------
void networkTask(void *pvParameters) {
    WiFiClient client;
    
    Serial.printf("[NET] Connecting to Access Point: %s\n", WIFI_SSID_CONF);
    WiFi.begin(WIFI_SSID_CONF, WIFI_PASS_CONF);
    
    while (WiFi.status() != WL_CONNECTED) {
        vTaskDelay(pdMS_TO_TICKS(500));
        Serial.print(".");
    }
    Serial.println("\n[NET] WiFi Connected.");

    // NTP Time Synchronization (Critical for signature validity)
    configTime(0, 0, "pool.ntp.org", "time.nist.gov");

    SeismicEvent receivedEvt;
    for(;;) {
        // Block until event is received from Sensor Task
        if (xQueueReceive(eventQueue, &receivedEvt, portMAX_DELAY) == pdTRUE) {
            
            // Connection Watchdog
            if (WiFi.status() != WL_CONNECTED) { 
                WiFi.disconnect(); 
                WiFi.reconnect(); 
                vTaskDelay(pdMS_TO_TICKS(1000));
                continue; 
            }
            
            // Timestamp Reconstruction
            time_t now_unix; 
            time(&now_unix);
            unsigned long age_ms = millis() - receivedEvt.event_millis;
            time_t evt_time = now_unix - (age_ms / 1000);
            
            // Payload Construction
            int val = (int)(receivedEvt.magnitude * 100);
            String payload = String(val) + ":" + String(evt_time);
            
            // Cryptographic Signing
            String sig = signMessage(payload);

            // JSON Serialization
            JsonDocument doc;
            doc["value"] = val; 
            doc["misurator_id"] = SENSOR_ID_CONF;
            doc["device_timestamp"] = evt_time; 
            doc["signature_hex"] = sig;
            String json; 
            serializeJson(doc, json);

            // HTTP POST Transmission
            Serial.println("[NET] Transmitting Event to Server...");
            if (client.connect(SERVER_HOST_CONF, SERVER_PORT_CONF)) {
                client.println(String("POST ") + SERVER_PATH_CONF + " HTTP/1.1");
                client.println(String("Host: ") + SERVER_HOST_CONF);
                client.println("Content-Type: application/json");
                client.print("Content-Length: "); client.println(json.length());
                client.println("Connection: close"); 
                client.println();
                client.println(json);
                
                // Flush Response Buffer
                while(client.connected() || client.available()) { 
                    if(client.available()) client.readStringUntil('\n'); 
                }
                client.stop();
                Serial.println("[NET] Transmission Successful.");
            } else {
                Serial.println("[NET] Connection Failed.");
            }
        }
    }
}

// --------------------------------------------------------------------------
// SYSTEM INITIALIZATION
// --------------------------------------------------------------------------
void setup() {
    Serial.begin(115200);
    // Wait for the Serial Monitor to initialize
    while(!Serial) delay(10); 
    delay(2000); 

    Serial.println("\n\n==================================================");
    Serial.println("[BOOT] QuakeGuard Security System First...");
    Serial.println("==================================================");

    // 1. INITIALIZE CRYPTO SUBSYSTEM & DISPLAY KEY (PRIORITY OVER SENSOR)
    initCrypto();

    Serial.println("\n⚠️  WARNING: You have 10 seconds to copy the Public Key above!");
    Serial.println("    Register it in the server database to prevent 403 Forbidden errors.");
    Serial.println("    Sensor initialization will commence shortly...");
    
    // Visual Countdown
    for(int i=10; i>0; i--) {
        Serial.printf(" %d...", i);
        delay(1000);
    }
    Serial.println("\n\n[BOOT] Starting Hardware Initialization...");

    // 2. HARDWARE INIT (I2C PINS 7 & 8)
    Serial.printf("[HARDWARE] Configuring I2C Bus on SDA=%d, SCL=%d\n", I2C_SDA_PIN, I2C_SCL_PIN);
    
    // Bus Recovery Sequence: Manually toggles pins to unlatch the sensor 
    // if it is stuck in a "zombie" state holding the line low.
    pinMode(I2C_SDA_PIN, INPUT_PULLUP);
    pinMode(I2C_SCL_PIN, INPUT_PULLUP);
    digitalWrite(I2C_SDA_PIN, HIGH);
    digitalWrite(I2C_SCL_PIN, HIGH);
    delay(50);
    
    Wire.end(); 
    Wire.setPins(I2C_SDA_PIN, I2C_SCL_PIN);
    Wire.begin();
    Wire.setClock(10000); // 10kHz stability clock
    delay(100); 

    // 3. DYNAMIC MEMORY ALLOCATION
    Serial.println("[HARDWARE] Allocating Sensor Object...");
    if (accel != NULL) delete accel;
    accel = new Adafruit_ADXL345_Unified(12345);

    // 4. SENSOR STARTUP
    if(!accel->begin(0x53)) {
        Serial.println("[WARN] Not found at 0x53. Trying 0x1D...");
        if(!accel->begin(0x1D)) {
            Serial.println("[FATAL] Sensor Check Failed. (Did you copy the key?)");
            // We do not block execution in an infinite loop here, otherwise the Key 
            // would scroll off-screen. The sensorTask will handle hardware absence gracefully.
        }
    } else {
        accel->setDataRate(ADXL345_DATARATE_100_HZ);
        accel->setRange(ADXL345_RANGE_16_G);
        Serial.println("[SYS] Sensor OK.");
    }

    // 5. TASK CREATION
    eventQueue = xQueueCreate(20, sizeof(SeismicEvent));
    xTaskCreate(sensorTask, "SensorTask", 4096, NULL, 5, NULL);
    xTaskCreate(networkTask, "NetworkTask", 8192, NULL, 1, NULL);

    Serial.println("[SYS] System Running.");
}

void loop() {
    // Main loop delegates to FreeRTOS tasks
    vTaskDelay(pdMS_TO_TICKS(1000));
}