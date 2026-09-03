= DevOps Automation & Scripting (v2.0.0)

With the release of v2.0.0, QuakeGuard introduces a "Zero-Config" orchestration pipeline designed to eliminate manual setup overhead and credential mismanagement across the distributed architecture. The `scripts/` directory provides a suite of bash tools that handle everything from dynamic cryptographic generation to multi-terminal provisioning.

== The QuakeGuard Orchestrator (`quakeguard_init.sh`)

The `quakeguard_init.sh` script serves as the master entrypoint for the local development and testing environment. When executed on a fresh clone of the repository, it automates the entire lifecycle:

1. *Environment Provisioning:* It detects if the core `.env` configurations are missing and automatically invokes `generate_secrets.sh` (see below) to populate them securely.
2. *Dynamic Tunnel Negotiation:* It invokes `tunnel_init.sh` to negotiate an ephemeral Cloudflare HTTPS tunnel, instantly injecting the resulting `https://*.trycloudflare.com` URL into both the ESP32 firmware C++ build configuration and the React Native mobile client.
3. *Multi-Process Boot:* Utilizing `ptyxis` (or `tmux`), it spawns three isolated, parallel terminal sessions:
   - *Backend:* Rebuilds and launches the Docker Compose stack (including the AI-Worker profile).
   - *Mobile:* Clears the Expo cache and starts the React Native bundler.
   - *IoT Edge:* Triggers a PlatformIO `run -t upload -t monitor` command to compile the firmware with the injected dynamic URLs and flash the attached ESP32-C3 node.

== Idempotent Secrets Sync (`generate_secrets.sh`)

To enforce the "Zero-Trust" architecture without manual pain, `generate_secrets.sh` generates and synchronizes cryptographic tokens (`ENROLLMENT_TOKEN`, `IOT_API_KEY`, `MOBILE_WS_TOKEN`).

- *Smart Generation:* It uses `openssl rand -hex 32` to generate secure 256-bit keys, substituting them into the respective `.env` files via regex.
- *Conflict Resolution:* If keys are modified manually and become desynchronized across the backend, mobile, or firmware, the script performs a Global Mismatch Check. It prompts the developer via an interactive `[b/m/f]` prompt to select the "Source of Truth," subsequently synchronizing the remaining systems to match the selected component.
- *Dependency Checks:* The script actively scans for missing manual configuration (such as the Mosquitto MQTT broker credentials) and forces a loud terminal warning to ensure the data plane is fully established before boot.

== E2E Pipeline Stress Testing

The automation suite also includes Python-based stress testers to validate the deployment's resilience:
- *`stress_test.py` (in `backend/tests/`):* Simulates the "Thundering Herd" effect by spawning 150 concurrent asynchronous sensors, blasting the API to validate the Redis sliding-window rate limiter and the `FastAPI` concurrency limits. A successful run finishes with a `🏆 SYSTEM CERTIFIED` banner.
- *`simulate_zone.py` (in `backend/scripts/`):* Streams synthetic, scaled acceleration telemetry into specific PostGIS zones to visualize live graphs on the React Native mobile app without triggering a full E2E pipeline crash.

== Testing & CI/CD Pipeline

To maintain production-grade reliability, QuakeGuard is backed by a rigorous Continuous Integration and Continuous Deployment (CI/CD) pipeline running on GitHub Actions:
- *Test Coverage:* The backend is validated by 104 `pytest` scenarios covering ECDSA cryptography, state machine transitions, and Redis streams processing. The mobile application is covered by 23 Jest tests ensuring state management and UI resilience.
- *Quality Gates:* Every pull request is automatically analyzed by SonarCloud, enforcing strict quality, reliability, and security metrics before a merge is permitted.
- *Linting & Safety:* Python code is statically analyzed and formatted using Ruff, while dependencies are audited by Safety and CodeQL to prevent supply-chain attacks.
