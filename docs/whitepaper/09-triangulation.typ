= Epicenter Triangulation Algorithm

In QuakeGuard v2.0.0, the backend actively performs multi-node spatial and temporal correlation to transform isolated sensor triggers into a cohesive, verified seismic event.

== Temporal & Spatial Correlation Engine

Before calculating the physical epicenter, the ingestion worker (`backend/src/worker.py`) groups the incoming telemetry via a distributed state machine backed by Redis:

1. *Temporal Window:* When a valid trigger arrives, its payload is appended to a Redis List specific to its geographical area, and the list's Time-To-Live (TTL) is refreshed to 60 seconds. This creates a sliding temporal buffer that captures the seismic wavefront as it propagates across multiple sensors.
2. *Quorum Consensus:* To eliminate isolated false positives (e.g., localized heavy impacts or tampering), the correlation engine requires a minimum quorum of 3 independent sensors (`llen(buffer_key) == 3`).
3. *Execution:* The moment the quorum is reached within the 60-second window, the worker flushes the payload cluster to the triangulation function to compute the unified epicenter and trigger the downstream AI reporting services.

#page(flipped: true, margin: 1cm)[
  #figure(
    image("assets/sequence-triangulation_1.svg", width: 100%, fit: "contain"),
    caption: [_Epicenter Triangulation & Correlation Sequence (Part A)_]
  )
  #figure(
    image("assets/sequence-triangulation_2.svg", width: 100%, fit: "contain"),
    caption: [_Epicenter Triangulation & Correlation Sequence (Part B)_]
  )
]

== Mathematical Model (v2.0 MVP)

The current release implements a deterministic, magnitude-weighted spatial centroid (Barycenter approximation) coupled with an empirical P-wave travel time estimator. While future iterations may introduce a non-linear Least Squares solver based purely on Time Difference of Arrival (TDOA), the current heuristic guarantees real-time computational efficiency ($O(N)$ complexity) and handles the dense topological nature of the IoT network natively.

*1. Spatial Centroid Computation*
For a given cluster of $N$ triggers (where $N >= 3$), the estimated epicenter coordinates $(hat(lambda), hat(phi))$ are computed as a weighted average of the sensor coordinates, where the weight $W_i$ is the local magnitude recorded by sensor $i$:

$ hat(lambda) = (sum_(i=1)^N lambda_i dot W_i) / (sum_(i=1)^N W_i) $
$ hat(phi) = (sum_(i=1)^N phi_i dot W_i) / (sum_(i=1)^N W_i) $

*2. Haversine Distance*
To estimate the origin time of the rupture, the backend computes the great-circle distance $d$ between the calculated epicenter $(hat(lambda), hat(phi))$ and the first triggered sensor $(lambda_0, phi_0)$ (the node recording the earliest arrival time $T_"first"$) using the Haversine formula (where $R approx 6371 " km"$):

$ a = sin^2((Delta phi) / 2) + cos(phi_1) dot cos(phi_2) dot sin^2((Delta lambda) / 2) $
$ c = 2 dot "atan2"(sqrt(a), sqrt(1-a)) $
$ d = R dot c $

*3. Origin Time Estimation*
Assuming an average crustal primary wave (P-wave) velocity of $V_P = 6.0 " km/s"$, the estimated travel time from the hypocenter to the first sensor is:

$ Delta t_"travel" = d / V_P $

The event origin time $T_0$ is then retroactively calculated by subtracting the travel time from the first absolute NTP-synchronized timestamp recorded:

$ T_0 = T_"first" - Delta t_"travel" $

== Accuracy & Future Work

This methodology yields highly accurate epicenters when the sensor density is high (e.g., city-scale deployments). However, since it relies on magnitude weights rather than pure arrival times, asymmetrical network topologies (where sensors are clustered only on one side of a fault) can pull the epicenter centroid artificially toward the cluster. The current architecture separates this core calculation into a decoupled function, ensuring a seamless upgrade path to standard TDOA multilateration in future releases without disrupting the ingestion pipeline.
