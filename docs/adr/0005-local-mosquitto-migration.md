# ADR-0005: Local Mosquitto as the Primary MQTT Broker

## Status
Accepted (v2.1.0)

## Context
In ADR-0002, HiveMQ Cloud was selected as the MQTT broker to avoid self-hosting infrastructure and provide managed TLS. However, QuakeGuard aims to achieve "Zero-Config" deployment and "Local-First Resilience" (Claim R2 in the architectural whitepaper).

Relying on a cloud broker like HiveMQ introduces a strict WAN dependency: if the internet connection drops during an earthquake (a highly probable scenario), the nodes cannot deliver telemetry to the backend, rendering the local processing useless.

## Decision
Migrate the primary telemetry transport from HiveMQ Cloud back to a locally hosted **Eclipse Mosquitto** instance running inside the backend's Docker Compose stack.

- Mosquitto is bundled in `docker-compose.yml` natively.
- Both the FastAPI backend and MQTT bridge communicate with it over the internal Docker network.
- ESP32 nodes connect to the local IP of the host machine (e.g., `192.168.1.100`) on port 1883.
- `mosquitto.conf` is configured for local access (`allow_anonymous true` for zero-config developer experience, relying on internal LAN security).

## Consequences
- **Positive:** **True Local-First Resilience.** The entire stack (Sensors -> Broker -> Backend -> AI Worker -> TimescaleDB) runs entirely offline on a local area network (LAN).
- **Positive:** **Zero-Config DX.** Developers no longer need to register for a HiveMQ account, generate API keys, or configure TLS certificates just to test the firmware. `docker compose up` brings up the *entire* infrastructure.
- **Negative:** Telemetry is sent unencrypted (port 1883) over the local Wi-Fi. However, since the payloads themselves are cryptographically signed with ECDSA (P-256) and verified by the backend, data integrity and non-repudiation are guaranteed even over plaintext transport.
- **Negative:** ESP32 nodes must be manually configured with the host's local IP address in `esp32_config.env` before flashing.

## Relation to Previous ADRs
- Deprecates **ADR-0002 (HiveMQ Cloud)**. The cloud broker approach is abandoned in favor of operational sovereignty and disaster resilience.
