/**
 * Project: QuakeFinder - Distributed Seismic Detection System
 * Firmware Version: 2.2.0-STABLE
 * Target Hardware: ESP32-C3 + ADXL345
 * Author: GiZano
 * * Description:
 * This firmware implements a resilient IoT seismic node using FreeRTOS.
 * Key Features:
 * - Dual-core Multitasking: Decoupled Data Acquisition (Real-Time) and Network Dispatch.
 * - Timestamp Reconstruction: Events are time-tagged relative to boot, then converted 
 * to Unix Epoch upon transmission to prevent blocking sensor data during connectivity loss.
 * - Digital Signal Processing: 100Hz Sampling, High-Pass Filter, STA/LTA Trigger.
 * - Security: ECDSA (NIST256p) Payload Signing using hardware-accelerated MbedTLS.
 */

#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_ADXL345_U.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <ArduinoJson.h>
#include <Preferences.h> 
#include <time.h>

// MbedTLS headers for cryptographic operations
#include "mbedtls/entropy.h"
#include "mbedtls/ctr_drbg.h"
#include "mbedtls/ecdsa.h"
#include "mbedtls/pk.h"
#include "mbedtls/error.h"

// --------------------------------------------------------------------------
// USER CONFIGURATION
// --------------------------------------------------------------------------
const char* WIFI_SSID     = "YOUR_WIFI_SSID";
const char* WIFI_PASS     = "YOUR_WIFI_PASSWORD";
const char* SERVER_HOST   = "api.quakefinder.io"; 
const int   SERVER_PORT   = 443;
const char* SERVER_PATH   = "/misurations/";
const int   SENSOR_ID     = 101; 

// --------------------------------------------------------------------------
// HARDWARE CONFIGURATION
// --------------------------------------------------------------------------
#define SDA_PIN 8
#define SCL_PIN 9
Adafruit_ADXL345_Unified accel = Adafruit_ADXL345_Unified(12345);

// --------------------------------------------------------------------------
// ALGORITHM CONSTANTS (STA/LTA)
// --------------------------------------------------------------------------
const float ALPHA_LTA     = 0.05f; 
const float ALPHA_STA     = 0.40f; 
const float TRIGGER_RATIO = 1.8f;  

// --------------------------------------------------------------------------
// GLOBAL HANDLES & STRUCTURES
// --------------------------------------------------------------------------
QueueHandle_t eventQueue; 

// Data structure representing a detected seismic event
struct SeismicEvent {
    float magnitude;            // Normalized intensity ratio
    unsigned long event_millis; // System uptime (ms) when event occurred
};

// --------------------------------------------------------------------------
// CRYPTOGRAPHY CONTEXTS
// --------------------------------------------------------------------------
Preferences preferences;
mbedtls_entropy_context entropy;
mbedtls_ctr_drbg_context ctr_drbg;
mbedtls_pk_context pk_context;

/**
 * @brief Initializes the cryptographic engine and manages Identity Keys.
 * Checks NVS for an existing Private Key. If missing, generates a new SECP256R1 pair.
 */
void initCrypto() {
    mbedtls_entropy_init(&entropy);
    mbedtls_ctr_drbg_init(&ctr_drbg);
    mbedtls_pk_init(&pk_context);
    
    const char *pers = "quake_signer_gizano";
    mbedtls_ctr_drbg_seed(&ctr_drbg, mbedtls_entropy_func, &entropy, (const unsigned char *)pers, strlen(pers));

    preferences.begin("quake-keys", false); 
    
    if (!preferences.isKey("priv_key")) {
        Serial.println("[SEC] Generating new ECDSA Key Pair (NIST256p)...");
        
        mbedtls_pk_setup(&pk_context, mbedtls_pk_info_from_type(MBEDTLS_PK_ECKEY));
        mbedtls_ecp_gen_key(MBEDTLS_ECP_DP_SECP256R1, mbedtls_pk_ec(pk_context), mbedtls_ctr_drbg_random, &ctr_drbg);

        unsigned char priv_buf[128];
        // Export to DER. Note: writes at the END of the buffer.
        int ret = mbedtls_pk_write_key_der(&pk_context, priv_buf, sizeof(priv_buf));
        int key_len = ret; 
        
        preferences.putBytes("priv_key", priv_buf + sizeof(priv_buf) - key_len, key_len);
        Serial.println("[SEC] New keys generated and stored in NVS.");
    } else {
        Serial.println("[SEC] Loading existing keys from NVS...");
        size_t len = preferences.getBytesLength("priv_key");
        uint8_t buf[len];
        preferences.getBytes("priv_key", buf, len);
        
        mbedtls_pk_parse_key(&pk_context, buf, len, NULL, 0);
    }
    
    // Print Public Key for Server Registration
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
 * @brief Signs a string message using ECDSA.
 * Compatible with ESP32 Arduino Core 2.x (MbedTLS v2).
 */
String signMessage(String message) {
    unsigned char hash[32];
    unsigned char sig[MBEDTLS_ECDSA_MAX_LEN];
    size_t sig_len = 0;

    // 1. SHA256 Hash
    mbedtls_md_context_t ctx;
    mbedtls_md_init(&ctx);
    mbedtls_md_setup(&ctx, mbedtls_md_info_from_type(MBEDTLS_MD_SHA256), 0);
    mbedtls_md_starts(&ctx);
    mbedtls_md_update(&ctx, (const unsigned char*)message.c_str(), message.length());
    mbedtls_md_finish(&ctx, hash);
    mbedtls_md_free(&ctx);

    // 2. ECDSA Signature
    // FIX APPLIED: Removed 'sizeof(sig)' argument for MbedTLS v2 compatibility
    mbedtls_pk_sign(&pk_context, MBEDTLS_MD_SHA256, hash, 0, sig, &sig_len, mbedtls_ctr_drbg_random, &ctr_drbg);

    // 3. Hex Conversion
    String hexSig = "";
    for(size_t i = 0; i < sig_len; i++) {
        char buf[3];
        sprintf(buf, "%02x", sig[i]);
        hexSig += buf;
    }
    return hexSig;
}

// --------------------------------------------------------------------------
// TASK 1: DATA ACQUISITION & PROCESSING (Real-Time Priority)
// --------------------------------------------------------------------------
void sensorTask(void *pvParameters) {
    float lta = 0.0f;
    float sta = 0.0f;
    float prev_raw_mag = 9.81f; 
    float filtered_mag = 0.0f;
    
    // Fill buffer for algorithm stabilization
    sensors_event_t event;
    for(int i=0; i<20; i++) {
        accel.getEvent(&event);
        float mag = sqrt(pow(event.acceleration.x, 2) + pow(event.acceleration.y, 2) + pow(event.acceleration.z, 2));
        lta = mag; sta = mag;
        vTaskDelay(pdMS_TO_TICKS(10));
    }

    TickType_t xLastWakeTime;
    const TickType_t xFrequency = pdMS_TO_TICKS(10); // 100Hz
    xLastWakeTime = xTaskGetTickCount();

    bool inAlarm = false;
    unsigned long alarmStart = 0;

    for(;;) {
        // High precision delay
        vTaskDelayUntil(&xLastWakeTime, xFrequency);

        accel.getEvent(&event);
        float raw_mag = sqrt(pow(event.acceleration.x, 2) + pow(event.acceleration.y, 2) + pow(event.acceleration.z, 2));

        // High Pass Filter (Gravity Removal)
        const float alpha_hpf = 0.9f; 
        filtered_mag = alpha_hpf * (filtered_mag + raw_mag - prev_raw_mag);
        prev_raw_mag = raw_mag;
        float abs_signal = abs(filtered_mag);

        // STA/LTA Algorithm
        lta = (ALPHA_LTA * abs_signal) + ((1.0f - ALPHA_LTA) * lta);
        sta = (ALPHA_STA * abs_signal) + ((1.0f - ALPHA_STA) * sta);
        if (lta < 0.01f) lta = 0.01f;

        float ratio = sta / lta;

        if (ratio >= TRIGGER_RATIO && !inAlarm) {
            Serial.printf("[SENSOR] Event detected! Ratio: %.2f\n", ratio);
            
            SeismicEvent evt;
            evt.magnitude = ratio;
            // CRITICAL: Save uptime (millis), not absolute time.
            // This prevents blocking if NTP is not yet ready.
            evt.event_millis = millis(); 

            xQueueSend(eventQueue, &evt, 0);

            inAlarm = true;
            alarmStart = millis();
        }

        if (inAlarm && (millis() - alarmStart > 2000)) {
            inAlarm = false;
        }
    }
}

// --------------------------------------------------------------------------
// TASK 2: NETWORK CONNECTIVITY & DISPATCH (Lower Priority)
// --------------------------------------------------------------------------
void networkTask(void *pvParameters) {
    WiFiClientSecure client;
    client.setInsecure(); // Prod: Use setCACert()

    // 1. Connect WiFi
    WiFi.begin(WIFI_SSID, WIFI_PASS);
    while (WiFi.status() != WL_CONNECTED) {
        vTaskDelay(pdMS_TO_TICKS(1000));
        Serial.print(".");
    }
    Serial.println("\n[NET] WiFi Connected");

    // 2. Blocking NTP Sync (Required for valid signatures)
    // We pause processing here until we have a valid time reference.
    configTime(0, 0, "pool.ntp.org", "time.nist.gov");
    Serial.println("[NET] Synchronizing Time...");
    
    while (time(NULL) < 100000) { // Wait until year > 1970
        Serial.print(".");
        vTaskDelay(pdMS_TO_TICKS(500));
    }
    Serial.println("\n[NET] Time Synced!");

    SeismicEvent receivedEvt;

    for(;;) {
        // Wait for event from Queue
        if (xQueueReceive(eventQueue, &receivedEvt, portMAX_DELAY) == pdTRUE) {
            
            if (WiFi.status() != WL_CONNECTED) {
                Serial.println("[NET] Reconnecting...");
                WiFi.disconnect();
                WiFi.reconnect();
                vTaskDelay(pdMS_TO_TICKS(2000));
                continue; 
            }

            // --- TIMESTAMP RECONSTRUCTION ---
            // Calculate exact event time: Now - (How long ago event happened)
            time_t now_unix;
            time(&now_unix);
            
            unsigned long current_millis = millis();
            unsigned long age_ms = current_millis - receivedEvt.event_millis;
            
            // Reconstructed Unix Timestamp
            time_t event_unix_timestamp = now_unix - (age_ms / 1000);

            // Prepare Payload
            int value_to_send = (int)(receivedEvt.magnitude * 100); 
            String payloadData = String(value_to_send) + ":" + String(event_unix_timestamp);
            
            String signature = signMessage(payloadData);

            JsonDocument doc;
            doc["value"] = value_to_send;
            doc["misurator_id"] = SENSOR_ID;
            doc["device_timestamp"] = event_unix_timestamp; // Use reconstructed time
            doc["signature_hex"] = signature;

            String jsonString;
            serializeJson(doc, jsonString);

            // Send HTTPS
            if (client.connect(SERVER_HOST, SERVER_PORT)) {
                client.println(String("POST ") + SERVER_PATH + " HTTP/1.1");
                client.println(String("Host: ") + SERVER_HOST);
                client.println("Content-Type: application/json");
                client.print("Content-Length: ");
                client.println(jsonString.length());
                client.println();
                client.println(jsonString);

                while (client.connected()) {
                    String line = client.readStringUntil('\n');
                    if (line == "\r") break;
                }
                String response = client.readStringUntil('\n');
                Serial.println("[NET] Response: " + response);
                client.stop();
            } else {
                Serial.println("[NET] Transmit Failed");
            }
        }
    }
}

// --------------------------------------------------------------------------
// MAIN ENTRY POINTS
// --------------------------------------------------------------------------

void setup() {
    Serial.begin(115200);
    delay(2000); 

    Wire.begin(SDA_PIN, SCL_PIN);
    if(!accel.begin()) {
        Serial.println("[FATAL] ADXL345 failure");
        while(1);
    }
    accel.setDataRate(ADXL345_DATARATE_100_HZ);
    accel.setRange(ADXL345_RANGE_16_G);

    initCrypto();

    eventQueue = xQueueCreate(20, sizeof(SeismicEvent));

    // High Priority Sensor Task
    xTaskCreate(sensorTask, "SensorTask", 4096, NULL, 5, NULL);
    
    // Low Priority Network Task
    xTaskCreate(networkTask, "NetworkTask", 8192, NULL, 1, NULL);

    Serial.println("[SYS] System Armed.");
}

void loop() {
    vTaskDelay(pdMS_TO_TICKS(1000));
}