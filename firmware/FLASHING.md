# 🔧 QuakeGuard — Firmware Flashing Guide

> Step-by-step instructions for flashing the QuakeGuard firmware onto an ESP32-C3 SuperMini, without requiring VS Code or PlatformIO IDE.

## Prerequisites

- **Python 3.8+** installed on your system
- **PlatformIO Core (CLI):** Install via `pip install platformio`
- **USB-C cable** (data-capable, not charge-only)
- **QuakeGuard PCB** assembled, or ESP32-C3 SuperMini with ADXL345 wired on breadboard (see [PINOUT.md](PINOUT.md))

## 1. Configure Environment Variables

```bash
cd firmware
cp esp32_config.env.example esp32_config.env
```

Edit `esp32_config.env` with your specific values:
- **WiFi credentials** (`WIFI_SSID`, `WIFI_PASS`)
- **Backend address** (`SERVER_HOST`, `SERVER_PORT`)
- **MQTT broker** (`MQTT_BROKER_HOST`, credentials)
- **Enrollment token** (`ENROLLMENT_TOKEN`) — must match the backend `.env`

> ⚠️ The build will fail with `#error` if `ENROLLMENT_TOKEN`, `MQTT_BROKER_HOST`, `MQTT_USERNAME`, or `MQTT_PASSWORD` are missing. This is intentional fail-fast behavior.

## 2. Connect the ESP32-C3

1. Connect the ESP32-C3 SuperMini via USB-C to your computer
2. Identify the serial port:
   - **Linux:** `/dev/ttyACM0` (default)
   - **macOS:** `/dev/cu.usbmodem*`
   - **Windows:** `COM3` or similar (check Device Manager)

3. If needed, update the port in `platformio.ini`:
   ```ini
   upload_port = /dev/ttyACM0
   monitor_port = /dev/ttyACM0
   ```

## 3. Build and Flash

```bash
cd firmware

# Build only (compile without flashing)
pio run

# Build and flash to the connected device
pio run --target upload

# Open serial monitor after flashing
pio device monitor
```

### SuperMini Boot Mode

The ESP32-C3 SuperMini may require manual boot mode entry for the first flash:

1. Hold the **BOOT** button
2. Press and release the **RESET** button
3. Release the **BOOT** button
4. Run `pio run --target upload`

Subsequent flashes should work without manual intervention (the `--before=no_reset --after=hard_reset` flags in `platformio.ini` handle this).

## 4. First Boot Sequence

On first power-up after a successful flash, the device will:

1. 🔵🔴 **LED boot test:** Both LEDs blink 2x to verify wiring
2. 📡 **WiFi captive portal:** Opens `QuakeGuard-Setup` AP (180s timeout)
3. 🌐 **Connect to WiFi** and auto-provision with the backend
4. 🔑 **Generate ECDSA key pair** (stored in NVS, never leaves the device)
5. 📋 **Register with backend** via `POST /devices/register`
6. 🔵 **Solid blue LED** = fully connected and transmitting

### Serial Monitor Output (Successful Boot)

```
[BOOT] QuakeGuard v2.1.1
[SEC] Generating New ECDSA Key Pair...
[SEC] Keys Generated.
[BOOT] Device UNREGISTERED. Entering Provisioning Mode...
[NET] WiFi Connected.
[PROV] Starting Device Handshake...
[PROV] SUCCESS! Assigned Sensor ID: 1
[SENSOR] Task Active. Stabilizing and filling buffers...
[SYS] System Running.
```

## 5. Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Build fails with `#error ENROLLMENT_TOKEN` | Missing env variable | Check `esp32_config.env` |
| `Upload failed: No serial port` | Wrong port or cable | Try different USB-C cable (data-capable) |
| 🔴 Solid red LED after boot | ADXL345 not detected | Check J3 wiring: SDA→GPIO7, SCL→GPIO8, VCC→3.3V |
| 🔵 Double blink | WiFi not connecting | Reconnect via `QuakeGuard-Setup` captive portal |
| `[PROV] Registration Failed. HTTP Code: -1` | Backend unreachable | Verify `SERVER_HOST` is correct and backend is running |
| `errno 118` / connection refused | DNS/subnet issue | Use local IP (e.g. `192.168.1.x`), not hostname |

## Optional: GNSS Module

To enable the optional GNSS module (NEO-6M), uncomment in `esp32_config.env`:

```env
GNSS_ENABLED=1
GPS_SERIAL_RX_PIN=5
GPS_SERIAL_TX_PIN=4
GPS_SERIAL_BAUD=9600
```

See [PINOUT.md](PINOUT.md) for connector wiring (J4).
