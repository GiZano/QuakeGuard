# ADR-0002: HiveMQ Cloud as the MQTT Broker

## Status
Deprecated (Superseded by [ADR-0005](0005-local-mosquitto-migration.md) in v2.1.0)

## Context
The ESP32-C3 firmware transmits cryptographically signed seismic telemetry via MQTT. The system requires a broker that:

1. Supports TLS (port 8883) for transport-layer encryption
2. Is reachable from any network (ESP32 nodes may be behind NAT)
3. Has minimal operational overhead (no broker to self-host and maintain)
4. Supports standard MQTT username/password authentication

## Decision
Use **HiveMQ Cloud (Serverless)** as the managed MQTT broker:

- Managed, zero-ops TLS termination on port 8883
- Free tier sufficient for development and small-scale deployment
- Standard Paho-compatible client library on both ESP32 (PubSubClient) and Python (paho-mqtt)
- No self-hosted infrastructure to maintain or secure

The Python MQTT bridge (`mqtt_subscriber.py`) subscribes to `quakeguard/telemetry` and forwards payloads to the HTTP ingestion pipeline, keeping the data plane (MQTT) separate from the control plane (REST).

## Consequences
- **Positive:** Zero infrastructure overhead, TLS built-in, globally reachable.
- **Negative:** WAN dependency — the alert path depends on internet connectivity. The "local-first resilience" claim (R2) only holds for on-premise topology with a local broker.
- **Risk:** Vendor lock-in is minimal (standard MQTT protocol), but a self-hosted Mosquitto would eliminate the WAN dependency.

## Alternatives Considered
- **Self-hosted Mosquitto:** Full local control, enables true local-first resilience. Documented as a future step in ROADMAP.md. Currently, the added operational burden outweighs benefits for a 2-person team.
- **EMQX Cloud:** Similar managed offering, but HiveMQ's free tier was more generous at evaluation time.
- **AWS IoT Core:** Enterprise-grade but introduces AWS dependency and costs that are disproportionate for a research/educational project.
