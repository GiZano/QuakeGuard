= Appendix A: OpenAPI / REST Endpoints

The QuakeGuard Control Plane exposes a REST API via FastAPI. The full OpenAPI 3.0 specification is available at the `/docs` endpoint of the backend service. Below is a summary of the core endpoints:

*Provisioning & Authentication*
- `POST /devices/register`: Enrolls a new IoT node. Requires `enrollment_token`. Returns assigned `sensor_id` and zone metadata.

*Ingestion (Data Plane Fallback)*
- `POST /readings/`: Accepts ECDSA-signed seismic payloads. Used by the MQTT bridge and USB Serial fallback.

*Alerts & Reports*
- `GET /alerts/{zone_id}`: Retrieves the latest alerts for a specific geographic zone.
- `GET /reports/{alert_id}`: Fetches the AI-generated emergency report for a confirmed alert.

*Telemetry & Analytics*
- `GET /sensors/{sensor_id}/statistics`: Returns time-series aggregates (count, max magnitude) for a specific sensor, leveraging TimescaleDB continuous aggregates.

= Appendix B: Project & Licensing Information

- *Software License:* QuakeGuard software (backend, mobile, firmware) is open-source and released under the GNU Affero General Public License v3.0 (AGPL-3.0). This ensures that any modifications or network use of the software remain freely available to the public.
- *Hardware License:* The QuakeGuard Printed Circuit Board (PCB) and related hardware designs are released under the CERN Open Hardware Licence (CERN-OHL-S).
- *Data Availability & Archival:* Stable releases of the project, including this whitepaper and the associated source code, are permanently archived on Zenodo and citable via the authoritative DOI identifier.
