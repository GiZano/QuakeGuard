= Threat Model & Security Audit

QuakeGuard's architecture implements a Zero-Trust model where the network is assumed to be hostile. The security model explicitly addresses spoofing, tampering, and denial-of-service via cryptographic enforcement.

== STRIDE Threat Analysis

#table(
  columns: (auto, auto, auto, auto),
  [*Threat Type*], [*Vector*], [*Mitigation*], [*Section*],
  [Spoofing], [Attacker injects fake seismic data], [ECDSA signatures required on all telemetry], [§4.1],
  [Tampering], [MITM alters event magnitude], [Payload hash (SHA-256) checked against signature], [§4.3],
  [Repudiation], [Node denies sending a false alert], [Public key strictly bound to Sensor ID at provisioning], [§4.2],
  [Info Disclosure], [Sniffing telemetry over WAN], [Data plane encrypted via TLS 1.2 (note: `setInsecure()` disables server certificate validation — channel is encrypted but not server-authenticated)], [§5.2],
  [Denial of Service], [Volumetric flooding of the ingestion API], [Redis sliding-window rate limiter (50 req/s/IP) and connection pooling], [§6],
  [Elevation of Priv], [Node attempts to provision others], [Enrollment Token required for `/devices/register`], [§4.2]
)

== Out of Scope
The following vectors are explicitly out of scope for the current threat model:
- *Physical Compromise:* If an attacker gains physical access to the node, they could theoretically extract the private key from the ESP32's NVS or perform side-channel attacks during signing. Hardware Secure Elements (e.g., ATECC608A) are recommended for production deployments to mitigate this (currently planned for integration in roadmap phase R3).
- *Sensor Spoofing:* Physically shaking the sensor to induce a false positive. Spatial correlation (Triangulation) mitigates this at the system level.

== Key Rotation and Revocation
In v2.0.0, key rotation is performed via manual re-provisioning. If a node is compromised, its public key can be revoked from the PostgreSQL database, immediately invalidating any future payloads signed by that key. Automated over-the-air (OTA) key rotation is planned for a future release.
