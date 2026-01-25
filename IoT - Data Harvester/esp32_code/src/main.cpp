/**
 * ESP32-C3 ADXL345 Seismic Detector (STA/LTA Algorithm)
 * * This firmware implements a Short Term Average / Long Term Average (STA/LTA) 
 * trigger algorithm to detect sudden vibration changes (simulating P-wave detection).
 * * Hardware:
 * - MCU: ESP32-C3
 * - Sensor: ADXL345 (I2C)
 */

#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_ADXL345_U.h>

// --- Hardware Configuration ---
// Unique ID for the sensor instance
Adafruit_ADXL345_Unified accel = Adafruit_ADXL345_Unified(12345);

// I2C Pins for ESP32-C3 SuperMini/DevKit
#define SDA_PIN 8
#define SCL_PIN 9

// --- STA/LTA Algorithm Configuration ---
// STA (Short Term Average): Represents the instantaneous seismic event.
// LTA (Long Term Average): Represents the background noise level.

float lta = 0.0f; 
float sta = 0.0f; 

// Smoothing factors (Alpha) for the Exponential Moving Average (EMA).
// Range: 0.0 to 1.0. 
// Lower value = Slower decay (Longer memory). 
// Higher value = Faster decay (Higher reactivity).
const float alpha_lta = 0.05f; // Slow update for background noise
const float alpha_sta = 0.40f; // Fast update for current events

// Trigger Threshold
// If STA / LTA > trigger_ratio, an event is declared.
const float trigger_ratio = 1.8f; 

// System State
bool alarmActive = false;
unsigned long alarmStartTime = 0;
const unsigned long ALARM_DURATION_MS = 2000;

void setup() {
  Serial.begin(115200);
  // Allow time for serial monitor connection and sensor power-up
  delay(3000); 

  // Initialize I2C interface
  Wire.begin(SDA_PIN, SCL_PIN);

  // Initialize Sensor
  if(!accel.begin()) {
    Serial.println("[ERROR] No ADXL345 detected. Check wiring.");
    while(1); // Halt execution
  }

  // Sensor Configuration
  // 100Hz data rate is sufficient for basic seismic detection
  accel.setDataRate(ADXL345_DATARATE_100_HZ);
  accel.setRange(ADXL345_RANGE_16_G); // Wide range to prevent clipping during shocks
  
  Serial.println("[SYSTEM] Seismic Detector Started");
  Serial.println("[SYSTEM] Calibrating baseline noise level...");

  // Fill initial buffer to stabilize LTA/STA before main loop
  sensors_event_t event; 
  for(int i = 0; i < 50; i++) {
    accel.getEvent(&event);
    
    // Calculate 3D Magnitude vector
    float mag = sqrt(event.acceleration.x * event.acceleration.x + 
                     event.acceleration.y * event.acceleration.y + 
                     event.acceleration.z * event.acceleration.z);
    lta = mag;
    sta = mag;
    delay(10);
  }
  
  Serial.println("[SYSTEM] Calibration Complete. Listening...");
}

void loop() {
  sensors_event_t event; 
  accel.getEvent(&event);

  // 1. Magnitude Calculation
  // Calculate the Euclidean norm of the acceleration vector
  float raw_mag = sqrt(pow(event.acceleration.x, 2) + 
                       pow(event.acceleration.y, 2) + 
                       pow(event.acceleration.z, 2));
  
  // 2. Gravity Compensation
  // Subtract approximate Earth gravity (9.81 m/s^2) to isolate dynamic vibration.
  // Note: For higher precision, a High-Pass Filter (HPF) is recommended over simple subtraction.
  float pure_vibration = abs(raw_mag - 9.81); 

  // 3. Update STA/LTA (Exponential Moving Average)
  // LTA tracks background noise slowly
  lta = (alpha_lta * pure_vibration) + ((1.0 - alpha_lta) * lta);
  
  // STA tracks current events quickly
  sta = (alpha_sta * pure_vibration) + ((1.0 - alpha_sta) * sta);

  // Prevent division by zero or extremely low noise floors
  if (lta < 0.05) lta = 0.05; 

  // 4. Calculate Ratio
  float ratio = sta / lta;

  // 5. Trigger Logic
  if (ratio >= trigger_ratio && !alarmActive) {
    Serial.println("\n--- DETECTED EVENT ---");
    Serial.println("[ALERT] P-Wave / Sudden Impulse Detected");
    Serial.print("Intensity Ratio: "); 
    Serial.println(ratio);
    Serial.println("Warning: Possible secondary wave approaching");
    Serial.println("----------------------");
    
    alarmActive = true;
    alarmStartTime = millis();
  }

  // 6. Reset Logic
  // Reset alarm state after the defined duration
  if (alarmActive && (millis() - alarmStartTime > ALARM_DURATION_MS)) {
     alarmActive = false;
     Serial.println("[INFO] Event ended. System re-armed.");
  }

  // Sampling delay
  // 20ms delay roughly equals a 50Hz polling rate (plus processing time)
  delay(20); 
}