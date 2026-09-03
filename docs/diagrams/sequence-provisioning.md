# Sequence Diagram — Device Provisioning (First Boot)

## a. Local Network Setup

<!--
FIX (Figure 6): text was "leggermente piccolo". Bumped
actor/message/note font sizes slightly (32/26/26 -> 34/28/28). Layout was
already fine, so nothing else changed. Render at a higher raster scale
(see notes.md) for extra crispness.
-->
```mermaid
%%{init: {"sequence": {"actorFontSize": 34, "messageFontSize": 28, "noteFontSize": 28, "messageMargin": 40, "boxMargin": 10}}}%%
sequenceDiagram
    participant ESP as ESP32-C3<br/>Node
    participant WM as WiFiManager
    participant User as User<br/>(Phone/Laptop)
    participant API as FastAPI<br/>Gateway

    Note over ESP: Power-on → LED boot test (2x blink)
    ESP->>ESP: Generate ECDSA key pair (if first boot)
    ESP->>ESP: Store private key in NVS

    ESP->>WM: Start captive portal "QuakeGuard-Setup"
    User->>WM: Connect to AP, enter WiFi credentials
    WM->>ESP: WiFi connected

    ESP->>ESP: Check NVS for existing sensor_id
    Note over ESP: sensor_id == 0 → Unregistered

    ESP->>API: POST /devices/register<br/>{public_key_hex, mac_address,<br/>enrollment_token, latitude?, longitude?}
```

## b. Backend Registration

<!--
FIX (Figure 7): same treatment as Part A — fonts bumped 32/26/26 -> 34/28/28.
-->
```mermaid
%%{init: {"sequence": {"actorFontSize": 34, "messageFontSize": 28, "noteFontSize": 28, "messageMargin": 38, "boxMargin": 10}}}%%
sequenceDiagram
    participant API as FastAPI<br/>Gateway
    participant DB as PostgreSQL<br/>+ PostGIS
    participant ESP as ESP32-C3<br/>Node
    participant NVS as ESP32 NVS<br/>Storage

    API->>API: Validate enrollment_token
    API->>DB: Check for existing device (MAC or public key)

    alt New Device
        API->>DB: INSERT Sensor (public_key, mac, coordinates)
        DB->>API: sensor_id assigned
    else Existing Device
        API->>DB: SELECT sensor_id WHERE mac_address = ...
        DB->>API: existing sensor_id
    end

    alt Coordinates provided
        API->>DB: ST_Contains query → assign zone
    else No coordinates
        API->>DB: Assign to "Unknown Region"
    end

    API-->>ESP: 200 OK {sensor_id: N}
    ESP->>NVS: Store sensor_id in NVS
    Note over ESP: Blue LED solid → Fully connected
    ESP->>ESP: Start SensorTask + NetworkTask
```
