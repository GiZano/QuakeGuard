# ROADMAP — QuakeGuard

> Semantic Versioning progression.

---

## v1.0.0 — Edge Seismic Detection (Released)

Edge seismic detection on ESP32 with local alerts.

- ADXL345 acquisition at 100 Hz with STA/LTA triggering
- ECDSA signature on every payload
- Local alert via LED / serial

---

## v1.1.0 — Cloud & Security (Released)

Data Plane migration to MQTT Cloud (HiveMQ), REST Control Plane (HTTPS) and TLS security.

- Data Plane: ESP32 → HiveMQ Cloud (port 8883, TLS + username/password)
- Control Plane: HTTPS tunnel for REST provisioning — *Cloudflare quick tunnel* in dev (the ngrok free-tier edge is unusable by ESP32 IoT clients: it terminates ESP-IDF/mbedTLS TLS handshakes via JA3 fingerprinting)
- `setInsecure()` for TLS handshake on ESP32
- MQTT Bridge (Python Paho) with TLS
- Working mobile dashboard with live data
- Active CI/CD

---

## v1.2.0 — On-Premise AI Reports (Released)

On-premise AI integration (LLM in the backend) to generate textual emergency reports from MQTT data.

- ✅ On-premise LLM via Ollama (`llama3.2:1b`) consuming confirmed alerts — telemetry never exposed
- ✅ Automatic emergency report generation: magnitude, zone, timestamp, recommendations (deterministic, anti-hallucination)
- ✅ WebSocket push of the AI report to the mobile app (banner + history card)
- ✅ `PENDING → COMPLETED | FAILED` state machine with DLQ and explicit fallback
- ✅ REST endpoint `GET /reports/{alert_id}`

---

## v1.2.1 — Geo-Zoning & Cooldown Fragmentation (GNSS-ready) (Released)

Geographic zone division designed so the system is ready for the GNSS upgrade (v1.3). The alert cooldown is fragmented from the coarse macro-region level down to a per-area geohash granularity, and the zone-assignment hot path is offloaded from PostGIS queries to a Redis geohash index — with PostGIS kept as the single source of truth.

> **Blocking prerequisite for v1.3 (GNSS):** real GNSS coordinates replace the hardcoded Rome fix in the firmware (`main.cpp`), so the geo layer must already resolve zones and fragment cooldowns from raw coordinates — not from a fixed registration-time zone.

- ✅ **Geohash zone index (Redis fast path)** — `backend/src/geo.py`: at seed time every zone polygon is decomposed into the set of geohash cells (prec 3, ~156 km) it intersects; `resolve_zone()` (in `main.py`) resolves a coordinate from the Redis SET without a DB round-trip. Redis miss or ambiguous multi-zone match falls back to the authoritative PostGIS `ST_Contains` + `ST_Area ASC` query, so the cache can never assign a wrong zone
- ✅ **Pure-Python geohash encoder** matching PostGIS `ST_GeoHash` — zero new dependencies, deterministic keys shared by seed-time index and runtime lookup
- ✅ **Fragmented cooldown lock** — `alert_cooldown:<geohash>` (prec 4, ~50 km) instead of `alert_cooldown:<zone_id>`: two independent events inside the same overlapping macro-polygon no longer silence each other. Legacy `alert_cooldown:zone:<id>` retained for coordinates-less sensors
- ✅ **GNSS-ready data model** — `Sensor.last_fix_at`, `Reading.latitude`/`longitude`; the ingestion payload carries the sensor's fix + geohash; `/devices/register` re-resolves the zone if a relocated node reports a changed fix
- ✅ **Real spatial tests** — integration tests assert resolution against the seeded PostGIS polygons (Milan, Madrid, Tokyo, unknown point), and `point_to_geohash` is cross-validated against PostGIS `ST_GeoHash`

> **Future hardening (for administrative polygons):** `ST_SimplifyPreserveTopology` + GiST tuning, sizing zones so an event cannot physically reach the adjacent zone (~50–100 km for destructive surface-wave propagation).

---

## v1.2.2 — Zero-Trust Serial Fallback (Released)

Signed telemetry over a serial link (USB CDC) when MQTT/WiFi connectivity is lost, so the host still receives data during offline simulations.

- ✅ **Second consumer of the existing event queue** — `networkTask` dispatches each event to the first available path: MQTT publish (unchanged data plane), USB serial fallback, or in-memory retention ring when no path exists
- ✅ **ECDSA-signed payloads, identical signing to the MQTT data plane** — `SerialFallback.h` builds `[QG:FB]{...}` frames with the exact MQTT JSON; retained events are re-signed with the current wall time at drain so the backend ±300 s replay window accepts them
- ✅ **USB-host-aware retention** — `Serial.isConnected()` (HWCDC) distinguishes a real host from a power-only USB charger: with no host, events are retained in the ring instead of being written to a dead port; drained FIFO when a path becomes available
- ✅ **Offline wall clock** — software clock anchored at the first NTP sync (`epoch_at_sync` + `millis()`), so timestamps stay valid even after WiFi drops; no frames emitted before time is valid
- ✅ **Host-side bridge collecting serial output and forwarding to the ingestion pipeline** — `firmware/tools/serial_bridge.py` reads `/dev/ttyACM0`, filters `[QG:FB]` frames, and POSTs them to `/readings/` with `X-API-Key` (same forwarding as the MQTT bridge)
- ✅ **Automatic first-boot provisioning** — compile-time `SENSOR_ID` shortcut removed; the node POSTs `/devices/register` (public key + MAC + enrollment token + GNSS-ready coords) and the backend assigns the `sensor_id` and zone. Verified live on hardware. Backend accepts NULL geometry when a node has no GNSS fix yet

---

## v1.3.0 — Synchronized GNSS (Released)

Advanced GNSS synchronization of nodes for exact timestamps.

- ✅ Optional GPS/GNSS module on ESP32
- ✅ Correct NTP + PPS timestamps for all nodes
- ✅ Replace hardcoded GPS (Rome coordinates) with real coordinates
- ✅ ADXL345 offset calibration on boot

---

## v2.0.0 — Epicenter Triangulation

Triangulation algorithm. Multi-node spatial correlation combined with AI reports to compute the internal epicenter.

- ✅ Triangulation algorithm from ≥3 nodes
- ✅ Multi-node spatial and temporal correlation
- ✅ Internal epicenter computation
- ✅ AI + triangulation data fusion for precise alerts
- ✅ KiCad schematics and Gerber files of the node PCB (hardware blueprints for the triangulation node) — fabricated and assembled, ready for deployment

---

## v2.0.1 — Documentation & Zenodo Sync (Released)

Documentation-only patch aligning the technical whitepaper, GitHub Wiki, and project website.

- ✅ Typst PDF compilation polished (LLM citation removal, version updates)
- ✅ Architectural Coherence: tunnel architecture (Cloudflare) and threshold/anti-replay values (300s) synchronized across all assets
- ✅ Hardware Documentation: clarified `1.8f` firmware threshold vs `2.4` SIL offline threshold; ROC curve contextualized
- ✅ Project Licensing Health: testing pipelines, AGPL-3.0 software licensing, and CERN-OHL hardware licensing explicitly documented
- ✅ `CITATION.cff` bumped for Zenodo archival

---

## v2.1.1 — Demo Calibration & Repository Fixes (Released)

- ✅ **Demo Plausibility:** Modified the `/demo/trigger-earthquake` endpoint (magnitude 5.0, PostGIS dynamic centroid, 1.6 calibration factor).
- ✅ **Hollywood Simulator:** Added Pisa to local orchestration.
- ✅ **Versioning Fix:** Cleaned up ghost roadmap entries.


## v2.1.0 — System Telemetry & Repository Health (Released)

Comprehensive repository maturity improvements: CI hardening, architectural documentation, developer experience, and compliance foundations.

- ✅ **Dependabot** for automated dependency updates (pip, npm, GitHub Actions)
- ✅ **Gitleaks** secret scanning in CI (prevents credential leaks)
- ✅ **Architecture Decision Records (ADRs):** 4 initial ADRs (Redis Streams, HiveMQ, Hybrid Edge AI, CERN-OHL)
- ✅ **C4 and Sequence Diagrams** in Mermaid (versionable, GitHub-renderable)
- ✅ **Multi-stage Dockerfile** (builder + runtime stages, reduced image size)
- ✅ **Firmware versioning** (`FIRMWARE_VERSION` define, printed at boot)
- ✅ **Pinout reference** (`firmware/PINOUT.md`) and **Flashing guide** (`firmware/FLASHING.md`)
- ✅ **Privacy Policy** (`mobile/PRIVACY_POLICY.md`) for App Store/Play Store readiness
- ✅ **SUPPORT.md**, **Hardware Issue Template**, **Docker Compose override example**
- ✅ **BOM enrichment** (manufacturer, cost, distributor links, socketable modules)
- ✅ **README enhancements** (landing page link, PRs welcome badge, hardware disclaimer)

- ✅ **Grafana Dashboards:** natively connected to TimescaleDB via automated JSON provisioning
- ✅ **System Telemetry:** (End-to-End Latency, ESP32 Free Heap, RSSI, GNSS Fix) appended to payload
- ✅ **Captive Portal Onboarding:** `WiFiManager` embedded HTML to serve the mobile APK and display the ECDSA Public Key
- ✅ **Dynamic Demo Onboarding:** terminal QR Code (`qrencode`) and mobile `AsyncStorage` override for zero-recompile tunnel routing
- ✅ **Over-the-Air (OTA) Updates:** GitHub-based React Native automatic in-app updater
- ✅ Real-time visualization of multi-node network activity
- ✅ Automated zero-config deployment via `docker-compose.yml`
- ✅ **Hollywood Simulator:** `scripts/hollywood.sh` demo orchestrator for live exhibitions with automated zone seeding

---

> **Geo-zoning & cooldown-lock design (relevant for the paper's System-Engineering claim):**
> - **Implemented in v1.2.1:** fragmentation to Geohash keys (`alert_cooldown:<geohash>`),
>   which offloads zone assignment from PostGIS `ST_Contains` to fast Redis lookups
>   and stops overlapping macro-regions from silencing independent earthquakes.
> - **Future:** H3 hex-grid reindexing is re-evaluated when the v2.1 triangulation
>   clustering is designed; daily H3 resolution can replace the coarsen geohash grid
>   with no zone-model change. For real administrative polygons: apply
>   `ST_SimplifyPreserveTopology` + a GiST index; size zones so an event cannot
>   physically reach the adjacent zone (~50–100 km for destructive surface-wave propagation).

---

## v2.2.0 — Heterogeneous Edge Intelligence

Crowning of the engineering phase. Two-tier edge cluster where TinyML is **not** a simple STA/LTA replacement, but a hierarchical Decision Fusion between cheap ubiquitous sensors and intelligent confirmation gates.

> **Blocking prerequisite:** the STA/LTA parameter calibration from **R1** must be completed before drafting/training the v2.2.0 models. Calibration is urgent and runs in parallel with v1.3.

**Tier A — Ubiquitous sensors (ESP32-C3):**
- Low-cost, installable anywhere; STA/LTA + ECDSA signing, unchanged from v1.x
- Produce the **proprietary MEMS dataset** (fills the domain gap vs INGV professional seismometers)

**Tier B — Intelligent confirmation gates (ESP32-S3):**
- Hybrid quantized CNN (INT8) via ESP-DL / TensorFlow Lite Micro
- Activated **only on STA/LTA triggers** to compute the local event probability
- Emits a confidence score that confirms or discards Tier A triggers (Decision Fusion)

---

## Right-Sized Ingestion at Scale (Redis Streams + TimescaleDB) (Released)

Backend ingestion redesigned so the control plane sustains tens of thousands of sensors on a small footprint instead of degrading into a single-queue toy.

- ✅ **Redis Streams replaces the single-consumer list queue** — producers XADD to `readings:stream` (O(1) append); N worker processes drain via consumer groups (`docker compose scale worker=N`); `XAUTOCLAIM` recovers pending entries across worker restarts (at-least-once delivery); poisoned heartbeats park on the `readings:dlq` stream so they never stall the group — `backend/src/ingest.py`
- ✅ **Batched DB commits** — a stream batch (default 64) is written in one transaction instead of one commit per heartbeat
- ✅ **TimescaleDB hypertable on `readings`** — chunked on `recorded_at`; continuous aggregate `readings_minute` serves the dashboard rollups; compression + retention policies. Migration (`backend/src/timescale.py`) is idempotent and **fails closed** on plain PostGIS (dev/CI)
- ✅ **Statistics fast-path** — `/sensors/{id}/statistics` reads the continuous aggregate when present, falls back to a COUNT otherwise
- ✅ **Single TimescaleDB+PostGIS image** — `backend/docker/postgres-timescale.Dockerfile`, wired into `docker-compose.yml`
- ✅ **Real migration coverage** — dedicated CI job runs the hypertable + aggregate tests against the actual deployment image
- ✅ **Load generator** `backend/scripts/load_test.py` — N sensors at H Hz (default matches the 150-sensor CI requirement), stream or HTTP transport

> **Scale math (design target):** 150 sensors @ 1/5s ≈ 30 msg/s (trivial today); 10k sensors @ 1 Hz ≈ 2k msg/s (bounded by worker count + hypertable inserts, still 1 Postgres node). The MQTT transport already exists (firmware → broker → bridge → API); the bridge stays HTTP-proxying by design — direct MQTT→stream is the documented next step only if the broker becomes the bottleneck.

---

## #Research — Scientific Validation (SIL)

Parallel node (non-semantic). **R1 is the Foundation**: it starts immediately, in parallel with v1.3 (GNSS), and its calibration is urgent because it is the blocking prerequisite for v2.2.0 and the paper.

Software-in-the-Loop (SIL) cross-validation: no logic duplication. It uses **100% of the production C++ code** on both the firmware and the host, guaranteeing numerical equivalence for the IEEE paper.

### R1 — STA/LTA detection cross-validation via SIL (Foundation) (Completed)

> Status: **completed.** The STA/LTA core is isolated in pure C++, compiled natively in CI, and driven by the Python orchestrator with zero logic duplication.
>
> Scheduling: **completed in parallel with v1.3 (GNSS)**. The calibration of the trigger parameters is completed and unblocks v2.2.0 model drafting/training.

- [x] Isolation of the STA/LTA algorithmic core in pure C++, fully decoupled from the ESP32 hardware (no I2C/WiFi/FreeRTOS calls in the algorithmic core) — `firmware/src/DetectionCore.h`
- [x] Native host compilation of the C++ core (same source as the firmware) — `detect_cli.cpp` + CI build
- [x] Python as the **sole orchestrator**: reading the public INGV dataset (accelerograms), passing data to the C++ binary via `subprocess`, collecting trigger points and tracing ROC curves — `research/`
- [x] Metrics: Sensitivity/Recall, False-Alarm Rate, response latency — `research/metrics.py`
- [x] Calibration of the trigger parameters (`TRIGGER_RATIO`, `NOISE_FLOOR`, `HPF_ALPHA`) against ground-truth — `research/calibrate.py`; **real ground-truth download via INGV FDSN** (public API + ObsPy, CC-BY-4.0 flatfiles) — see `research/README.md`

> **Completed full R1 closure:** real ESM/INGV ground-truth validation via ObsPy and ROC curve generated.

### R2 — AI Benchmarking (this is the paper's primary novelty contribution)

- P50/P99 latency benchmark of the local async AI worker (Ollama)
- Measurement of the hallucination rate of the generated reports
- Quantification of the privacy/latency advantage vs Cloud baseline

> **Two distinct claims — do not conflate them in the paper:**
> - **Self-hosted, data-sovereign LLM.** Inference runs inside the Docker network
>   (`http://ollama:11434`), uses no third-party inference API, and telemetry never
>   leaves the deployment. *True regardless of deployment target (defensible).*
> - **Local-first resilience** is a *deployment property*, not a software property:
>   it holds only when the full alert path (local MQTT broker → bridge → AI worker)
>   runs on an on-premise host co-located with the community. **Today the alert path
>   uses HiveMQ Cloud, so the alert path still depends on the WAN.** Claim this only
>   for the on-premise topology.
>
> **Determinism is a hypothesis, not a guarantee:** `temperature=0`, `top_k=1`
> (greedy decoding) remove *stochastic variance*, but the model can be
> *deterministically wrong*. The hallucination rate must be **measured empirically**
> in this benchmark before any quantitative claim is reported.

---

### R3 — Dissemination & Output

> R1 + R2 converge here: results are published as artifacts separate from the software.

- [ ] Publish open validation dataset (Zenodo DOI, separate from software)
- [ ] Draft technical paper / preprint (arXiv)

> **Open data strategy & license gate:**
> - Publish the **derived ESM parametric dataset** (CC-BY-4.0) as a re-distributable
>   Zenodo artifact with its own DOI, separate from the software.
> - **License re-verification step before publishing ANY derived data:** re-check the
>   current ITACA/ESM license terms and update `CITATION.cff` at release time (ITACA is
>   CC-BY-NC-ND-4.0 and forbids redistribution of derived waveforms).

---

## Future Horizon — Cloud Infrastructure & Real-Time Auto-Scaling

Production-grade cloud platform behind the alert pipeline: the MQTT/REST/AI stack of v1.x–v2.2 runs as containerized workloads on Kubernetes, fully provisioned as **Infrastructure-as-Code** with Terraform. The control plane elastically scales with the number of deployed sensors and with real-time alert bursts.

> Post-research horizon (after v2.2.0 / paper). Not blocking for the thesis; it targets the operational release of the system.

**Infrastructure-as-Code (Terraform):**
- Declarative provisioning of the cloud provider resources (managed Kubernetes cluster, VPC, node pools, networking) in versioned modules
- State management and drift detection for reproducible, auditable deployments

**Orchestration (Kubernetes):**
- Containerized deployment of the MQTT broker, AI report worker, REST control plane and dashboard
- Native autoscaling (Horizontal Pod Autoscaler / cluster autoscaler) driven by MQTT ingestion rate and CPU/memory
- Real-time elastic burst handling: alert spikes scale up workers (AI reports) and event queues; quiet periods scale to zero
- Rolling updates, health probes and self-healing for continuous availability

**Delivery & observability:**
- GitOps / CI/CD pipeline applying Terraform and Helm charts
- Monitoring and alerting for the cluster itself (resource saturation, autoscaling events)

### Performance & scaling engineering (post-paper, not needed at current scale)

- **Kafka / Redpanda as the central ingestion buffer (millions-class)** — replaces Redis Streams as the durable, replayable backbone once sustained ingestion exceeds what a single Redis node can buffer. The consumer interface (`src/ingest.py`) is deliberately transport-agnostic: `enqueue_reading` / `read_batch` / `ack` / `recover_pending` are re-pointable so a Kafka-backed implementation can slot in without touching the worker. Also unlocks partitions-per-sensor ordering and backfill reprocessing for the triangulation engine.
- **ClickHouse for cold-path analytics** — move long-range dashboards / multi-node correlation queries (epicenter triangulation, swarm clustering) off the operational Postgres node onto a columnar store with a Kafka connector. Cold reads never contend with the ingestion hot path; TimescaleDB continuous aggregates keep serving the real-time dashboard.
- **Non-blocking MQTT-Bridge refactor** — `aiomqtt` + async push to Redis (or `httpx`/`aiohttp`)
  to make the bridge relay fully non-blocking. *Partially superseded: the ingestion
  endpoint is now an O(1) stream append, so the HTTP-proxying bridge is no longer the DB
  bottleneck; direct MQTT→stream still removes the HTTP hop and is the documented next step.*
- **Rust ingestion microservice (Axum) + ECDSA verification via PyO3** — the hybrid path:
  keep FastAPI/PostGIS/Ollama, move only the CPU-bound signature verification (P-256/SHA-256)
  to native speed; a dedicated Axum ingestion endpoint can later absorb `POST /readings/`.
- **Local MQTT broker (`mosquitto`) as the default alert path** — makes the R2 "local-first
  resilience" claim real; explicitly note HiveMQ Cloud as the current WAN dependency.
- **Load-test on rented infrastructure (e.g. AWS), one-off** — not GitHub Actions (hardware
  limits); results published as static charts in the paper.

---

