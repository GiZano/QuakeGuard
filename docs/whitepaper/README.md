# QuakeGuard — Documentation Hub

This directory holds the authoritative technical documentation for QuakeGuard, authored in [Typst](https://typst.app/) and compiled into a single PDF technical report.

## Contents

| File | Covers |
|------|--------|
| `main.typ` | Document setup, cover page, table of contents (compiles all chapters) |
| `01-architecture.typ` | System architecture & high-level topology (edge / backend / client) |
| `02-hardware.typ` | ESP32-C3 edge node: DSP, STA/LTA, FreeRTOS, optional GNSS subsystem |
| `03-security.typ` | ECDSA identity, provisioning handshake, payload authentication |
| `04-broker.typ` | MQTT data plane, Eclipse Mosquitto, internal MQTT bridge |
| `05-backend.typ` | Redis Streams ingestion, worker, TimescaleDB, geo-zoning, alerts |
| `06-mobile.typ` | React Native client: per-zone seismograph, GPS zone detection, themes |
| `07-deployment.typ` | Local/development provisioning, scaling, simulation & stress testing |
| `08-ai.typ` | On-premise AI Emergency Report service (Ollama) |
| `assets/` | Logos and color palette used by the report |

## Compiling the PDF

Requires [Typst](https://typst.app/) (`typst` on PATH) and the Liberation Serif font family.

```bash
cd docs
typst compile main.typ QuakeGuard_Technical_Report_v2.0.0.pdf
```

The output PDF is a local build artifact and is intentionally **not** tracked in git.

## Editing conventions

- Chapters are plain Typst with `[cite: 1]` markers that reference the original `codebase_docs.txt` source export (see `extract.sh`).
- Keep each chapter self-contained; the build order is defined in `main.typ` via `#include`.
- When a new release changes behaviour, update the affected chapters and bump the version string in `main.typ` (cover + page header) to match.

## `extract.sh`

`extract.sh` compiles the entire QuakeGuard codebase into a single `codebase_docs.txt` file for LLM context. Run it from this directory when you need a fresh export:

```bash
cd docs
./extract.sh
```
