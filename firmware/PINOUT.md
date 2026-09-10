# 🔌 QuakeGuard — Firmware Pinout Reference

> **PCB Revision:** v2.0.0 (JLCPCB)
> **MCU:** ESP32-C3 SuperMini

## GPIO Mapping

| GPIO | Function | Component | PCB Connector | Notes |
|------|----------|-----------|---------------|-------|
| 7 | I2C SDA | ADXL345 | J3-3 (SDA) | 100 kHz clock, internal pull-up |
| 8 | I2C SCL | ADXL345 | J3-4 (SCL) | 100 kHz clock, internal pull-up |
| 10 | LED Blue (PWM) | Status LED | D2 (Blue) | Connection state indicator, via R2 (330Ω) |
| 3 | LED Red (Digital) | Alert LED | D3 (Red) | Earthquake detected indicator, via R3 (330Ω) |
| 5 | UART1 RX | NEO-6M GNSS TX | J4-3 (GNSS TX) | Optional: compile with `GNSS_ENABLED=1` |
| 4 | UART1 TX | NEO-6M GNSS RX | J4-4 (GNSS RX) | Optional: compile with `GNSS_ENABLED=1` |
| 2 | PPS Interrupt | NEO-6M PPS | J4-5 (PPS) | Optional: 1PPS discipline for ms-accuracy |
| USB | CDC Serial | Host Bridge | USB-C | Telemetry fallback + debug monitor |

## I2C Bus

| Address | Device | Purpose |
|---------|--------|---------|
| `0x53` | ADXL345 | Primary accelerometer address |
| `0x1D` | ADXL345 | Alternate address (ALT pin HIGH) |

## LED Behavior

| Pattern | Meaning |
|---------|---------|
| 🔵 Double blink (100ms on/off) | WiFi disconnected |
| 🔵 Single blink (200ms on/off) | WiFi OK, MQTT disconnected |
| 🔵 Solid (PWM ~40%) | Fully connected |
| 🔴 Solid | Sensor hardware fault (ADXL345 init failed) |
| 🔴 3-second pulse | Earthquake event detected |
| 🔵🔴 2x alternating blink | Boot self-test (wiring verification) |
| 🔴 Rapid 3x blink | ADXL345 I2C retry (during init) |

## Power

| Pin | Source | Notes |
|-----|--------|-------|
| 3V3 | ESP32-C3 LDO | Powers ADXL345 (J3-1) and GNSS (J4-1) |
| GND | Common ground | Shared across all connectors |
| 5V (USB) | USB-C input | Powers the ESP32-C3 SuperMini |

## PCB Connector Pinout

### J1 — ESP32-C3 Left Header (8-pin)
Directly soldered to the ESP32-C3 SuperMini left row.

### J2 — ESP32-C3 Right Header (8-pin)
Directly soldered to the ESP32-C3 SuperMini right row.

### J3 — ADXL345 Accelerometer (8-pin)
| Pin | Signal | Connected To |
|-----|--------|-------------|
| 1 | VCC (3.3V) | ESP32 3V3 |
| 2 | GND | Common GND |
| 3 | SDA | GPIO 7 |
| 4 | SCL | GPIO 8 |
| 5-8 | NC | Not connected |

### J4 — GNSS Module NEO-6M (5-pin)
| Pin | Signal | Connected To |
|-----|--------|-------------|
| 1 | VCC (3.3V) | ESP32 3V3 |
| 2 | GND | Common GND |
| 3 | TX (GNSS → ESP) | GPIO 5 (UART1 RX) |
| 4 | RX (ESP → GNSS) | GPIO 4 (UART1 TX) |
| 5 | PPS | GPIO 2 |

## Passive Components

| Ref | Value | Purpose |
|-----|-------|---------|
| R1, R2, R3 | 330Ω | Current limiting for LEDs D1, D2, D3 |
| C1, C3 | 10µF | Decoupling capacitors (power supply) |
| C2 | 0.1µF | High-frequency bypass capacitor |
| D1 | Green LED | Reserved (future use) |
| D2 | Blue LED | Connection status indicator |
| D3 | Red LED | Earthquake alert indicator |
