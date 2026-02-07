# QuakeGuard - Electro-Domestic Earthquake Alarm System
### Firmware Version: 3.0.0-MASTER

## 1. Project Overview
QuakeGuard is an IoT-based seismic detection node designed for the **ESP32-C3 SuperMini** platform. It utilizes an **ADXL345** accelerometer to detect ground vibrations in real-time using the **STA/LTA (Short Term Average / Long Term Average)** algorithm.

Upon detecting a seismic event, the device constructs a JSON payload containing the magnitude and timestamp, cryptographically signs it using **ECDSA (NIST256p)**, and transmits it via HTTP POST to a central server.

## 2. Hardware Architecture

### Target Platform
* **Microcontroller:** ESP32-C3 SuperMini (RISC-V)
* **Sensor:** ADXL345 Digital Accelerometer (I2C Interface)

### Pin Configuration (Critical)
Due to the specific layout of the ESP32-C3 SuperMini, the I2C bus is forced via software to the following GPIOs:

| Component Pin | ESP32-C3 GPIO | Notes |
| :--- | :--- | :--- |
| **SDA** | **GPIO 7** | Requires internal Pull-Up (Handled by Firmware) |
| **SCL** | **GPIO 8** | Requires internal Pull-Up (Handled by Firmware) |
| **VCC** | **3.3V** | **Do not use 5V** (Risk of sensor damage) |
| **GND** | **GND** | Common Ground |

## 3. Key Features

### Signal Processing (DSP)
* **Dynamic Allocation:** Sensor objects are instantiated dynamically after boot to prevent I2C bus race conditions.
* **Digital High-Pass Filter (HPF):** Removes the DC component (gravity) to isolate vibration data.
* **Noise Gate:** Ignores micro-vibrations below **0.04G** to prevent false positives from electrical noise.
* **Dropout Protection:** Automatically discards invalid frames (0G readings) caused by temporary wiring disconnects.

### Security Subsystem
* **Identity:** Unique Device Identity based on a persistent **ECDSA Private Key** stored in NVS (Non-Volatile Storage).
* **Integrity:** Every payload is hashed (SHA-256) and signed. The server can verify the origin using the device's Public Key.
* **Replay Protection:** Timestamps are synchronized via NTP (`pool.ntp.org`) to prevent replay attacks.

## 4. Configuration

Before compiling, ensure the network and server credentials in `src/main.cpp` are updated:

```cpp
#ifndef WIFI_SSID
  #define WIFI_SSID "YOUR_WIFI_NAME"
#endif

#ifndef SERVER_HOST
  #define SERVER_HOST "192.168.1.X" // Your Backend IP
#endif
```

## 5. Installation & Provisioning

### Step 1: Upload Firmware
Connect the ESP32-C3 via USB and upload the firmware using PlatformIO or Arduino IDE.

### Step 2: Key Extraction (Crucial)
On the **first boot**, the device will generate a new cryptographic key pair. You must capture the **Public Key** from the Serial Monitor to register the device on the server.

1.  Open the Serial Monitor (Baud Rate: **115200**).
2.  Reset the board.
3.  Look for the security header:

```text
[BOOT] QuakeGuard Security System First...
[SEC] Generating New ECDSA Key Pair...
[SEC] Keys Generated and Saved to NVS.
[SEC] DEVICE PUBLIC KEY (HEX): 04a3b2c1... <COPY THIS STRING>
```

4.  **Copy the HEX string.** You have a 10-second window before the sensor initialization begins.
5.  Register this key in your backend database associated with `SENSOR_ID 101`.

**Note:** If the server does not have this key, it will reject data with `403 Forbidden`.

## 6. LED / Serial Status Codes

* `[SYS] Sensor OK`: Hardware initialization successful.
* `[SENSOR] Stabilizing...`: Calibrating the accelerometer baseline (do not move the device).
* `[SENSOR] EARTHQUAKE DETECTED!`: The STA/LTA ratio exceeded **1.8** and intensity exceeded **0.04G**.
* `[NET] Transmission Successful`: JSON payload accepted by the server.

## 7. Troubleshooting

### "Sensor Hardware Failure" / "Fatal Error"
If the serial monitor displays `[FATAL] Sensor Check Failed`:
1.  **Cold Boot:** Unplug the USB cable completely for 5 seconds (the ADXL345 must lose power to reset). Reconnect and retry.
2.  **Check Wiring:** Ensure SDA is on Pin 7 and SCL is on Pin 8.
3.  **Voltage:** Verify the sensor is receiving 3.3V.

### "403 Forbidden" from Server
The device is connected to WiFi but the server rejected the signature.
* **Solution:** Re-connect to Serial Monitor, reset the board, copy the **Public Key**, and update the server's authorized devices list.

## 8. License
Copyright (c) 2026 GiZano. All rights reserved.
intended for educational and research purposes.