# Backend Data Elaborator 🧠

Welcome to the **Backend Data Elaborator** module of the **Electro-Domestic Earthquake Alarm System**.
This service is the "brain" of the operation: it receives real-time telemetry from the IoT devices, processes the data using seismic detection algorithms, and triggers alerts when necessary.

## 📂 Project Structure

The project is organized to keep the source code, configurations, and environment definitions clean and separated.

```text
backend-data-elaborator/
├── api/
│   ├── src/                # Main application source code (FastAPI/Flask)
│   ├── tests/              # Unit and Integration tests
│   ├── init-scripts/       # Database or service initialization scripts
│   ├── Dockerfile          # Docker image definition
│   ├── docker-compose.yml  # Local development orchestration
│   ├── requirements.txt    # Python dependencies
│   └── .env                # Environment variables (do not commit secrets!)
└── README.md               # This file
```

## 🚀 Tech Stack

* **Language:** Python 3.x
* **Framework:** FastAPI / Flask (adjust based on your actual implementation)
* **Containerization:** Docker & Docker Compose
* **CI/CD:** GitHub Actions (Automated build & push to GHCR)

---

## 🛠️ Getting Started

You can run this service either using Docker (Recommended 🐳) or manually with a Python virtual environment.

### Prerequisites

* **Docker** and **Docker Compose** installed.
* **Python 3.10+** (only for manual execution).

### Option 1: Run with Docker (The "Chill" Way)

This is the preferred method as it ensures the environment is identical to production.

1.  Navigate to the `api` directory:
    ```bash
    cd api
    ```

2.  Create your environment file (if missing):
    ```bash
    cp .env.example .env
    # Edit .env with your specific configuration
    ```

3.  Build and start the container:
    ```bash
    docker-compose up --build
    ```

The service should now be running (usually on `http://localhost:8000` or similar, check your compose config).

### Option 2: Manual Execution

If you need to debug locally without Docker:

1.  Navigate to the `api` directory:
    ```bash
    cd api
    ```

2.  Create and activate a virtual environment:
    ```bash
    python -m venv .venv
    # Windows
    .\.venv\Scripts\activate
    # Linux/Mac
    source .venv/bin/activate
    ```

3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4.  Run the application (example for generic app):
    ```bash
    # Command depends on your framework, e.g.:
    uvicorn src.main:app --reload
    # OR
    python src/main.py
    ```

---

## 🧪 Testing

We believe in code quality. Here is how to run the test suite.

**Using Docker:**
```bash
docker-compose run backend pytest
```

**Manual:**
```bash
pytest tests/
```

## 🐳 Deployment

This repository uses **GitHub Actions** for CI/CD.
Every push to the `main` branch (involving this folder) triggers a workflow that:
1.  Builds the Docker image using the context `./backend-data-elaborator/api`.
2.  Pushes the image to **GitHub Container Registry (GHCR)**.

## 🤝 Contribution

1.  Create a feature branch from `main`.
2.  Ensure your code follows the project's style guide.
3.  Write tests for new features.
4.  Open a Pull Request.
