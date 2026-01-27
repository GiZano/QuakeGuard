# Backend - Data Elaborator 🧠

This is the core API for the EDEAS system. It manages the database, validates incoming IoT data via cryptography, and serves the frontend application.

## 🛠 Tech Stack
* **Language:** Python 3.11
* **Framework:** FastAPI
* **Database:** PostgreSQL 15 + PostGIS (Spatial Extensions)
* **ORM:** SQLAlchemy + GeoAlchemy2
* **Security:** Python-ECDSA (NIST256p)
* **Containerization:** Docker & Docker Compose

## ⚙️ Configuration

1.  Create a `.env` file in this directory based on the following template:

    ```ini
    # Database Credentials
    POSTGRES_USER=developer
    POSTGRES_PASSWORD=password
    POSTGRES_DB=monitoraggio_db

    # Connection String (Ensure host is 'postgres' for Docker networking)
    DATABASE_URL=postgresql://developer:password@postgres:5432/monitoraggio_db
    ```

2.  Ensure the `init-scripts/` folder contains the SQL script to enable PostGIS.

## 🐳 Running the Server

Run the application using Docker Compose:

```bash
# Build and Start
docker-compose up -d --build

# View Logs
docker-compose logs -f
```

### Endpoints
* **Swagger Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
* **pgAdmin (DB Interface):** [http://localhost:8080](http://localhost:8080) (User: `admin@example.com`, Pass: `admin`)

## ⚠️ Troubleshooting
* **"Type geometry does not exist":**
    If the database was created before PostGIS was enabled, run:
    ```bash
    docker-compose exec postgres psql -U developer -d monitoraggio_db -c "CREATE EXTENSION IF NOT EXISTS postgis;"
    ```