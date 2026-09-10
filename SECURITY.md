# Security Policy

## Supported Versions
QuakeGuard takes the security of its IoT early warning infrastructure very seriously. We currently provide security updates for the following versions:

| Version | Supported          | Notes |
| ------- | ------------------ | ----- |
| 2.1.x   | :white_check_mark: | Current stable release (Grafana Observability, System Telemetry, Local Mosquitto). |
| 2.0.x   | :white_check_mark: | Prior stable release (Repository Health, Hybrid Network Architecture, GNSS Precision & SIL Validation). |
| 1.3.x   | :x:                | Deprecated. (GNSS Precision & SIL Validation). |
| 1.2.x   | :x:                | Deprecated. (Cloud MQTT + TLS + on-premise AI reports). |
| 1.1.x   | :x:                | Deprecated. Cloud MQTT + TLS. |
| < 1.0   | :x:                | Pre-release prototypes. |

## Reporting a Vulnerability

**DO NOT OPEN A PUBLIC ISSUE FOR SECURITY VULNERABILITIES.**

Because QuakeGuard is designed as a critical infrastructure early warning system, public disclosure of a vulnerability (such as a bypass in the ECDSA signature verification, MQTT bridge injection, or anti-replay mechanisms) could compromise active sensor nodes.

Please report security issues directly by emailing: **gizano.dev@gmail.com**

### What to include in your report:
*   A description of the vulnerability and its impact.
*   The affected component (e.g., `backend/security.py`, ESP32 firmware, React Native client).
*   Detailed steps to reproduce the vulnerability.
*   Any proof-of-concept (PoC) code or scripts.

### Our Response Time
We will acknowledge receipt of your vulnerability report within 48 hours and strive to send you regular updates about our progress. If the vulnerability is confirmed, we will release a patch as quickly as possible and coordinate public disclosure with you.
