= Roadmap & Future Horizons

#table(
  columns: (auto, 1fr),
  [*Version*], [*Description*],
  [v1.0.0], [Edge Seismic Detection (STA/LTA on ESP32)],
  [v1.1.0], [Cloud & Security (MQTT, HTTPS, TLS, ECDSA)],
  [v1.2.x], [On-Premise AI, Geo-Zoning, Serial Fallback],
  [v1.3.0], [Synchronized GNSS (NTP + PPS Time Discipline)],
  [v2.0.0], [Epicenter Triangulation & Hardware Assembly],
  [v2.1.0], [Grafana Observability, System Telemetry, Captive Portal Onboarding, Dynamic Demo Onboarding (QR), OTA In-App Updates, Hollywood Simulator, and Repository Health (ADRs, CI Hardening, Dependabot)],
  [v2.1.1], [Demo Calibration & Repository Fixes],
)

== Next Steps
- *v2.2.0 - Edge AI (Two-Tier Cluster):* A hierarchical Decision Fusion network where ubiquitous ESP32-C3 sensors (Tier A) act as triggers, and intelligent ESP32-S3 nodes (Tier B) run quantized INT8 CNNs via ESP-DL to confirm or discard triggers.

== Detailed v1.2.x Changelog
- *v1.2.0:* Introduced On-Premise AI Emergency Reports via a dedicated Ollama worker, isolating LLM inference to the edge host.
- *v1.2.1:* Refactored geographic tracking with Geo-Zoning and Cooldown Fragmentation (GNSS-ready), utilizing Redis geohashes and PostGIS `ST_Contains`.
- *v1.2.2:* Implemented Zero-Trust Serial Fallback (USB CDC), ensuring cryptographically-signed telemetry is persisted and retried when Wi-Fi/MQTT is unreachable.

== Future Horizon: Post-Research Cloud Infrastructure
Following the validation phase, the system targets an operational release focusing on real-time auto-scaling. The MQTT/REST/AI stack will be fully provisioned as Infrastructure-as-Code (Terraform) and orchestrated via Kubernetes. Real-time elastic burst handling will scale worker pods in response to alert spikes, while long-range analytics will be migrated to ClickHouse and Kafka for massive multi-node correlation.
