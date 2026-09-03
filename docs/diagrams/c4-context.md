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

    sensor -- "MQTT" --> mosquitto
    mosquitto -- "MQTT" --> quakeguard
    sensor -- "Register" --> quakeguard

    quakeguard -- "Metrics" --> grafana
    grafana -- "Views" --> maintainer
    
    quakeguard -- "Request" --> ollama
    ollama -- "AI Report" --> quakeguard
    
    quakeguard -- "HTTP & WSS\n(Alerts, Reports)" --> cloudflare
    cloudflare -- "HTTP & WSS" --> mobile
    mobile -- "UI / Alerts" --> user
    
    quakeguard -- "Push" ---> expo
    expo -- "Push" --> user

    style quakeguard fill:#1168bd,stroke:#0b4884,color:#ffffff,stroke-width:2px
```

## Container-Level Breakdown

```mermaid
---
config:
  themeVariables:
    fontSize: 36px
    lineColor: '#343a40'
  flowchart:
    padding: 60
  layout: fixed
---
flowchart TB
 subgraph edge["IoT Edge Layer<br>"]
    direction LR
        adxl["ADXL345"]
        gnss["NEO-6M GNSS"]
        esp32["ESP32-C3 Node"]
  end
 subgraph mobile["Mobile Layer<br>"]
    direction TB
        app["React Native App"]
  end
 subgraph backend["Backend Layer (Docker)<br>"]
    direction LR
        worker["Background Worker"]
        mqtt_bridge["MQTT Bridge"]
        api["FastAPI Gateway"]
        redis[("Redis")]
        ai_worker["AI Report Worker"]
        postgres[("TimescaleDB")]
  end
    adxl -- I2C --> esp32
    gnss -- UART --> esp32
    edge ~~~ mobile
    mqtt_bridge -- HTTP --> api
    api -- XADD --> redis
    redis -- XREAD --> worker
    worker -- INSERT --> postgres
    worker -- PUB alerts --> redis
    redis -- POP queue --> ai_worker
    esp32 -- Register --> api
    esp32 -- MQTT --> mosquitto["Eclipse Mosquitto"]
    mosquitto -- Sub --> mqtt_bridge
    ai_worker -- POST --> ollama["Ollama (Host)"]
    ai_worker -- PUB reports --> redis
    api -. WSS .-> app
    app -- REST --> api
    app -- UI --> user(("End User"))
    ollama -- AI Report --> ai_worker

    style edge fill:#f8f9fa,stroke:#6c757d,stroke-width:6px,color:#000
    style mobile fill:#f8f9fa,stroke:#6c757d,stroke-width:6px,color:#000
    style backend fill:#f8f9fa,stroke:#343a40,stroke-width:6px,color:#000
```
