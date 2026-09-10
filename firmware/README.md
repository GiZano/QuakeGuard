# QuakeGuard - Distributed Earthquake Early Warning System
### Firmware Version: v2.1.0

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

### USB Serial Fallback 
When the MQTT data plane is unreachable, the node re-certifies each event and emits it over the **USB CDC** port as a machine-readable frame so a co-located host still receives data during offline simulations:

```
[QG:FB]{"value":250,"sensor_id":42,"device_timestamp":1720000000,"signature_hex":"..."}
```

* **Identical signing** to the MQTT data plane — the backend ECDSA + replay-window checks apply unchanged.
* **USB-host aware:** frames are only written while a real USB host is attached (`Serial.isConnected()`, HWCDC). Plugged into a power-only charger, events are **retained in an in-memory ring** (last 100) instead of being sent to a dead port, and are drained FIFO when a path returns.
* **Offline wall clock:** timestamps come from a software clock anchored at the first NTP sync, so they stay valid after WiFi drops; retained events are re-signed with the current time at drain.
* **Host bridge:** `tools/serial_bridge.py` reads the CDC device and forwards each frame to the ingestion pipeline:
  ```bash
  pip install pyserial requests
  python tools/serial_bridge.py --port /dev/ttyACM0 --api-key "$IOT_API_KEY"
  ```
* **Toggle:** set `SERIAL_FALLBACK_ENABLED=0` in `esp32_config.env` for MQTT-only behaviour.

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

### HTTPS Tunnel Compatibility (IoT TLS clients)
The device registers over plain HTTPS using the ESP-IDF **mbedTLS** stack. The ngrok **free-tier** edge terminates TLS handshakes from such clients via **JA3 fingerprinting** (bot-protection) *before* any HTTP header — including `ngrok-skip-browser-warning` — can be read, so the request never reaches the backend (`HTTP Code: -1`, `SSL - The connection indicated an EOF`). For the dev tunnel we use a **Cloudflare quick tunnel** (`cloudflared tunnel --url http://localhost:8000`), whose edge does not fingerprint IoT TLS clients, or a real HTTPS domain in production. Set `SERVER_HOST` (no scheme) and `SERVER_PROTOCOL` accordingly.

> **Dev tunnel lifecycle (ephemeral).** The quick tunnel is account-less and has no uptime guarantee: it dies with the `cloudflared` process and the URL changes at **every restart**. The node only calls the HTTP endpoint at **first boot** (provisioning); after that it publishes over MQTT. If you erase the node's NVS (re-provisioning) or build fresh, restart the tunnel and update `SERVER_HOST` (firmware) and `EXPO_PUBLIC_API_BASE_URL` (mobile) with the new URL:
> ```bash
> ~/bin/cloudflared tunnel --url http://localhost:8000 --no-autoupdate --protocol http2
> ```
> `--protocol http2` is required on networks that block the default QUIC edge connection. For a stable URL, use a named Cloudflare tunnel with your own domain.

### Enabling the Optional GNSS Module (Experimental)
The firmware ships with a **GNSS heartbeats module**, disabled by default. When enabled, the device reads a connected UART GNSS receiver, computes a geohash from the current fix, and includes it in every heartbeat sent to the server (used by the geo-spatial zone-alerting feature on the backend).

* **Makefile/environment flag:** set `GNSS_ENABLED=1` in the `esp32_config.env` file (see `esp32_config.env.example`) and rebuild. Without the flag (or without the file), the module compiles out entirely — zero RAM/flash overhead.
* **Hardware wiring (UART):** connect the GNSS receiver TX to a free UART-capable pin and set `GNSS_UART_TX_PIN` / `GNSS_UART_RX_PIN` in `src/gnss/GnssModule.h`.
* **Behavior while unlocked:** the module stays **UART-silent** (no `$GxRMC`/`$GxGGA` requests) so legacy GeoGuessr-style debugging on the same UART line is preserved.
* **Fallback:** if the receiver never produces a fix, the heartbeat is sent without location and the server falls back to the device's registered location.

## 5. Installation & Provisioning

### Step 1: Upload Firmware
Connect the ESP32-C3 via USB and upload the firmware using PlatformIO or Arduino IDE.

### Step 2: Automatic Registration (no manual step)
On the **first boot** the device performs the automated handshake:

1. Generates a fresh **ECDSA key pair** and seals the private key in NVS.
2. Opens the WiFi captive portal (`QuakeGuard-Setup`) so you can connect it to your network.
3. POSTs `/devices/register` with its `public_key_hex`, `mac_address`, `enrollment_token` and (GNSS-ready) coordinates.
4. Receives its `sensor_id` back from the backend and persists it in NVS.

No per-device configuration is needed for distribution — the backend assigns the ID
and the zone (via PostGIS) at registration time. The serial output shows:

```text
[PROV] SUCCESS! Assigned Sensor ID: 7
[PROV] Public key: 3059301306072a8648ce3d0201...
```

## 6. LED / Serial Status Codes

* `[SYS] Sensor OK`: Hardware initialization successful.
* `[SENSOR] Stabilizing...`: Calibrating the accelerometer baseline (do not move the device).
* `[SENSOR] EARTHQUAKE DETECTED!`: The STA/LTA ratio exceeded **1.8** and intensity exceeded **0.04G**.
* `[NET] Transmission Successful`: JSON payload accepted by the server.
* `[NET] MQTT Publish OK.` / `[NET] Serial Fallback Publish OK.`: event dispatched over the active path.
* `[NET] No delivery path: event retained in ring.`: MQTT down and no USB host — the event is buffered for later drain.

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