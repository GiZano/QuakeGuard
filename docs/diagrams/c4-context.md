# System Context Diagram — QuakeGuard

> Level 1 (System Context): shows the QuakeGuard system and the external actors/systems that interact with it.

```mermaid
%%{init: {"themeVariables": {"fontSize": "26px"}}}%%
flowchart TD
    user(("End User\n(Mobile)"))
    maintainer(("Maintainer\n(DevOps)"))
    mobile["Mobile App"]
    sensor["IoT Sensor\n(ESP32-C3)"]

    subgraph sys [ ]
        direction LR
        quakeguard["QuakeGuard Platform"] ~~~ label["QuakeGuard System"]
    end
    style sys fill:#fefce8,stroke:#d4af37,stroke-width:2px,stroke-dasharray: 5 5
    style label fill:none,stroke:none,color:#000,font-weight:bold,font-size:24px

    mosquitto["Eclipse Mosquitto\n(Local MQTT)"]
    ollama["Ollama (Host)\n(LLM Inference)"]
    cloudflare["Cloudflare Tunnel\n(HTTPS)"]
    expo["Expo Push Service\n(iOS/Android)"]
    grafana["Grafana\n(Observability)"]

    quakeguard -- "Metrics" --> grafana
    grafana -- "Views" --> maintainer
    
    quakeguard -- "Request" --> ollama
    ollama -- "AI Report" --> quakeguard
    
    quakeguard -- "HTTP & WSS\n(Alerts, Reports)" --> cloudflare
    cloudflare -- "HTTP & WSS" --> mobile
    mobile -- "UI / Alerts" --> user
    
    quakeguard -- "Push" --> expo
    expo -- "Push" --> user

    style quakeguard fill:#1168bd,stroke:#0b4884,color:#ffffff,stroke-width:2px
```

## Container-Level Breakdown (a. Data Ingestion)

<!--
FIX (Figure 2):
- "PUB reports" was overlapping "POP queue" because both edges ran between
  ai_worker and redis in the same direction. Reversed the POP queue edge
  (redis -> ai_worker, since the worker is the one popping/reading) which
  gives dagre two distinct paths instead of two parallel ones on top of
  each other.
- Reordered node declarations inside the backend subgraph (worker declared
  before mqtt_bridge/api) so the "Register" edge from the ESP32 node no
  longer crosses the "HTTP" edge from the MQTT Bridge to FastAPI Gateway.
-->
```mermaid
%%{init: {"themeVariables": {"fontSize": "20px"}}}%%
flowchart TD
    subgraph edge["IoT Edge Layer"]
        direction TB
        adxl["ADXL345"]
        gnss["NEO-6M GNSS"]
        esp32["ESP32-C3 Node"]
        adxl -- "I2C" --> esp32
        gnss -- "UART" --> esp32
    end

    mosquitto["Eclipse Mosquitto"]

    subgraph backend["Backend Layer (Docker)"]
        direction TB
        worker["Background Worker"]
        mqtt_bridge["MQTT Bridge"]
        api["FastAPI Gateway"]
        redis[("Redis")]
        ai_worker["AI Report Worker"]
        postgres[("TimescaleDB")]

        mqtt_bridge -- "HTTP" --> api
        api -- "XADD" --> redis
        worker -- "XREAD" --> redis
        worker -- "INSERT" --> postgres
        worker -- "PUB alerts" --> redis
        redis -- "POP queue" --> ai_worker
    end

    ollama["Ollama (Host)"]

    esp32 -- "Register" --> api
    esp32 -- "MQTT" --> mosquitto
    mosquitto -- "Sub" --> mqtt_bridge

    ai_worker -- "POST" --> ollama
    ai_worker -. "PUB reports" .-> redis

    style edge fill:#f8f9fa,stroke:#ced4da,stroke-width:2px,color:#000
    style backend fill:#f8f9fa,stroke:#ced4da,stroke-width:2px,color:#000
```

## Container-Level Breakdown (b. Mobile Interaction)

<!--
FIX (Figure 3):
- Only content changed: direction TD -> LR. The old top-down layout was
  tall and narrow (aspect ~0.6:1); at `width: 100%` on the page it had to
  be blown up a lot to fill the column, which is what made it look
  "enormous" and pixelated. The wide/short LR layout needs far less
  upscaling to fill the same width, so it stays crisp and looks
  proportionate. Rendered at a higher raster scale (see notes.md) for
  extra sharpness on top of that.
-->
```mermaid
%%{init: {"themeVariables": {"fontSize": "20px"}}}%%
flowchart LR
    user(("End User"))

    subgraph backend["Backend Layer (Docker)"]
        direction TB
        api["FastAPI Gateway"]
    end

    subgraph mobile["Mobile Layer"]
        direction TB
        app["React Native App"]
    end

    api -- "WSS" --> app
    app -- "REST" --> api
    app -- "UI" --> user

    style backend fill:#f8f9fa,stroke:#ced4da,stroke-width:2px,color:#000
    style mobile fill:#f8f9fa,stroke:#ced4da,stroke-width:2px,color:#000
```
