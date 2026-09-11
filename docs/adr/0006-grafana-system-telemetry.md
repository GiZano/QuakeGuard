# ADR-0006: Grafana Observability for System Telemetry

## Status
Accepted (v2.1.0)

## Context
QuakeGuard requires a strict separation of concerns between the user-facing application (React Native Mobile App) and the engineering observability stack. The mobile app is designed to deliver visual/auditory alarms and a simple map of nodes for the end user. However, for systems engineering, researchers, and infrastructure maintainers, a deeper level of real-time telemetry is required to validate the network's health and hardware reliability.

Crucial metrics to track for Proof of Rigor:
- **Free Heap (ESP32):** To identify memory leaks over long uptimes.
- **End-to-End Latency:** The exact millisecond duration between the hardware trigger (ADXL345 interrupt) and the ingestion into the backend's Redis Streams. This is the most critical metric for an Earthquake Early Warning (EEW) system.
- **RSSI (Wi-Fi Signal):** To predict node disconnections or poor placement.
- **GNSS Fix Status / Satellites:** To validate the accuracy of the timing discipline.

## Decision
Integrate **Grafana** directly into the `docker-compose.yml` infrastructure as a zero-config, self-hosted observability layer.

1. **Telemetry Injection:** The ESP32-C3 firmware now appends `free_heap`, `rssi`, `gnss_satellites`, and a `device_timestamp_ms` to the JSON payload without modifying the core cryptographic signature (which protects the underlying sensor value and epoch).
2. **Latency Calculation:** The FastAPI ingress router calculates `latency_ms` by diffing the server's UTC time with the sensor's millisecond timestamp before enqueueing to Redis.
3. **Database Schema:** The `readings` TimescaleDB hypertable is dynamically altered at startup to store these telemetry columns.
4. **Grafana Datasource Provisioning:** A `postgres.yml` datasource is automatically provisioned, allowing Grafana to natively query TimescaleDB without needing a custom API or proxy layer.
5. **Dashboard-as-Code (JSON Provisioning):** A full "Mission Control" dashboard (`quakeguard_dashboard.json`) is auto-provisioned via `dashboards.yml`. This includes a robust **Geomap panel** that queries the active sensor coordinates, providing a visually spectacular, global real-time view of the fleet network (crucial for both operations and demo/Hollywood mode).

## Consequences
- **Positive:** System administrators have a real-time, zero-cost, open-source dashboard specifically optimized for high-frequency time-series data.
- **Positive:** True demonstration of Systems Engineering rigor by making end-to-end latency and memory health measurable and observable.
- **Positive:** Grafana connects natively to TimescaleDB, removing the need for a secondary telemetry database or complex API development.
- **Negative:** Slightly increased JSON payload size per telemetry packet.
