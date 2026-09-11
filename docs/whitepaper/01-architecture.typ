= System Architecture & Overview

QuakeGuard is a distributed, high-throughput backend system designed for the real-time ingestion, cryptographic validation, and processing of seismic data from IoT devices. It serves as the core infrastructure for an Earthquake Early Warning (EEW) system. The architecture is explicitly designed to handle high-concurrency event firehosing during seismic swarms while maintaining strict security boundaries.

== High-Level Topology

The infrastructure is decoupled into three primary tiers (illustrated in @fig-context):

- *Edge Layer (IoT):* Composed of ESP32-C3 SuperMini microcontrollers interfaced with ADXL345 digital accelerometers. These nodes execute on-device Digital Signal Processing (DSP) using the STA/LTA (Short Term Average / Long Term Average) algorithm. 
- *Core Backend & Processing:* A polyglot backend architecture utilizing FastAPI (Python) as the API gateway. Validated data is asynchronously offloaded to a Redis Stream (`readings:stream`) and consumed by horizontally-scalable background workers via consumer groups. The workers persist time-series data into a PostgreSQL/PostGIS database (provisioned as a TimescaleDB hypertable) and trigger area-scoped alerts via Redis Pub/Sub.
- *Client Presentation Layer:* A React Native (Expo) mobile application providing users with real-time seismograph telemetry and instantaneous critical event notifications delivered through WebSockets and native push notifications.
- *Observability Layer:* A Grafana instance automatically provisioned via `docker-compose.yml` with a JSON dashboard and TimescaleDB datasource, providing system telemetry (latency, RSSI, free heap).
- *Device Onboarding:* A WiFiManager-based Captive Portal (`QuakeGuard-Setup` SSID) serves the mobile APK download link and displays the ECDSA public key for zero-touch enrollment. Additionally, the system features a Dynamic Demo Onboarding mode where a QR code is generated in the terminal to configure the mobile app URL without recompilation. A hardware reset via the BOOT button (GPIO 0, 5-second hold) re-enters AP mode for credential recovery.
- *Over-the-Air Updates:* A custom React Native hook (`useUpdateChecker`) polls GitHub Releases for new APK versions and triggers a native sideload prompt, eliminating manual update distribution.

Beyond the core data path, the platform provides three supporting capabilities:

- *Observability Layer:* A Grafana instance automatically provisioned via `docker-compose.yml` with a JSON dashboard and TimescaleDB datasource, providing system telemetry (latency, RSSI, free heap).
- *Device Onboarding:* A WiFiManager-based Captive Portal (`QuakeGuard-Setup` SSID) serves the mobile APK download link and displays the ECDSA public key for zero-touch enrollment. Additionally, the system features a Dynamic Demo Onboarding mode where a QR code is generated in the terminal to configure the mobile app URL without recompilation. A hardware reset via the BOOT button (GPIO 0, 5-second hold) re-enters AP mode for credential recovery.
- *Over-the-Air Updates:* A custom React Native hook (`useUpdateChecker`) polls GitHub Releases for new APK versions and triggers a native sideload prompt, eliminating manual update distribution.

#figure(
  image("assets/fig01-context-diagram.pdf", width: 115%, height: 105%, fit: "contain"),
  caption: [_High-Level Architecture Context Diagram_],
  numbering: _ => "2.1",
  placement: auto
) <fig-context>

== Data Plane and Control Plane

Following the v1.1.0 cloud migration, the architecture strictly separates the data and control pipelines (see @fig-container for the core container topology):

- *Data Plane (Telemetry):* Flows exclusively through a local Eclipse Mosquitto broker on port 1883. A Python-based MQTT bridge (`mqtt_subscriber.py`) subscribes to the `quakeguard/telemetry` topic and forwards payloads to the internal FastAPI ingestion pipeline via HTTP POST.
- *Control Plane (Provisioning & Management):* Device onboarding, cryptographic handshakes, and REST retrieval operations are routed through an HTTPS tunnel to the FastAPI endpoints (e.g., `/devices/register`). In development the tunnel is a *Cloudflare quick tunnel* (`cloudflared tunnel --url http://localhost:8000`); production should use a real HTTPS domain. The ngrok free-tier edge is not used because its bot-protection terminates ESP-IDF (mbedTLS) TLS handshakes via JA3 fingerprinting *before* any HTTP header can be read, so IoT clients never reach the backend.

#figure(
  image("assets/fig02-container-diagram.pdf", width: 115%, height: 105%, fit: "contain"),
  caption: [_High-Level Architecture Container Diagram_],
  numbering: _ => "2.2",
  placement: auto
) <fig-container>

== Key Design Principles

- *Zero-Trust Security:* Every telemetry payload must be cryptographically signed using an ECDSA (NIST256p) private key stored securely in the ESP32's Non-Volatile Storage (NVS). The backend validates these signatures (SHA-256) and device timestamps to prevent spoofing and replay attacks.
- *Asynchronous Decoupling:* The ingestion API is strictly non-blocking. Validated payloads are immediately pushed to the Redis Stream, allowing the gateway to acknowledge the IoT device in milliseconds while background workers handle heavy database transactions and magnitude estimations.
- *Spatial Awareness:* Leveraging PostGIS, the system automatically assigns newly provisioned sensors to geographic zones using polygon containment. A geohash-based Redis index (`zoneindex:<geohash>`) pre-computed at seed time provides a fast-path for coordinate-to-zone resolution, with PostGIS `ST_Contains` as the authoritative fallback. This enables targeted, geographically bounded alert broadcasting with per-area cooldowns.