<div align="center">

# 🌋 QuakeGuard
### Distributed Earthquake Early Warning System

**Full-Stack IoT Architecture for Real-Time Earthquake Detection**

![Version](https://img.shields.io/github/v/tag/GiZano/QuakeGuard?style=for-the-badge&color=red)
![License](https://img.shields.io/badge/License-AGPL--3.0-blue?style=for-the-badge)
![C++](https://img.shields.io/badge/C++-Hardware_Logic-00599C?style=for-the-badge&logo=c%2B%2B&logoColor=white)
![Python](https://img.shields.io/badge/Python-FastAPI-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![React Native](https://img.shields.io/badge/React_Native-Mobile-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-PostGIS-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-Message_Broker-DC382D?style=for-the-badge&logo=redis&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Containerization-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Local AI](https://img.shields.io/badge/Local_AI-Ollama_%7C_Llama_3.2-000000?style=for-the-badge&logo=meta&logoColor=white)
![HiveMQ](https://img.shields.io/badge/HiveMQ-Cloud_MQTT-FFC107?style=for-the-badge&logo=mqtt&logoColor=black)
![Cloudflare](https://img.shields.io/badge/Cloudflare-HTTP2_Tunnel-F38020?style=for-the-badge&logo=cloudflare&logoColor=white)

![CI Backend](https://github.com/GiZano/QuakeGuard/actions/workflows/backend-ci.yml/badge.svg)
![CI Frontend](https://github.com/GiZano/QuakeGuard/actions/workflows/frontend-ci.yml/badge.svg)
![CI IoT](https://github.com/GiZano/QuakeGuard/actions/workflows/iot-ci.yml/badge.svg)

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21710405.svg)](https://doi.org/10.5281/zenodo.21710405)

[![Security Rating](https://sonarcloud.io/api/project_badges/measure?project=GiZano_QuakeGuard&metric=security_rating)](https://sonarcloud.io/summary/new_code?id=GiZano_QuakeGuard)
[![Reliability Rating](https://sonarcloud.io/api/project_badges/measure?project=GiZano_QuakeGuard&metric=reliability_rating)](https://sonarcloud.io/summary/new_code?id=GiZano_QuakeGuard)
[![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=GiZano_QuakeGuard&metric=sqale_rating)](https://sonarcloud.io/summary/new_code?id=GiZano_QuakeGuard)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=GiZano_QuakeGuard&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=GiZano_QuakeGuard)

[![Bugs](https://sonarcloud.io/api/project_badges/measure?project=GiZano_QuakeGuard&metric=bugs)](https://sonarcloud.io/summary/new_code?id=GiZano_QuakeGuard)
[![Code Smells](https://sonarcloud.io/api/project_badges/measure?project=GiZano_QuakeGuard&metric=code_smells)](https://sonarcloud.io/summary/new_code?id=GiZano_QuakeGuard)
[![Duplicated Lines (%)](https://sonarcloud.io/api/project_badges/measure?project=GiZano_QuakeGuard&metric=duplicated_lines_density)](https://sonarcloud.io/summary/new_code?id=GiZano_QuakeGuard)

![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen?style=for-the-badge)

> 📚 **Technical Specification:** A comprehensive architecture whitepaper is available in the `docs/` directory, compiled via Typst. For a browsable, topic-by-topic reference, check out the [project Wiki](https://github.com/GiZano/QuakeGuard/wiki).

![QuakeGuard Logo](docs/web/assets/quakeguard/github-banner.png)


</div>

---

🌐 **[Landing Page](https://giovanni-zanotti.is-a.dev/projects/quakeguard.html)** · 📚 **[Wiki](https://github.com/GiZano/QuakeGuard/wiki)** · 📄 **[Whitepaper (PDF)](docs/whitepaper/)** · 🗺️ **[ROADMAP](ROADMAP.md)**

---

## 📖 Overview

**QuakeGuard** is a full-stack IoT architecture for real-time detection, analysis, and reporting of seismic events. The system transforms everyday household appliances — washing machines, TVs, refrigerators — into a distributed seismic sensor network, each node capable of detecting and reporting earthquake activity autonomously.

Intelligent edge sensors (ESP32-C3 + ADXL345) analyze vibrations locally using professional-grade algorithms and transmit cryptographically signed data to an asynchronous cloud backend. The backend is engineesred to handle the massive traffic spikes — the **Thundering Herd** effect — typical during widespread seismic events, ensuring reliable alarm delivery without bottlenecking. A React Native mobile app receives real-time haptic and visual alerts via WebSocket.

### QuakeGuard Proprietary Hardware

<img align=center src="docs/whitepaper/assets/pcb_assembled.jpg" width="600" alt="QuakeGuard v2.0 Assembled PCB" />

*The QuakeGuard v2.0 fully assembled PCB, featuring the ESP32-C3 SuperMini, the ADXL345 accelerometer, and the u-blox GNSS module. For a complete list of required components, refer to the [Bill of Materials (BOM)](https://github.com/GiZano/QuakeGuard/wiki/Bill-of-Materials) in the Wiki.*

---

## 🏗️ System Architecture

```
ESP32-C3 + ADXL345
       │
       │  MQTT (signed payload)
       ▼
MQTT Bridge ──► POST /readings/ ──► ECDSA Verification
                                              │
                                              ▼
                                        Redis Queue
                                              │
                                              ▼
                                     Background Worker ────►┌───────────┐
                                      │           │ (Queue)  │ AI Worker │
                                      ▼           ▼          │ (Ollama)  │
                               PostgreSQL    Redis Pub/Sub ◄─└─────┬─────┘
                               + PostGIS               │
                                                   ▼
                                            WebSocket Broadcast
                                                  │
                                                  ▼
                                        React Native Mobile App
                                        (Haptic + Visual Alert)
```

The project follows **Microservices** and **Event-Driven Design** principles across three fully independent layers.

---

## 📡 IoT Edge (`firmware/`)

| Feature | Detail |
|---------|--------|
| Hardware | ESP32-C3 SuperMini + ADXL345 Accelerometer |
| Sampling Rate | 100 Hz |
| Detection Algorithm | STA/LTA (Short Term / Long Term Average) |
| Signal Processing | Digital High-Pass Filter (HPF) to remove gravity |
| Data Structure | Statically allocated Ring Buffers (`RingBuffer<100>` STA, `RingBuffer<1000>` LTA) |
| Security | ECDSA NIST256p cryptographic signing on every payload |
| Transmission | MQTT publish to `quakeguard/telemetry` |
| Provisioning | Automated device handshake on first boot via `POST /devices/register` |
| Secret Injection | Compile-time `ENROLLMENT_TOKEN` via PlatformIO pre-script + `#error` fail-fast |

---

## ☁️ Backend (`backend/`)

| Feature | Detail |
|---------|--------|
| Framework | FastAPI (Python 3.11), fully async |
| Security | API Key auth, ECDSA signature verification, Anti-Replay (300s window) |
| Message Broker | Redis — decouples ingestion from processing |
| Rate Limiting | Fixed-window 50 req/s per IP via Redis |
| Alert Engine | ML-like magnitude proxy (`M = log10(PGA_calib) + b`), threshold M ≥ 4.5 |
| Deduplication | Redis TTL cooldown lock per zone (60s), prevents alert storms |
| Persistence | PostgreSQL + PostGIS with `recorded_at` timestamps |
| Zone Assignment | Automatic via PostGIS `ST_Contains` spatial query, ordered by `ST_Area` ascending |
| Zone Seeding | 8 pre-populated global macro-regions + "Unknown Region" fallback |
| Observability | `GET /health` — concurrent PostgreSQL + Redis ping |
| Secrets | Fail-fast `RuntimeError` on missing env vars at startup |
| MQTT Bridge | `mqtt_subscriber.py` — forwards MQTT payloads to the secure HTTP pipeline |
| Edge AI | Asynchronous emergency report generation via local Ollama (Llama 3.2) |

---

## 📱 Frontend (`mobile/`)

| Feature | Detail |
|---------|--------|
| Framework | React Native (Expo) with TypeScript |
| Navigation | Expo Router — 3-tab Bottom Navigator (Monitor, Sensors Map, Settings) |
| State Management | Zustand slices (`usePreferencesStore`, `useAlertStore`) |
| Server State | TanStack Query + Axios — caching, background refetch, retry |
| Real-Time | WebSocket context with exponential backoff reconnection |
| Alert Delivery | SOS haptic vibration pattern + OS push notification via `expo-notifications` |
| Alert History | In-session feed of last 10 critical events |
| AI Report Banner | Inline AI-generated emergency report (summary + recommendations) for the latest alert, with "Report unavailable" badge on failures |
| Offline Mode | Toggle silences WebSocket, halts all TanStack Query polling |
| Notifications | `notificationsEnabled` toggle gates haptics and push notifications |
| Safe Areas | `react-native-safe-area-context` — Dynamic Island and punch-hole compatible |

---

## 🔐 Security Model

Data integrity is paramount in an emergency system. Every telemetry packet is cryptographically secured end-to-end.

```
ESP32 signs payload with ECDSA NIST256p (SHA256)
         ↓
Backend verifies signature against registered public key
         ↓
Timestamp validated within 300-second window (Anti-Replay)
         ↓
API Key checked on every request (X-API-Key header)
         ↓
Payload accepted → Redis Queue
```

**Threat model coverage:**
- ✅ Man-in-the-Middle (MitM) — ECDSA signature verification
- ✅ Spoofing — public key registration + signature check
- ✅ Replay attacks — 300-second timestamp window
- ✅ Brute force — rate limiting 50 req/s per IP
- ✅ Unauthorized access — API Key + enrollment token fail-fast

---

## 🚀 Quick Start

### Prerequisites

- Docker Desktop & Docker Compose
- PlatformIO (VS Code Extension)
- Node.js 18+ & Expo Go (mobile)
- A mobile hotspot or shared WiFi network for ESP32 + backend connectivity

### 1. Configure Environment Variables

```bash
cd backend
cp .env.example .env
```

Edit `.env` and set the required secrets:

```env
# --- Application Secrets ---
IOT_API_KEY=your_secret_key
MOBILE_WS_TOKEN=your_ws_token
ENROLLMENT_TOKEN=your_enrollment_token

# --- Database ---
POSTGRES_DB=quakeguard_db
POSTGRES_USER=developer
POSTGRES_PASSWORD=your_db_password
API_PORT=8000

# --- Cloud MQTT (HiveMQ) ---
MQTT_BROKER=your-cluster-id.s1.eu.hivemq.cloud
MQTT_PORT=8883
MQTT_USERNAME=your_mqtt_username
MQTT_PASSWORD=your_mqtt_password

# --- AI Emergency Reports (hybrid Edge AI architecture) ---
AI_REPORT_ENABLED=true
OLLAMA_HOST=http://127.0.0.1:11434
OLLAMA_MODEL=llama3.2:1b
```

> ⚠️ The backend will refuse to start if any of these are missing — this is intentional fail-fast behavior.

> 💡 **Edge AI Architecture (v2.0.0):** To maximize hardware efficiency and avoid Docker's GPU passthrough overhead, QuakeGuard employs an industrial **Hybrid Edge AI** pattern (similar to NVIDIA Jetson or Tesla FSD architectures). The core AI inference engine (Ollama) runs bare-metal on the host Linux OS, while the application microservices run in Docker and communicate via `network_mode: "host"`.
> 
> **To enable on-premise AI reports:**
> 1. Install Ollama natively on your Linux host: `curl -fsSL https://ollama.com/install.sh | sh`
> 2. Pull the model natively: `ollama pull llama3.2:1b`
> 3. Start the Docker stack with the AI worker profile: `docker compose --profile ai up --build -d`
> 
> Reports are generated entirely on your machine: telemetry never leaves the host.

### 2. Launch the Backend Stack

```bash
cd backend
docker compose up --build -d
```

| Endpoint | URL |
|----------|-----|
| API | `http://localhost:8000` |
| Swagger UI | `http://localhost:8000/docs` |
| Health Check | `http://localhost:8000/health` |

### 3. Configure and Flash the IoT Firmware

```bash
cd firmware
cp esp32_config.env.example esp32_config.env
# Edit esp32_config.env with your network IP and ENROLLMENT_TOKEN
```

Flash via PlatformIO. On first boot the device will:
1. Open a WiFi captive portal (`QuakeGuard-Setup`)
2. Connect to your network
3. Automatically register with the backend and receive a `sensor_id`

> 💡 If the sensor registers with `latitude=0.0, longitude=0.0` it will be assigned to "Unknown Region". Hardcode your coordinates in `main.cpp` for correct zone assignment until GPS integration is complete.

### 4. Launch the Mobile App

```bash
cd mobile
npm install
```

Update `constants/config.ts` with your machine's local IP:

```typescript
export const API_BASE_URL = "http://YOUR_LOCAL_IP:8000";
```

Create `.env` in the mobile root:

```env
EXPO_PUBLIC_IOT_API_KEY=your_secret_key
EXPO_PUBLIC_MOBILE_WS_TOKEN=your_ws_token
```

```bash
npx expo start
```

Scan the QR code with Expo Go. Ensure your phone is on the **same WiFi network** as the backend machine.

---

## 🧪 Stress Test

Validates the full pipeline: ingestion → Redis → worker → PostGIS → WebSocket alerts.

```bash
cd backend
export API_URL="http://localhost:8000"
export NUM_SENSORS=150
export CONCURRENCY_LIMIT=50
python -m tests.stress_test
```

**Three phases:**

| Phase | What it tests |
|-------|--------------|
| 🔥 Phase 1 — Firehose | 150 concurrent sensors, rate limiter validation |
| ⚔️ Phase 2 — Security | Bad signature blocked (401), Replay attack blocked (403) |
| 🔍 Phase 3 — E2E | DB persistence verified via polling `GET /sensors/{id}/statistics` |

A successful run ends with `🏆 SYSTEM CERTIFIED`.

---

## 🎮 Demo Mode

Trigger a simulated earthquake instantly from Swagger UI without running the stress test:

```
POST /demo/trigger-earthquake
```

Default payload (works with empty `{}`):
```json
{
  "zone_id": 1,
  "magnitude": 7.5,
  "message": "Simulated Critical Event"
}
```

This publishes directly to the Redis `quake_alerts` channel, bypassing the IoT pipeline entirely and triggering the mobile app alert UI within milliseconds.

---

## 🗺️ Geographic Zones

The database is pre-seeded with 8 global macro-regions. Sensors are automatically assigned to the correct zone via PostGIS spatial query at registration time.

| Zone | Coverage |
|------|----------|
| Italy - North | Lombardy, Veneto, Piedmont |
| Italy - Center | Tuscany, Lazio, Umbria |
| Italy - South & Islands | Campania, Sicily, Sardinia |
| Western Europe | France, Spain, Germany, UK |
| North America | USA, Canada, Mexico |
| South America | Brazil, Argentina, Chile |
| East Asia | China, Japan, India |
| Unknown Region | Fallback for unmapped coordinates |

---

## 🔄 CI/CD Pipeline

| Workflow | Trigger | Checks |
|----------|---------|--------|
| `backend-ci.yml` | `backend/**` | Bandit, Safety, stress test |
| `frontend-ci.yml` | `mobile/**` | ESLint, npm audit |
| `iot-ci.yml` | `firmware/**` | PlatformIO compilation |
| `pr-lint.yml` | All PRs | Semantic PR title (`type(scope): message`) |
| `devops-ci.yml` | `.github/workflows/**` | Actionlint workflow validation |

---

## 🗂️ Project Structure

```
QuakeGuard/
├── backend/
│   ├── src/
│   │   ├── main.py              # FastAPI gateway + REST endpoints
│   │   ├── security.py          # ECDSA, API Key, Anti-Replay
│   │   ├── worker.py            # Redis consumer + magnitude + alert engine + AI enqueue
│   │   ├── ai_report_worker.py  # Dedicated AI report consumer (Ollama + state machine)
│   │   ├── ollama_client.py     # Deterministic LLM client (anti-hallucination)
│   │   ├── mqtt_subscriber.py   # MQTT to HTTP bridge
│   │   ├── seed.py              # Geographic zone seeder
│   │   ├── models.py            # SQLAlchemy ORM models (+ EmergencyReport)
│   │   ├── schemas.py           # Pydantic request/response schemas
│   │   └── database.py          # DB engine and session factory
│   ├── tests/
│   │   ├── stress_test.py       # Critical E2E stress test suite
│   │   └── unit/                # Unit tests (worker, ollama client, AI worker, models, ...)
│   ├── init-scripts/
│   │   └── ollama-entrypoint.sh # Auto-pulls the Ollama model on startup
│   ├── build.ps1                # Automatic container publish
│   ├── docker-compose.yml
│   ├── Dockerfile
│   ├── mosquitto.conf
│   ├── requirements.txt         # Python requirements for backend development
│   └── .env.example
├── mobile/
│   ├── app/                         # Expo Router screens
│   │   └── (tabs)/
│   │       ├── index.tsx            # Monitor / Dashboard
│   │       ├── map.tsx              # Sensor Network Map
│   │       └── settings.tsx         # User Preferences
│   ├── api/                         # Axios client + TanStack Query hooks
│   ├── components/                  # Shared UI components
│   ├── store/                       # Zustand state slices
│   ├── context/
│   │   └── WebSocketContext.tsx     # Real-time alert context
│   └── constants/
│       └── config.ts                # Centralized configuration
├── firmware/
│   ├── src/
│   │   ├── main.cpp             # FreeRTOS tasks, STA/LTA, MQTT, provisioning
│   │   ├── DetectionCore.h      # Pure-C++ STA/LTA core (shared firmware/host, R1)
│   │   └── RingBuffer.h         # Statically allocated circular buffer
│   ├── tools/
│   │   └── detect_cli.cpp       # Native host CLI (SIL replay, same core)
│   ├── test/                    # Test scripts to insert into the ESP32
│   ├── key-generator/           # ECDSA key generator for backend testing
│   ├── esp32_config.env.example
│   ├── extra_script.py          # ENV variables injector
│   └── platformio.ini
├── research/                    # SIL validation (ROADMAP R1)
│   ├── fetch_itaca.py           # ITACA download (graceful degradation) / synthetic fallback
│   ├── synthetic.py             # Realistic synthetic dataset generator
│   ├── calibrate_io.py          # Dataset layout I/O + path-injection guard
│   ├── orchestrator.py          # Compile & run the host C++ CLI (subprocess bridge)
│   ├── metrics.py               # Sensitivity, False-Alarm Rate, latency, ROC
│   ├── calibrate.py             # TRIGGER_RATIO x NOISE_FLOOR sweep (F1 maximization)
│   ├── plot_roc.py              # ROC curve figure for the paper
│   ├── requirements.txt         # matplotlib (optional, plotting)
│   └── README.md                # Dataset layout, unit conversion, licensing policy
└── docs/                            # Technical Documentation
    ├── main.typ                     # Typst Whitepaper Entrypoint
    ├── 01-architecture.typ          # System Architecture & Overview
    ├── 02-hardware.typ              # Hardware & Edge Computing (ESP32-C3)
    ├── 03-security.typ              # Cryptographic Security & Provisioning
    ├── 04-broker.typ                # Data Plane & Message Broker (MQTT)
    ├── 05-backend.typ               # Backend Services & Event Processing
    ├── 06-mobile.typ                # Mobile Client & Live Telemetry
    ├── 07-deployment.typ            # Deployment & CI/CD
    └── 08-ai.typ                    # AI Emergency Report Service (v1.2.0)
```

---

## 🔮 Roadmap

| Version | Focus |
|---------|-------|
| **v1.0** | ✅ Released — edge seismic detection on ESP32, local alerts |
| **v1.1** | ✅ Released — HiveMQ Cloud MQTT (TLS), ngrok HTTPS tunnel, security hardening |
| **v1.2** | ✅ Released — On-Premise AI Worker (Local Ollama / Llama 3.2) for privacy-preserving emergency reports |
| **v1.2.1** | ✅ Released — Geo-Zoning & Cooldown Fragmentation — geohash Redis zone index (FastAPI/PostGIS source of truth), per-area cooldown, GNSS-ready data model (`Sensor.last_fix_at`, `Reading.lat/lon`), per-zone live seismograph |
| **v1.2.2** | ✅ Released — Zero-Trust Serial Fallback — signed telemetry over USB CDC (serial) when MQTT is unreachable |
| **v2.0.0** | ✅ Released — Triangulation (multi-node spatial correlation), Hybrid Network Architecture, Automated DevOps Orchestration (Ptyxis), Local Factory Provisioning, GNSS sync, NTP+PPS, ADXL calibration, and INGV FDSN SIL validation |
| **v2.0.1** | ✅ Released — Documentation & Zenodo Sync: PDF/Wiki architectural coherence (Cloudflare, 300s anti-replay), CERN-OHL hardware licensing, SIL vs Firmware threshold clarification, and `CITATION.cff` bump |
| **v2.1.0** | ✅ Released — System Telemetry & Grafana Observability, Local Mosquitto architecture, Repository Health: Dependabot, ADRs, C4/sequence diagrams, multi-stage Dockerfile, firmware versioning, pinout, flashing guide, hardware compliance |
| **v2.1.1** | Timeseries DB & Mobile Fix — migration to TimescaleDB/InfluxDB; per-sensor chart isolation in React Native mobile |
| **v2.2** | Heterogeneous Edge Intelligence — hybrid Tier A (STA/LTA) + Tier B (quantized CNN) decision fusion |
| **Future** | Cloud IaC — Kubernetes + Terraform auto-scaling platform (see [ROADMAP.md](ROADMAP.md)) |

### #Research — Scientific Validation (SIL)

| Node | Focus |
|------|-------|
| **#Research** | Parallel ongoing node — SIL cross-validation: replay of the exact production C++ STA/LTA core (`DetectionCore.h`) on the host via the same C++ source, Python-only as orchestrator, ROC metrics + AI benchmarking (latency P50/P99, hallucination rate). R1 pipeline (core isolation, host CLI, orchestrator, metrics, calibration) implemented; see [ROADMAP.md](ROADMAP.md) |

---

## 🏆 Awards & Recognition

QuakeGuard's architecture and real-world applicability have been recognized in the following academic and industrial contexts:

* 🥇 **1st Place Overall - Institute Project Day (2025):** Awarded best technical project out of ~20 prototypes across four engineering disciplines (Computer Science, Automation, Mechanics, Chemistry). The full-stack architecture was evaluated and awarded by an industrial jury featuring technical representatives from **Siemens, ABB, SORINT.lab, SAME, Ferrero, and Confindustria**.
* 🎓 **Academic Origin & Consultation:** The system's conceptualization originated during the 2025 CQIIA-MatNet Summer School (Università di Bergamo). The distributed network logic and spatial deployment strategy were subsequently refined following technical consultations with Prof. F. Finazzi.
* 🏅 **GF Marilli Competition:** [Currently competing - Pending evaluation].

---

## 📄 License

This project is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)**.
See the [LICENSE](LICENSE) file for details.

Hardware designs (`hardware/`) are licensed under the **CERN Open Hardware Licence v2 — Strongly Reciprocal (CERN-OHL-S-2.0)**.
See [hardware/LICENSE](hardware/LICENSE) for details.

> ⚠️ **Hardware Compliance:** The QuakeGuard PCB is **not certified for CE/FCC/RoHS**. It is intended for **prototyping, educational, and research use only**. Do not deploy as a commercial safety-critical device without appropriate regulatory certification.

---

<div align="center">

**Developed by [GiZano](https://giovanni-zanotti.is-a.dev) and [riccardo0731](https://riccardo0731.github.io)**
<br>
*Open Source — AGPL-3.0 License*
<br><br>

</div>