# ADR-0003: Hybrid Edge AI — Ollama Bare-Metal on Host

## Status
Accepted (v1.2.0)

## Context
QuakeGuard generates AI emergency reports from confirmed seismic alerts using a local LLM (Llama 3.2 1B via Ollama). The architectural decision is whether to run Ollama inside Docker alongside the other services, or bare-metal on the host OS.

Key constraints:
- The deployment target is a Linux workstation (not a cloud VM with GPU passthrough).
- Docker on Linux does not natively support GPU passthrough without `nvidia-container-toolkit` or `--gpus` flags, which adds complexity.
- Even CPU-only inference benefits from direct access to host memory and SIMD instructions.
- The AI worker is a non-critical, asynchronous service — an alert is delivered regardless of whether the AI report succeeds.

## Decision
Adopt an industrial **Hybrid Edge AI** pattern (similar to NVIDIA Jetson or Tesla FSD architectures):

- **Ollama runs bare-metal** on the host Linux OS (`curl -fsSL https://ollama.com/install.sh | sh`)
- **Application services run in Docker** as before
- The AI worker container uses `network_mode: "host"` to reach Ollama at `http://127.0.0.1:11434`
- The Ollama Docker container definition is kept in `docker-compose.yml` (commented out) for environments where Docker-native is preferred

## Consequences
- **Positive:** Maximum hardware efficiency (direct memory, no container overhead), simpler GPU passthrough if available, model persisted natively.
- **Positive:** Clear separation of concerns: the AI engine is a host-level capability, not a container sidecar.
- **Negative:** The AI worker container must use `network_mode: "host"`, losing Docker network isolation for that single service.
- **Negative:** Requires separate Ollama installation on the host (not fully containerized).

## Alternatives Considered
- **Ollama in Docker:** Fully containerized, but Docker GPU passthrough adds significant complexity on heterogeneous hardware. The commented `ollama` service block remains available for this path.
- **Cloud LLM API (OpenAI, Anthropic):** Eliminates the privacy-first claim — telemetry would leave the host. Rejected on principle.
- **TensorFlow Lite on ESP32:** Inference on the edge device itself. Reserved for v2.2.0 Tier B sensors (ESP32-S3 with quantized CNN). The ESP32-C3 lacks the memory for meaningful LLM inference.
