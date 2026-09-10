# ADR-0001: Redis Streams as the Ingestion Transport

## Status
Accepted

## Context
QuakeGuard's original ingestion pipeline used a Redis `LPUSH`/`BRPOP` list queue with a single-consumer worker. While simple, this design has inherent scaling limitations:

- **Single consumer:** Only one worker process can drain the queue, creating a bottleneck under load.
- **No at-least-once delivery:** A crashed worker loses the popped message.
- **No message inspection:** No way to audit pending or failed messages.
- **No replay:** Once consumed, a message is gone.

As the sensor network grows beyond ~150 nodes, the single-consumer list becomes the throughput ceiling.

## Decision
Replace the Redis list queue with **Redis Streams** (`XADD`/`XREADGROUP`):

- Producers append via `XADD` to `readings:stream` (O(1)).
- Workers form a **consumer group**, enabling horizontal scaling (`docker compose scale worker=N`).
- `XAUTOCLAIM` recovers pending entries across worker restarts (at-least-once delivery).
- Poisoned messages are parked on `readings:dlq` (dead-letter queue) instead of stalling the group.
- Batched DB commits: a stream batch (default 64 messages) is written in one transaction.

## Consequences
- **Positive:** Horizontal worker scaling, at-least-once delivery, DLQ for debugging, batched writes.
- **Negative:** Slightly more complex consumer logic vs. simple `BRPOP`.
- **Neutral:** The `enqueue_reading` / `read_batch` / `ack` interface in `src/ingest.py` is transport-agnostic, so a future Kafka backend can slot in without touching the worker.

## Alternatives Considered
- **Kafka/Redpanda:** More scalable but adds an entirely new infrastructure dependency. Documented as the next step for millions-class ingestion (see ROADMAP.md "Future Horizon").
- **RabbitMQ:** Feature-rich but heavier; Redis is already in the stack.
- **Keep LPUSH/BRPOP:** Insufficient for consumer groups and recovery.
