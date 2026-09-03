# System Context Diagram — QuakeGuard

> Level 1 (System Context): shows the QuakeGuard system and the external actors/systems that interact with it.

```mermaid
flowchart TD
    user(("End User\n(Mobile)"))
    maintainer(("Maintainer\n(DevOps)"))
    mobile["Mobile App"]
    sensor["IoT Sensor\n(ESP32-C3)"]

    subgraph sys [QuakeGuard System]
        quakeguard["QuakeGuard Platform"]
    end
    style sys fill:none,stroke:#0b4884,stroke-width:2px,stroke-dasharray: 5 5

    mosquitto["Eclipse Mosquitto\n(Local MQTT)"]
    ollama["Ollama (Host)\n(LLM Inference)"]
    cloudflare["Cloudflare Tunnel\n(HTTPS)"]
    expo["Expo Push Service\n(iOS/Android)"]
    grafana["Grafana\n(Observability)"]

    quakeguard -- "Metrics" --> grafana
    grafana -- "Views" --> maintainer
    
    quakeguard -- "Request" --> ollama
    ollama -- "AI Report" --> quakeguard
    
    quakeguard -- "HTTP & WSS (Alerts, Reports)" --> cloudflare
    cloudflare -- "HTTP & WSS" --> mobile
    mobile -- "UI / Alerts" --> user
    
    quakeguard -- "Push" --> expo
    expo -- "Push" --> user

    style quakeguard fill:#1168bd,stroke:#0b4884,color:#ffffff,stroke-width:2px
```

## Container-Level Breakdown (a. Data Ingestion)

```mermaid
flowchart TD
    subgraph edge["IoT Edge Layer"]
        direction TB
        adxl["ADXL345"]
        gnss["NEO-6M GNSS"]
        esp32["ESP32-C3 Node"]
        adxl -- "I2C" --> esp32
        gnss -- "UART" --> esp32
    end

    subgraph backend["Backend Layer (Docker)"]
        direction TB
        api["FastAPI Gateway"]
        mqtt_bridge["MQTT Bridge"]
        redis[("Redis")]
        worker["Background Worker"]
        ai_worker["AI Report Worker"]
        postgres[("TimescaleDB")]
    end

    %% Collegamento diretto tra i layer per forzare l'impaginazione in verticale dritta
    esp32 -- "Register" --> api

    mosquitto["Eclipse Mosquitto"]
    ollama["Ollama (Host)"]

    esp32 -- "MQTT" --> mosquitto
    mqtt_bridge -- "Sub" --> mosquitto
    mqtt_bridge -- "HTTP" --> api
    
    api -- "XADD" --> redis
    worker -- "XREAD" --> redis
    worker -- "INSERT" --> postgres
    worker -- "PUB alerts" --> redis
    
    ai_worker -- "POP queue" --> redis
    ai_worker -- "POST" --> ollama
    ai_worker -. "PUB reports" .-> redis

    style edge fill:#f8f9fa,stroke:#ced4da,stroke-width:2px,color:#000
    style backend fill:#f8f9fa,stroke:#ced4da,stroke-width:2px,color:#000
```

## Container-Level Breakdown (b. Mobile Interaction)

```mermaid
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