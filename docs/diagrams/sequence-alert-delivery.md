# Sequence Diagram — Alert Delivery (Earthquake Detection → Mobile Alert)

## a. Event Ingestion

<!--
FIX (Figure 8): "testo piccolo e diagramma che esce dalla pagina".
Bumped fonts 20/18/18 -> 22/20/20 and tightened actor/message/box/note
margins so the extra font size didn't blow up the footprint. Net effect:
height dropped from 904px to ~808px at the same width, giving a wider,
flatter aspect ratio (~1.94:1) that leaves much more headroom against the
page. See notes.md for the companion Typst fix needed to fully guarantee
no overflow, since Figures 8+9 share one page.
-->
```mermaid
%%{init: {"sequence": {"actorFontSize": 22, "messageFontSize": 20, "noteFontSize": 20, "actorMargin": 45, "messageMargin": 18, "boxMargin": 5, "boxTextMargin": 4, "noteMargin": 7, "diagramMarginX": 15, "diagramMarginY": 6}}}%%
sequenceDiagram
    participant ADXL as ADXL345<br/>Sensor
    participant ESP as ESP32-C3<br/>Node
    participant MQTT as Eclipse<br/>Mosquitto
    participant Bridge as MQTT<br/>Bridge
    participant API as FastAPI<br/>Gateway
    participant Redis as Redis
    participant Worker as Background<br/>Worker
    participant DB as PostgreSQL

    ADXL->>ESP: Acceleration data (100 Hz, I2C)
    ESP->>ESP: HPF → STA/LTA detection
    Note over ESP: STA/LTA ratio > 1.8 → TRIGGER

    ESP->>ESP: ECDSA sign (value:timestamp)
    ESP->>MQTT: PUBLISH quakeguard/telemetry<br/>{value, sensor_id, timestamp, signature}

    MQTT->>Bridge: Deliver message (TLS)
    Bridge->>API: POST /readings/ (X-API-Key header)

    API->>API: Validate API Key
    API->>API: Verify ECDSA signature
    API->>API: Check anti-replay (300s window)
    API->>API: Rate limit check (50 req/s/IP)

    API->>Redis: XADD readings:stream

    Worker->>Redis: XREADGROUP (batch)
    Worker->>Worker: Calculate magnitude<br/>M = log10(PGA/scale) × K + B
    Worker->>DB: INSERT INTO readings
```

## b. Alert Delivery & AI Report

<!--
FIX (Figure 9): same treatment as Part A. This one was the taller of the
two (nested alt/opt blocks), so it benefited the most: height dropped
from 1054px to ~788px at the same width (~1.99:1 aspect), roughly a 25%
reduction. Fonts bumped 20/18/18 -> 22/20/20.
-->
```mermaid
%%{init: {"sequence": {"actorFontSize": 22, "messageFontSize": 20, "noteFontSize": 20, "actorMargin": 45, "messageMargin": 18, "boxMargin": 5, "boxTextMargin": 4, "noteMargin": 7, "diagramMarginX": 15, "diagramMarginY": 6}}}%%
sequenceDiagram
    participant Worker as Background<br/>Worker
    participant Redis as Redis
    participant DB as PostgreSQL
    participant AI as AI Report<br/>Worker
    participant Ollama as Ollama<br/>LLM
    participant WS as WebSocket
    participant App as Mobile<br/>App
    participant User as End<br/>User

    alt M ≥ 4.5 (Alert threshold)
        Worker->>Redis: Check cooldown lock (alert_cooldown:geohash)

        alt No active cooldown
            Worker->>DB: INSERT INTO alerts
            Worker->>Redis: SET cooldown lock (60s TTL)
            Worker->>Redis: PUBLISH quake_alerts<br/>{zone, magnitude, alert_id}

            Redis->>WS: Broadcast to subscribers
            WS->>App: QUAKE_ALERT message

            App->>App: SOS haptic vibration
            App->>App: Push notification
            App->>User: 🚨 EARTHQUAKE ALERT

            opt AI Reports enabled
                Worker->>Redis: LPUSH ai_report_queue
                AI->>Redis: BRPOP ai_report_queue
                AI->>Ollama: POST /api/generate (structured prompt + telemetry)
                Ollama-->>AI: Emergency report text
                AI->>DB: UPDATE EmergencyReport (COMPLETED)
                AI->>Redis: PUBLISH ai_reports
                Redis->>WS: Broadcast report
                WS->>App: EMERGENCY_REPORT message
                App->>User: 📋 AI Report banner
            end

        else Cooldown active
            Note over Worker: Duplicate suppressed (60s window)
        end
    end
```
