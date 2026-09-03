= Data Plane & Message Broker (MQTT)

With the release of v2.1.0, QuakeGuard migrated its Data Plane from a cloud-based MQTT architecture to a resilient, local-first infrastructure. This decoupling ensures that high-frequency seismic telemetry is handled by a dedicated message broker optimized for IoT, freeing the edge nodes from the overhead of HTTP round-trips while guaranteeing resilience against WAN outages.

== Eclipse Mosquitto Infrastructure

The core of the Data Plane is a local Eclipse Mosquitto broker, orchestrated natively within the Docker Compose stack.
- *Local-First Transport:* Telemetry is transmitted over port 1883. Removing the cloud dependency means the system operates autonomously even if internet connectivity drops during a seismic event.
- *Authentication:* The broker requires explicit `MQTT_USERNAME` and `MQTT_PASSWORD` credentials for every connection.
- *Topic Topology:* All valid seismic anomalies are published to the unified `quakeguard/telemetry` topic.

== Edge Node Implementation (Firmware)

On the ESP32-C3, the `networkTask` handles the MQTT transmission asynchronously. 
- To support TLS on resource-constrained hardware, the firmware utilizes `WiFiClientSecure::setInsecure()` combined with the `PubSubClient` library. 
- When a `SeismicEvent` is popped from the FreeRTOS queue, the firmware packages the JSON and fires the payload to the broker. This "fire-and-forget" approach reduces transmission blocking time to milliseconds, ensuring the `sensorTask` is never starved of CPU cycles.

== Host Serial Bridge — Second Ingestion Path 

When MQTT is unreachable the host can collect `[QG:FB]` frames over USB CDC and forward them to the same ingestion pipeline. `firmware/tools/serial_bridge.py` tails `/dev/ttyACM0` (default `SERIAL_PORT`), filters lines starting with `[QG:FB]`, parses the JSON suffix and POSTs it to `/readings/` with `X-API-Key` — identical security gates as the MQTT bridge. URL validation (`_validate_api_url`) restricts schemes to `http/https`, rejects embedded credentials and non-alphanumeric hostnames (SSRF guard), and `parse_frame()` returns `None` on boot-log noise so the reader never crashes on malformed lines. A `dry-run` and `--stdin` mode plus the `iot-ci.yml` parser smoke test keep the bridge testable without hardware.

== Internal MQTT Bridge Service

To securely ingest the MQTT data into the backend, QuakeGuard employs a dedicated bridging microservice (`mqtt_subscriber.py`).
- *Protocol Bridging:* Written in Python using the `paho.mqtt.client` (v2 API), the bridge acts as an authorized subscriber to the Eclipse Mosquitto broker.
- *Internal Routing:* Upon receiving a message on `quakeguard/telemetry`, the bridge wraps the payload and forwards it to the internal FastAPI ingestion endpoint (`/readings/`) via a standard HTTP POST request.
- *Security Injection:* The bridge injects the `X-API-Key` header into the HTTP request, acting as a trusted proxy between the MQTT broker and the internal Docker network. If the API rejects the payload (e.g., due to an invalid cryptographic signature), the bridge logs the failure without crashing.