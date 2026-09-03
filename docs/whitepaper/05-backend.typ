= Backend Services & Event Processing

The QuakeGuard backend is engineered to handle massive telemetry spikes (firehosing) typical of seismic swarms. To achieve this, the architecture strictly decouples data ingestion from data processing using a producer-consumer pattern mediated by Redis.

== API Gateway & Asynchronous Ingestion

The primary entry point is a FastAPI application running behind an ASGI server (Uvicorn) within a Docker container.
- *Rate Limiting:* To protect against Denial of Service (DoS) and buggy edge nodes, the ingestion endpoint (`/readings/`) utilizes a sliding-window rate limiter backed by Redis sorted sets (`ZADD`, `ZREMRANGEBYSCORE`), restricting traffic to 50 requests per second per IP.
- *Queue Offloading:* Once a payload passes the strict cryptographic validation pipeline, the API does not block to perform database writes. Instead, it immediately serializes the event and pushes it to the ingest stream via an `XADD` command, returning an HTTP `202 Accepted` to the bridge in milliseconds.

== Redis Streams Ingestion Substrate

The telemetry queue is a Redis *Stream* (default `readings:stream`), not a plain List. Lists cannot support consumer groups, so the previous single-worker `BRPOP` design bounded scale to one process and could lose a message on a crash mid-read. Streams fix both concerns:
- *Horizontal Scale:* Any number of producers `XADD` to the stream (HTTP API, MQTT bridge, ...). Any number of worker processes consume with `XREADGROUP`; Redis balances deliveries across the group, so capacity is added with `docker compose scale worker=N`.
- *At-Least-Once Delivery:* `XAUTOCLAIM` reclaims entries left pending by crashed consumers, so no message is lost across worker restarts.
- *Poisoned-Message Isolation:* Unparseable or fatally-failing messages are parked on a Dead Letter Stream (default `readings:dlq`) and acknowledged, so a poisoned heartbeat can never stall the group.
- *Right-Sized Backpressure:* The stream is capped with `MAXLEN ~200000` (approximate trimming); consumers read in batches of up to 64 messages with a 500ms block, and every batch is flushed in a single database transaction.
- *Logical Multi-Tenancy:* Every key (stream, group, DLQ, consumer prefix) is re-pointable via environment variables, so a single backend can serve multiple logical regions simply by renaming the stream.

== Background Worker & Persistence

A decoupled Python worker (`worker.py`) runs in a continuous loop, consuming the `readings:stream` via a blocking `XREADGROUP` and reclaiming stale pending entries with `XAUTOCLAIM`.
- *Database Pooling:* The worker and the API share a heavily optimized SQLAlchemy connection pool targeting a PostgreSQL database. The engine is configured with aggressive pooling parameters (`pool_size`, `max_overflow`) to handle high-concurrency load testing without queue exhaustion.
- *Batch Atomicity:* A whole stream batch is staged in-memory and persisted with a single `db.commit()`; only cooldown locks are taken per-event (atomic Redis `SET NX`). On a database error the entire batch is routed to the DLQ rather than partially applied.

== TimescaleDB Hypertable

The `readings` table is provisioned as a TimescaleDB *hypertable* partitioned on `recorded_at`, so time-series chunks stay small and pruning stays efficient even under firehosing. The provisioning module (`timescale.py`) applies the DDL best-effort and idempotently: if the connected image lacks the extension it fails closed with a warning, keeping the standard PostGIS image compatible for CI while production uses the unified TimescaleDB+PostGIS image. On newer TimescaleDB releases (2.13+/3.x) the hypertable is additionally configured for columnstore access. The `Reading` model uses a composite primary key `(id, recorded_at)` because TimescaleDB requires the partitioning column to be part of every unique key.

== Geographic Zoning & Zone-Scoped Data

PostGIS zones act as the source of truth for the network topology:
- *Zone Management:* `GET /zones` lists the monitored polygons; `POST /zones/` creates one.
- *Spatial Auto-Assignment:* On provisioning, `resolve_zone` maps a device's coordinates to the smallest containing polygon. It first consults a Redis fast-path index (`zoneindex:<geohash>` → set of zone ids, precision 3), and only on a cache miss or an ambiguous multi-zone match does it run the authoritative PostGIS `ST_Contains` query ordered by polygon area. The cache is purely an optimization and can never assign the wrong zone.
- *Zone Detection:* `GET /zones/locate?latitude=...&longitude=...` resolves an arbitrary GPS fix into its containing monitored zone (404 when outside any polygon), powering the mobile "Detect my zone" flow.
- *Zone-Scoped Retrieval:* `GET /zones/{zone_id}/readings` (live per-zone telemetry for the per-zone seismograph), `DELETE /zones/{zone_id}/readings` (operational purge), and `GET /zones/{zone_id}/alerts` (confirmed alerts raised for a single area).

== Magnitude Estimation & Per-Area Deduplication

For every processed event, the worker performs a physical magnitude estimation based on a MyShake-style MEMS calibration approach.
The raw Peak Ground Acceleration (PGA) is converted using the formula:

$ M_"IoT" = log_10("PGA"_"calib") + b $

Where $"PGA"_"calib"$ accounts for the ADXL345 scale and hardware calibration constant (`K_CALIBRATION = 1.6`, applied as division), and $b$ is an empirical offset (`B_OFFSET = 3.0`). The same normalization is shared with the mobile client so the app and the backend report identical magnitudes.

- *Thresholding:* If the estimated magnitude reaches or exceeds the critical threshold of $4.5$, the worker triggers an `Alert` entity.
- *Per-Area Cooldown:* During a real earthquake, dozens of sensors in the same region will breach the threshold simultaneously. To prevent notification spam, the worker uses a Redis atomic check-and-set operation (`SET nx=True, ex=60`) keyed by the *area* — the reading's geohash region (precision 4, ~39 x 19 km) when coordinates are present, else the zone — enforcing a strict 60-second cooldown per geographic area rather than globally. `Reading.lat/lon` are captured at ingestion precisely to enable this fragmentation and future spatial correlation.
- *Outbox Pattern:* Only the first worker process that successfully acquires the Redis lock will persist the `Alert` to PostgreSQL and publish the JSON payload to the `quake_alerts` Redis Pub/Sub channel.

#page(flipped: true, margin: 1cm)[
  #figure(
    block(height: 47%, image("assets/sequence-alert-delivery_1.png", height: 100%, fit: "contain")),
    caption: [_End-to-End Alert Delivery Sequence (Part A)_]
  )
  #figure(
    block(height: 47%, image("assets/sequence-alert-delivery_2.png", height: 100%, fit: "contain")),
    caption: [_End-to-End Alert Delivery Sequence (Part B)_]
  )
]

== System Telemetry & Grafana Observability (v2.1.0)

To ensure the physical and network infrastructure operates with absolute reliability, the backend seamlessly integrates with *Grafana* for real-time observability of the sensor fleet. This stack allows Systems Engineers to strictly distinguish between consumer-facing alarms (handled by the mobile app) and critical diagnostic telemetry.

- *Data Injection:* The edge nodes append their current ESP32 `free_heap` (monitoring for memory leaks), Wi-Fi `rssi` (monitoring radio health), GNSS `satellites` count, and a precise millisecond epoch `device_timestamp_ms` to the JSON payload without affecting the cryptographic signature.
- *End-to-End Latency Calculation:* The API Gateway calculates the `latency_ms` by subtracting the hardware epoch from its own UTC ingestion time. This generates the core Proof of Rigor metric for the EEW pipeline.
- *Zero-Config Provisioning:* The system automatically alters the TimescaleDB hypertable at startup to store these columns. The `docker-compose.yml` launches Grafana, utilizing a pre-injected `postgres.yml` datasource to connect natively to TimescaleDB, rendering time-series diagnostics instantly.