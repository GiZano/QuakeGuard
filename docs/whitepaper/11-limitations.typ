= Limitations & State of the Art Comparison

== Known Limitations
While QuakeGuard provides a robust foundation for community EEW, several limitations exist in the v2.1.0 architecture:
- *Single Point of Failure (Broker):* The system currently relies on a single Mosquitto broker container for MQTT telemetry. A catastrophic Docker engine failure breaks the data plane, though the Zero-Trust serial fallback mitigates this for deployments bridging over USB.
- *TPR Limits on Cheap Hardware:* The ADXL345 sensor has an inherently higher noise floor compared to professional episensors, capping the theoretical True Positive Rate (TPR) at ~80% when validated against the INGV SIL dataset.
- *Macro-Region Alerting:* The triangulation algorithm computes the epicenter, but alerts are still broadcasted at the macro-zone level, potentially warning users who are outside the destructive radius.

== State of the Art Comparison
QuakeGuard sits between massive government systems and smartphone-based crowdsourcing.

#table(
  columns: (1fr, 1.2fr, 1fr, 1.3fr),
  [*Feature*], [*QuakeGuard (v2.1.0)*], [*ShakeAlert*], [*MyShake / EQN*],
  [Hardware], [Dedicated Edge IoT], [Professional], [Smartphones],
  [Latency], [< 200 ms], [< 5 s], [Variable (1-10 s)],
  [Coupling Noise], [Low (Rigid mount)], [Very Low], [Variable (Filtered when stationary/charging)],
  [Cost/Citizen], [Free (Embedded)], [Paid via Taxes], [Free (BYOD)]
)

QuakeGuard offers deterministic latency and low coupling noise like ShakeAlert, but at the democratization scale of MyShake and Earthquake Network (EQN). Crucially, the direct cost for the citizen remains zero: the deployment strategy is to embed these low-cost (~\$15 USD) nodes at the corporate level directly into home appliances, smart home infrastructures, or through municipality-led deployments. The current universal PCB is designed with footprint headroom to support a future ESP32-S3 variant. While currently operating with C3 capabilities, future releases will deploy TinyML to the S3 nodes, formally splitting the hardware into a two-tier edge cluster (ubiquitous sensors vs. intelligent confirmation gates).
