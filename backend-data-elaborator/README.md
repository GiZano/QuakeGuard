# QuakeGuard Backend Service

QuakeGuard is a distributed, high-throughput backend system designed for the real-time ingestion, cryptographic validation, and processing of seismic data from IoT devices.

This repository hosts the **API Gateway**, **Background Worker**, and **Persistence Layer** definitions, serving as the core infrastructure for an Earthquake Early Warning (EEW) system.

---

## 📂 Project Structure

The project is organized as a modular microservice architecture:

```text
backend-data-elaborator/
└── api/
    ├── init-scripts/       # SQL initialization scripts (PostGIS)
    ├── src/                # Source Code
    │   ├── main.py         # FastAPI Gateway & REST Endpoints
    │   ├── worker.py       # Async Background Event Processor
    │   ├── database.py     # SQLAlchemy Connection & Pool config
    │   ├── models.py       # ORM Models (GeoAlchemy2 enabled)
    │   └── schemas.py      # Pydantic DTOs
    ├── tests/              # Testing Suite
    │   ├── __init__.py
    │   └── stress_test.py  # Load testing & ECDSA simulation tool
    ├── .venv/              # Local Python Environment
    ├── build.ps1           # Build helper script
    ├── docker-compose.yml  # Container orchestration
    ├── Dockerfile          # Python runtime environment
    └── requirements.txt    # Project dependencies
```

---

## 🏗 System Architecture

The system operates on three decoupled layers:

1.  **Ingestion Layer (FastAPI):**
    * **Role:** Acts as the secure gateway for IoT sensors.
    * **Features:**
        * Asynchronous request handling (`async/await`).
        * **Zero-Trust Security:** Enforces ECDSA (NIST256p) signature verification with SHA-256 hashing on every payload.
        * **Polyglot Crypto Support:** Handles both DER (MbedTLS/C++) and RAW (Python/JS) signature formats.
        * **Non-Blocking:** Offloads valid payloads immediately to a Redis queue (`seismic_events`).

2.  **Processing Layer (Worker):**
    * **Role:** Consumes the message queue and analyzes data streams.
    * **Features:**
        * Persists raw telemetry to PostgreSQL.
        * Implements a sliding window counter in Redis to detect seismic swarms in real-time.
        * Triggers persistent `Alerts` when predefined thresholds are breached.

3.  **Persistence Layer:**
    * **PostgreSQL + PostGIS:** Primary storage for time-series data and geospatial entities (Zones, Sensors).
    * **Redis:** In-memory data structure store used for message queuing and high-speed counters.

---

## 🚀 Installation & Setup

### Prerequisites
* **Docker** & **Docker Compose**
* **Python 3.11+** (Optional, for local testing)

### 1. Environment Configuration
The system relies on environment variables. Ensure your `.env` or Docker configuration includes:

```env
DATABASE_URL=postgresql://developer:development_pass@db:5432/monitoraggio_db
REDIS_URL=redis://redis:6379/0
```

### 2. Build and Deployment
Navigate to the `api` directory and launch the stack:

```bash
cd api
docker-compose up -d --build
```

The API will be accessible at: `http://localhost:8000`

### 3. API Documentation
Interactive Swagger UI is available at:
`http://localhost:8000/docs`

---

## 📡 API Endpoints Overview

### 🛠️ Registration (Admin & Setup)
Endpoints for provisioning the infrastructure.

* **POST** `/zones/` - Create a new monitoring zone.
* **POST** `/misurators/` - Register a new sensor.
    * *Note:* Requires the sensor's ECDSA Public Key (Hex format).
* **GET** `/zones/` - Retrieve available zones.
* **GET** `/misurators/` - Retrieve registered sensors.

### 📥 Data Ingestion (IoT)
* **POST** `/misurations/` - High-frequency ingestion endpoint.
    * **Payload:** Telemetry data including `value`, `device_timestamp`, and `signature_hex`.
    * **Security:** Rejects any payload with an invalid or missing digital signature.

### 📊 Data Retrieval & Analytics
* **GET** `/zones/{zone_id}/alerts` - Retrieve confirmed seismic alerts for a specific area.
* **GET** `/sensors/{misurator_id}/statistics` - Get aggregated metrics (Count, Avg, Max, Min) for sensor diagnostics.

### 🟢 System
* **GET** `/health` - Detailed status check of API, Database, and Redis connectivity.

---

## ⚙️ Technical Specifications

### Cryptography & Security
The backend enforces strict cryptographic standards to prevent spoofing or replay attacks:
* **Algorithm:** ECDSA (Elliptic Curve Digital Signature Algorithm).
* **Curve:** NIST P-256 (secp256r1).
* **Hash Function:** SHA-256.
* **Format:** Accepts **DER encoded** signatures (standard for ESP32/MbedTLS) with a fallback to RAW formats.

### High-Concurrency Configuration
To handle bursts of traffic during seismic events, the database engine is optimized:
* **Pool Size:** 40 persistent connections.
* **Max Overflow:** 60 additional temporary connections (Total capacity: 100 concurrent threads).
* **Pre-Ping:** Enabled to prevent stale connection errors.

---

## 🧪 Stress Testing

A specialized load testing script is located in `tests/stress_test.py`. It simulates a fleet of 100 concurrent sensors generating cryptographically valid payloads.

**To run the test:**

1.  Ensure the Docker stack is running.
2.  Install test dependencies:
    ```bash
    pip install aiohttp ecdsa
    ```
3.  Execute the script:
    ```bash
    python -m tests.stress_test
    ```

**Success Criteria:**
The test should report a 100% success rate (HTTP 202 Accepted) with no signature validation errors.