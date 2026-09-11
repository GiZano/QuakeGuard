# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0] - 2026-09-10
### Added
- **Grafana Mission Control:** Automated dashboard provisioning via JSON configuration, providing real-time seismographs, IoT telemetry (RSSI, free heap), and backend latency metrics instantly on `docker compose up`.
- **Hollywood Simulator:** `scripts/hollywood.sh` demo orchestrator for live exhibitions, simulating a multi-node seismic fleet with automated world-zone seeding.
- **Captive Portal Onboarding:** Embedded HTML captive portal in `WiFiManager` to distribute the Mobile APK and display the ECDSA Public Key for seamless device enrollment.
- **Dynamic Backend Onboarding:** Introduced QR Code generation via `qrencode` in the local terminal during boot. The mobile app now supports overriding the static API URL dynamically by saving it to `AsyncStorage`, enabling zero-recompilation demo setups.
- **Over-the-Air (OTA) Updates:** Custom GitHub-based updater hook (`useUpdateChecker`) inside the React Native app that polls the latest release and triggers a native prompt to sideload the updated APK.
- **System Telemetry Injection:** ESP32-C3 firmware now appends `free_heap`, `rssi`, `gnss_satellites`, and `device_timestamp_ms` to the payload without breaking the cryptographic signature.
- **End-to-End Latency Tracking:** FastAPI Gateway calculates exact latency between the hardware timestamp and UTC ingestion time, powering the core Proof of Rigor metric in Grafana.
- **Dependabot Configuration:** Automated dependency updates for pip (backend), npm (mobile), and GitHub Actions (`.github/dependabot.yml`).
- **Gitleaks Secret Scanning:** CI workflow (`.github/workflows/gitleaks.yml`) to prevent accidental credential leaks in commits.
- **Architecture Decision Records (ADRs):** Created `docs/adr/` with 5 initial ADRs documenting key architectural decisions (including the migration to local Mosquitto).
- **C4 and Sequence Diagrams:** Created `docs/diagrams/` with comprehensive Mermaid diagrams (C4 Context/Container, provisioning, alert delivery, triangulation), now fully compiled and embedded inside the Typst whitepaper.
- **Firmware Versioning:** Added `#define FIRMWARE_VERSION "2.1.0"` printed at boot via serial for field identification.
- **Pinout Reference:** Created `firmware/PINOUT.md` — unified GPIO mapping, LED behavior table, connector pinout, and passive component reference.
- **Flashing Guide:** Created `firmware/FLASHING.md` — standalone step-by-step flashing instructions for users without VS Code/PlatformIO IDE.
- **Privacy Policy:** Created `mobile/PRIVACY_POLICY.md` — documents data collection, storage, and third-party services for App Store/Play Store compliance.
- **SUPPORT.md:** Routing guide for all help channels (bugs, features, hardware, security, discussions).
- **Hardware Issue Template:** `.github/ISSUE_TEMPLATE/hardware_issue.md` for PCB, wiring, and component assembly reports.
- **Docker Compose Override Example:** `backend/docker-compose.override.yml.example` for local development customization.

### Changed
- **Zero-Config Local Architecture:** Completely replaced HiveMQ Cloud with an on-premise Eclipse Mosquitto broker (port 1883) via `docker-compose`, guaranteeing Zero-Config offline resilience and full WAN independence.
- **Magnitude Formula Alignment:** Corrected a critical documentation mathematical discrepancy; the frontend UI and whitepaper now correctly apply the ADXL345 calibration factor via division (`M = log10(PGA / 1.6) + 3.0`) in sync with the Python backend.
- **Dockerfile Multi-Stage Build:** Refactored `backend/Dockerfile` to a two-stage build (builder + runtime), reducing final image size.
- **BOM Enrichment:** Expanded `hardware/QuakeGuard_PCB/output/BOM.csv` with distributor links and socketable modules.
- **README Enhancements:** Added "PRs welcome" badge, prominent landing page link, CERN-OHL-S license reference, and v2.1.0 roadmap entry.
- **Version artifacts bumped to v2.1.0** (CITATION.cff, firmware header, README roadmap, SECURITY.md, Web Docs).

## [2.0.1] - 2026-09-01
### Changed
- **Documentation Polish (Zenodo Sync):** Removed residual LLM tags (`[cite: 1]`) from the technical whitepaper.
- **Architectural Coherence:** Aligned documentation across PDF, GitHub Wiki, and project website regarding tunnel architecture (Cloudflare) and threshold/anti-replay values (300s).
- **Project Licensing Health:** Clearly detailed testing pipelines, AGPL-3.0 software licensing, and CERN-OHL hardware licensing in the whitepaper and wiki.
- **Hardware Documentation:** Clarified `1.8f` firmware threshold vs `2.4` SIL offline threshold; contextualized ROC curve as preliminary MVP validation.
- **Roadmap & Threat Model:** Added detailed v1.2.x changelog to the whitepaper and clarified `ATECC608A` secure element alignment to Roadmap Phase R3.

## [2.0.0] - 2026-09-01
### Added
- **Hybrid Networking Architecture:** Transitioned from pure cloud to a Local-First / Cloud-Hybrid architecture for robust exhibition reliability.
- **Local Factory Provisioning:** Provisioning now uses local HTTP to bypass ESP32 mbedTLS memory limitations with large Let's Encrypt tunnel certificates.
- **DevOps Orchestration:** Introduced `scripts/quakeguard_init.sh` (Ptyxis 3-window orchestrator) and `scripts/tunnel_init.sh` (automated Cloudflare quick-tunnel generation with dynamic `.env` injection and automatic firmware rebuild).
- **Synchronized GNSS & Timing:** Implemented `NTP + PPS` (GPIO 2) discipline for millisecond-accurate time synchronization, replacing the hardcoded fix.
- **ADXL345 Hardware Calibration:** Introduced boot-time routine computing static offsets from 100 samples and writing biases directly to hardware registers (`OFSX`, `OFSY`, `OFSZ`).
- **SIL Validation (INGV FDSN):** Integrated ObsPy and FDSN queries to INGV for algorithmic validation on public, reproducible open data. ROC curve documented, completing the R1 validation milestone.
- **Hardware Documentation:** Documented diagnostic LED patterns (including Serial Fallback) and integrated Proprietary Hardware (v2.0.0 PCB) assembly visuals into the whitepaper and website.

### Changed
- Shifted default fallback GNSS coordinates (simulated and IoT) to Milan (Italy North) for regional alignment.
- Refactored `firmware/esp32_config.env.example` as the standard configuration template, reflecting the new Local IP architecture.
- Version artifacts bumped to v2.0.0 across documentation and web assets.

### Fixed
- **UnboundLocalError in Backend Worker:** Fixed a bug where a sub-threshold seismic event (`magnitude < 4.5`) would trigger an `UnboundLocalError` on `triangulation_data`, leading to batch rollback and empty dashboard graphs.
- **Subnet DNS Patch:** Removed erroneous `WiFi.config` in firmware that forced `INADDR_NONE` on the subnet mask, causing local routing failures (errno 118).
- **Mobile Map Crash:** Resolved a critical React Native `AIRMapMarker` rendering crash by implementing a strict null/undefined coordinate filter in the sensor mapping array.
- **Mobile UI Polish:** Updated the `MAG` badge to default to `0.00` (instead of `N/A`) and implemented dynamic Y-axis domain scaling (0 to 5+) for the `VictoryChart` seismograph.

## [1.2.2] - 2026-08-31
### Added
- **Zero-Trust USB Serial Fallback:** ECDSA-signed telemetry over USB CDC (`[QG:FB]` frames) when MQTT/WiFi is unreachable. Pure C++ core shared by firmware (`networkTask`) and host SIL validation (`test_serial_fallback.cpp`).
- **Host Serial Bridge:** `firmware/tools/serial_bridge.py` reads CDC frames and forwards to ingestion API with SSRF-safe URL validation.

### Changed
- **SonarCloud Quality Gate Fixes:** Removed `'unsafe-inline'` from CSP (externalized gtag to `analytics.js`), fixed dropdown accessibility (`<button>` instead of `<a role="button">`), replaced `role="status"` with native `<output>` element.
- **Code Quality Improvements:** Reduced cognitive complexity in backend (`geo.py`, `worker.py`, `timescale.py`), eliminated duplicate "Zone not found" literal, flattened nested conditionals in simulator and mobile, modernized firmware C++ (removed char arrays, fixed enum usage).
- **Version artifacts bumped to v1.2.2** (CITATION.cff, mobile footer, README roadmap, site labels).

### Fixed
- Serial bridge exit code returns non-zero on serial port open failure (S3516 blocker fix).

## [1.2.1] - 2026-08-14
### Added
- **Redis Streams Ingestion:** Transitioned from `LPUSH`/`BRPOP` to Redis Streams (`XADD`/`XREADGROUP`) enabling horizontal worker scaling and at-least-once delivery (`XAUTOCLAIM`).
- **TimescaleDB Hypertable:** Provisioned the `readings` table as a TimescaleDB hypertable for efficient time-series chunking and fast statistical rollups.
- **Batched DB Commits:** `worker.py` now processes and commits stream batches in a single atomic transaction for massive throughput under firehosing.
- **Geo-Zoning:** PostGIS zones as the source of truth (`Zone` model, `GET /zones`, `POST /zones/`), with a geohash-based Redis fast path for coordinate→zone lookup.
- **Zone Detection:** `GET /zones/locate` resolves a device's GPS position into a monitored polygon; Settings now ships "Detect my zone via GPS".
- **Per-Zone Seismograph:** `GET /zones/{zone_id}/readings` + `DELETE /zones/{zone_id}/readings`; the mobile dashboard renders a live seismograph per zone (horizontal zone strip) instead of mixing network-wide telemetry.
- **Per-Area Cooldown Fragmentation:** alert cooldown keys are now area-based (geohash region or zone), not global.
- **GNSS-Ready Data Model:** `Sensor.last_fix_at`, `Reading.lat/lon` captured at ingestion for area-fragmented cooldowns and future spatial correlation.
- **Per-Zone Alerts Feed:** `GET /zones/{zone_id}/alerts` retrieves the confirmed seismic alerts raised for a single area.
- **Live Chart Overhaul (mobile):** sliding window anchored to the wall clock (stale readings leave the window), linear MAG scale (MIN 3.5 / MED 4.0 / ALTO 4.5) with the axis pinned left, positive X seconds and a centered `TIME` label; the trace always renders inside the plot.
- **Settings Explore Section:** links to the GitHub repository (`GiZano/QuakeGuard`) and the QuakeGuard site; `QuakeGuard v1.2.1` footer.

### Changed
- Worker alert pipeline uses per-area cooldown keys and rounds-trip normalization (magnitude estimation shared with the mobile client).
- Peripheral MQTT subscriber wiring and `scripts/simulate_zone.py` updated for the per-zone stream flow.
- Version artifacts bumped to v1.2.1 (CITATION.cff, mobile footer, README roadmap).

## [1.2.0] - 2026-08-06
### Added
- **On-Premise AI Emergency Reports:** New AI layer generates human-readable emergency reports from confirmed seismic alerts via a local Ollama LLM (`llama3.2:1b` default), keeping telemetry on the host.
- **`ollama_client.py`:** Deterministic report generation (`temperature 0.0`, `top_k 1`, streaming disabled) with a strict system prompt ("Only use the provided JSON telemetry. Do not invent data.") and explicit `"AI report unavailable."` fallback on failure.
- **`EmergencyReport` Model & State Machine:** `PENDING → COMPLETED | FAILED` lifecycle, persisted in PostgreSQL alongside alerts.
- **`ai_report_worker.py`:** Dedicated consumer of the `ai_report_queue`; publishes `EMERGENCY_REPORT` to the `ai_reports` Redis channel, routes failures to `ai_report_queue_dlq`, and handles graceful shutdown.
- **Worker Integration:** Alert engine now enqueues report jobs non-blocking (gated by `AI_REPORT_ENABLED`, default `false`); alert payloads carry `alert_id`.
- **`GET /reports/{alert_id}`:** REST endpoint for report retrieval after WebSocket reconnect.
- **Docker Compose `ai` profile:** `ollama` and `ai-worker` services behind a profile; `init-scripts/ollama-entrypoint.sh` auto-pulls the model on startup.
- **Mobile Report UI:** Inline AI report banner + history cards (summary + recommendations; "Report unavailable" badge on `FAILED`), driven by the `ai_reports` WebSocket channel.
- **Unit Tests:** Coverage for the Ollama client, AI worker state machine, worker enqueue path, and EmergencyReport model (68 backend tests; mobile store tests for report handling).

### Changed
- WebSocket broadcaster subscribes to the `ai_reports` channel in addition to `quake_alerts`.
- Mobile `WebSocketContext` handles `EMERGENCY_REPORT` messages and stores the latest report; `useAlertStore` keeps a `reports` map keyed by `alert_id`.

## [1.1.0] - 2026-07-29
### Added
- **HiveMQ Cloud MQTT Integration:** Migrated from local MQTT broker to a fully managed, TLS-secured cloud broker.
- **Python MQTT Bridge (`mqtt_subscriber.py`):** New service to proxy MQTT payloads to the HTTP ingestion pipeline securely.
- **ngrok HTTPS Tunnel:** Enabled secure, remote exposure of the control plane for device registration.
- **Docs as Code:** Added modular Typst documentation (`docs/`) outlining the entire system architecture.

### Changed
- Refactored ESP32 firmware to connect to port 8883 (TLS) and authenticate via standard MQTT credentials.
- Updated Mobile React Native App to point to the new remote WebSocket endpoint.
- Hardened Redis `seismic_events` queue to handle edge-case worker disconnects.

## [1.0.0] - 2026-06-15
### Added
- Initial stable release for the Hackersgen contest.
- STA/LTA seismic detection algorithm implemented in C++ (ESP32-C3).
- FastAPI backend with PostgreSQL + PostGIS integration for sensor mapping.
- ECDSA cryptographic signing and Zero-Trust device provisioning.
- React Native Mobile App with WebSockets and native haptic alerts.
- End-to-End stress test suite (`tests/stress_test.py`).
