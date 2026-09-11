= AI Emergency Report Service

With the release of v1.2.0, QuakeGuard introduces an on-premise AI layer that automatically generates human-readable emergency reports from confirmed seismic alerts. The service is powered by a locally hosted Large Language Model (LLM) via Ollama, guaranteeing that raw telemetry — including zone coordinates and magnitude estimates — never leaves the host machine.

== Privacy-First Local Inference

The AI pipeline is strictly self-contained and requires no external API keys or cloud LLM endpoints.

- *Local Ollama Service:* A dedicated `ollama` Docker container exposes the native Ollama API (`/api/generate`) on an internal Docker network. On first startup the entrypoint script (`init-scripts/ollama-entrypoint.sh`) automatically pulls the configured model (`OLLAMA_MODEL`, default `llama3.2:1b`) before the service becomes healthy.
- *On-Premise Isolation:* Because the model runs inside the Compose network, every telemetry attribute used to compose a report stays within the host's Docker bridge network. No third-party receives the data.
- *Model Selection:* The default 1B-parameter model is intentionally small to keep CPU and RAM footprints low while remaining fast enough to generate a report in near real-time. Operators may override `OLLAMA_MODEL` (e.g., `qwen2.5:1.5b`) for higher quality output.

== Deterministic Report Generation

Emergency messaging must never fabricate data. The AI client (`ollama_client.py`) therefore constrains the model with hard guarantees:

- *Sampling:* Every request is issued with `temperature: 0.0` and `top_k: 1` (greedy decoding), eliminating stochastic drift between retries.
- *Streaming Disabled:* Reports are generated in a single non-streaming inference pass, simplifying parsing and validation on the backend.
- *Strict System Prompt:* The model is instructed: _"You are an emergency response AI. Only use the provided JSON telemetry. Do not invent data."_
- *Telemetry Whitelist:* The prompt is built from a fixed allowlist of fields (`zone_id`, `zone_name`, `magnitude`, `timestamp`, `sensor_count`), so the model can only reason about authenticated, persisted data.
- *Failure Fallback:* If the inference request fails or returns an unparseable response, the pipeline stores an explicit `"AI report unavailable."` message rather than attempting to guess.

== Asynchronous Worker & State Machine

Report generation is fully decoupled from the alert engine via a dedicated Redis queue (`ai_report_queue`) and a separate consumer process (`ai_report_worker.py`).

- *Non-Blocking Enqueue:* When the main worker (`worker.py`) persists a confirmed `Alert`, it creates an `EmergencyReport` row in `PENDING` state and pushes the alert context to `ai_report_queue` via `lpush`. The alert pipeline is never blocked by LLM latency.
- *State Machine:* Each report transitions through a tri-state lifecycle (mapped in @fig-ai-state):

#align(center)[
  #figure(
    image("assets/fig07-ai-report-state-machine.pdf", width: 100%),
    caption: [_AI Report State Machine_],
    numbering: _ => "9.1",
    placement: top
  ) <fig-ai-state>
]

- *Dedicated Consumer:* The `ai-worker` container loops on a blocking `brpop`, fetches the telemetry context, invokes Ollama, and atomically flips the report state. On success the worker publishes an `EMERGENCY_REPORT` payload to the `ai_reports` Redis Pub/Sub channel and commits the `COMPLETED` report with its `summary` and `recommendations`.
- *Dead Letter Queue:* Unrecoverable failures (missing report, persistent inference errors) push the event to `ai_report_queue_dlq` and mark the report `FAILED`. The mobile app renders a "Report unavailable" badge for `FAILED` reports instead of showing partial or fabricated content.
- *Graceful Shutdown:* The worker traps `SIGTERM`/`SIGINT` to drain in-flight inference calls before exiting.

== WebSocket Delivery

The mobile client receives reports through the existing real-time channel.

- *Channel Subscription:* The backend WebSocket broadcaster (`main.py`) subscribes to both `quake_alerts` and `ai_reports`, delivering each `EMERGENCY_REPORT` payload over the authenticated `/ws/alerts` socket.
- *Correlation:* The payload carries the originating `alert_id`, allowing the app to attach the report to the matching alert in its history.
- *REST Fallback:* A new `GET /reports/{alert_id}` endpoint exposes the persisted report for clients that reconnect after the alert (e.g., after a WebSocket drop).
- *Inline Presentation:* The mobile app renders `COMPLETED` reports as a highlighted banner for the latest alert and as a dedicated card inside the alert history feed, showing the generated summary and per-item recommendations.

== Operational Notes

- *Compose Profile:* The `ollama` and `ai-worker` services are gated behind the `ai` profile so that the default `docker compose up` remains lightweight and CI stays hermetic. Enable the pipeline with `docker compose --profile ai up -d`.
- *Feature Flag:* The main worker only enqueues reports when `AI_REPORT_ENABLED=true` (default `false`) to avoid orphaned `PENDING` rows when the AI profile is not running.
- *Timeouts:* Inference requests honor `OLLAMA_TIMEOUT`; the Ollama service uses `KEEP_ALIVE` to reduce cold-start latency between alerts.
