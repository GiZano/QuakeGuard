= Deployment & Operations Guide

This section outlines the procedures for provisioning the QuakeGuard infrastructure in a local or development environment.

== Prerequisites

To orchestrate the full stack, the host machine must have the following dependencies installed:
- *Backend:* Docker Engine and Docker Compose.
- *Edge (IoT):* Visual Studio Code with the PlatformIO IDE extension.
- *Mobile:* Node.js (v18+) and the Expo Go application installed on a physical smartphone.

== Backend Provisioning

The backend services (PostgreSQL, TimescaleDB, Redis, FastAPI, Worker, AI-Worker, and MQTT Bridge) are fully containerized. The system uses a Hybrid Network Architecture where the backend runs locally, while exposing an automated Cloudflare tunnel for external WAN traffic.

+ Navigate to the project root and launch the orchestrator:
  ```bash
  ./scripts/quakeguard_init.sh
  ```
This single command automates the entire infrastructure deployment:
1. Spawns `tunnel_init.sh` to negotiate a new Cloudflare HTTPS tunnel.
2. Dynamically injects the generated URL into the Mobile and Firmware `.env` configurations.
3. Opens a 3-split terminal window (using `ptyxis` or `tmux`) that simultaneously boots the Docker Compose backend (with the `--profile ai` flag for LLaMa3.2), starts the Expo bundler for the mobile client, and compiles/flashes the ESP32 firmware via PlatformIO.

== Horizontal Worker Scaling

Because telemetry is consumed through Redis Streams consumer groups, the worker tier scales horizontally without reconfiguration: messages are balanced across the group automatically.
```bash
docker compose up --scale worker=N -d
```

== Observability & Telemetry Dashboards

System health and network latency are continuously monitored through a Grafana container. To eliminate manual configuration, QuakeGuard leverages Grafana's automated provisioning system:
- *Data Sources:* The `postgres.yml` file natively mounts the TimescaleDB connection parameters.
- *Dashboards:* The "Mission Control" JSON dashboard is mounted via `dashboards.yml` directly into `/etc/grafana/provisioning/dashboards/`.
Upon executing the orchestrator, Grafana exposes port `3000`, presenting a fully configured 4-tier dashboard:
 
#figure(
  image("assets/grafana_dashboard.png", width: 90%),
  caption: [QuakeGuard Mission Control Dashboard (Zone-Aware)],
) <fig-grafana>

1. *Live Seismograph:* Aggregated real-time Magnitude (PGA) and alert tables.
2. *IoT Telemetry:* Node counts, RSSI bar gauges, and ESP32 free heap stability.
3. *Backend Latency:* End-to-end packet latency and ingestion throughput (Events/sec).

== Seismic Simulation & Stress Testing

Two companion scripts exercise the ingestion pipeline:
- *`scripts/load_test.py`* — a high-concurrency End-to-End (E2E) stress test that simulates a massive seismic event through the real REST path (see the stress test section below).
- *`scripts/simulate_zone.py`* — streams synthetic per-zone readings straight through the ingestion flow, exercising the per-area cooldown fragmentation and the per-zone seismograph endpoints.

== Edge Node & Mobile Client Orchestration

Because the orchestrator (`quakeguard_init.sh`) dynamically resolves and injects environment variables, manual configuration of the edge node and mobile client is drastically reduced.

- *Edge Node:* The ESP32 is automatically flashed via PlatformIO during the orchestrator's boot sequence (`pio run -t upload -t monitor`). The firmware strictly requires compile-time secret injection, so rebuilding ensures the node receives the latest dynamic Cloudflare provisioning URL and Fallback Coordinates (now mapped to Milan, Italy North).
- *Mobile Client:* The Expo server is launched automatically. Ensure that the smartphone running Expo Go is connected to the same Local Area Network (LAN) as the host, and scan the QR code displayed in the top-right terminal window.

== Executing the Critical Stress Test

To validate the deployment, the system includes an End-to-End (E2E) stress test that simulates a massive seismic event.

From the `backend` directory, execute:
```bash
export API_URL="http://localhost:8000"
export NUM_SENSORS=150
export CONCURRENCY_LIMIT=50
python -m tests.stress_test
```
A successful test will conclude with the message `🏆 SYSTEM CERTIFIED`, confirming that the rate limiter, security gates, and per-area cooldown locks are functioning nominally.