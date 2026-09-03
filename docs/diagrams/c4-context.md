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
        mqtt_bridge["MQTT Bridge"]
        api["FastAPI Gateway"]
        redis[("Redis")]
        worker["Background Worker"]
        ai_worker["AI Report Worker"]
        postgres[("TimescaleDB")]
        
        mqtt_bridge -- "HTTP" --> api
        api -- "XADD" --> redis
        worker -- "XREAD" --> redis
        worker -- "INSERT" --> postgres
        worker -- "PUB alerts" --> redis
        ai_worker -- "POP queue" --> redis
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

```mermaid
%%{init: {"themeVariables": {"fontSize": "20px"}}}%%
flowchart TD
    user(("End User"))

    subgraph backend["Backend Layer (Docker)"]
        direction TB
        api["FastAPI Gateway"]
    end

    subgraph mobile["Mobile Layer"]
        direction BT
        app["React Native App"]
    end

    api -- "WSS" --> app
    app -- "REST" --> api
    app -- "UI" --> user

    style backend fill:#f8f9fa,stroke:#ced4da,stroke-width:2px,color:#000
    style mobile fill:#f8f9fa,stroke:#ced4da,stroke-width:2px,color:#000
```