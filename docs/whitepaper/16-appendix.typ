= Appendix A: OpenAPI / REST Endpoints

The QuakeGuard Control Plane exposes a REST API via FastAPI. The full OpenAPI 3.0 specification is available at the `/docs` endpoint of the backend service. Below is a summary of the core endpoints:

*Provisioning & Authentication*
- `POST /devices/register`: Enrolls a new IoT node. Requires `enrollment_token`. Returns assigned `sensor_id` and zone metadata.

*Ingestion (Data Plane Fallback)*
- `POST /readings/`: Accepts ECDSA-signed seismic payloads. Used by the MQTT bridge and USB Serial fallback.

*Alerts & Reports*
- `GET /alerts/{zone_id}`: Retrieves the latest alerts for a specific geographic zone.
- `GET /reports/{alert_id}`: Fetches the AI-generated emergency report for a confirmed alert.

*Demo & Simulation*
- `POST /demo/trigger-earthquake`: Simulates a critical seismic event for testing and demonstrations. Requires API key authentication (`verify_api_key`). Bypasses the standard IoT ingestion pipeline to execute a complete mock cascade:
  1. Resolves the geographic centroid for the requested `zone_id` (defaults to Milan coordinates if geometry is missing).
  2. Publishes the event directly to the `quake_alerts` Redis channel for instant WebSocket broadcast.
  3. Creates an `Alert` record (`is_triangulated=True`) and an `EmergencyReport` in `PENDING` state.
  4. Triggers the AI Worker for text report generation by pushing to the `ai_report_queue`.
  5. Injects 5 synthetic historical sensor readings into the database to populate telemetry graphs, applying reverse-calibration (K_CALIBRATION=1.6) to derive realistic raw hardware values.
  (Payload: `zone_id`, `magnitude`, `message`; defaults to `zone_id: 1`, `magnitude: 5.0`).

*Telemetry & Analytics*
- `GET /sensors/{sensor_id}/statistics`: Returns time-series aggregates (count, max magnitude) for a specific sensor, leveraging TimescaleDB continuous aggregates.

= Appendix B: Project & Licensing Information

- *Software License:* QuakeGuard software (backend, mobile, firmware) is open-source and released under the GNU Affero General Public License v3.0 (AGPL-3.0). This ensures that any modifications or network use of the software remain freely available to the public.
- *Hardware License:* The QuakeGuard Printed Circuit Board (PCB) and related hardware designs are released under the CERN Open Hardware Licence (CERN-OHL-S).
- *Data Availability & Archival:* Stable releases of the project, including this whitepaper and the associated source code, are permanently archived on Zenodo and citable via the authoritative DOI identifier.
