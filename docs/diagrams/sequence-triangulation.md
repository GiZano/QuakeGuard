# Sequence Diagram — Multi-Node Triangulation

## a. Event Correlation

<!--
FIX (Figure 11): "diagramma che esce dalla pagina". Bumped fonts
20/18/18 -> 22/20/20 and tightened margins. Also collapsed each POST
.../readings/ message onto a single line (was wrapping via <br/>) which
trims some height. Result: 750px -> 562px tall at the same width, aspect
now ~2.79:1 — a lot of breathing room against the page.
-->
```mermaid
%%{init: {"sequence": {"actorFontSize": 22, "messageFontSize": 20, "noteFontSize": 20, "actorMargin": 55, "messageMargin": 20, "boxMargin": 6, "boxTextMargin": 4, "noteMargin": 8, "diagramMarginX": 20, "diagramMarginY": 8}}}%%
sequenceDiagram
    participant N1 as Node A<br/>(ESP32)
    participant N2 as Node B<br/>(ESP32)
    participant N3 as Node C<br/>(ESP32)
    participant API as FastAPI<br/>Gateway
    participant Redis as Redis<br/>Stream
    participant Worker as Background<br/>Worker
    participant Tri as Triangulation<br/>Engine

    Note over N1,N3: Earthquake P-wave propagates outward from epicenter

    N1->>API: POST /readings/ (t₁, lat₁, lon₁, sig₁)
    Note over N1: First node triggered (closest to epicenter)

    N2->>API: POST /readings/ (t₂, lat₂, lon₂, sig₂)
    Note over N2: Second node triggered (Δt later)

    N3->>API: POST /readings/ (t₃, lat₃, lon₃, sig₃)
    Note over N3: Third node triggered (Δt later)

    API->>Redis: XADD readings:stream (×3)

    Worker->>Redis: XREADGROUP batch
    Worker->>Worker: Detect concurrent triggers<br/>(temporal window + spatial proximity)
```

## b. Triangulation & Broadcasting

<!--
FIX (Figure 12): this was the worst offender for page overflow (1256px
tall — almost square). Same margin/font treatment as above, plus
collapsing multi-line messages ("Compute TDOA...", "Solve least-squares
minimization...") onto single lines where they were only wrapped for
source readability, not because they needed it. Result: 1256px -> 1124px
tall at the same width, aspect improved from ~1.25:1 to ~1.4:1 — much
closer to the landscape page's own aspect ratio, which is exactly what
minimizes the shrink factor Typst has to apply.
-->
```mermaid
%%{init: {"sequence": {"actorFontSize": 22, "messageFontSize": 20, "noteFontSize": 20, "actorMargin": 70, "messageMargin": 20, "boxMargin": 6, "boxTextMargin": 4, "noteMargin": 8, "diagramMarginX": 20, "diagramMarginY": 8}}}%%
sequenceDiagram
    participant Worker as Background<br/>Worker
    participant Tri as Triangulation<br/>Engine
    participant DB as PostgreSQL<br/>+ PostGIS
    participant Redis as Redis<br/>Stream
    participant WS as WebSocket
    participant App as Mobile<br/>App

    alt ≥ 3 nodes triggered in window
        Worker->>Tri: correlate_events(triggers[])

        Tri->>Tri: Compute TDOA from timestamps<br/>Δt₁₂ = t₂ - t₁, Δt₁₃ = t₃ - t₁

        Tri->>Tri: Solve least-squares minimization<br/>for epicenter (lat_e, lon_e)

        Tri->>Tri: Estimate origin time (t₀)

        Tri-->>Worker: TriangulationResult<br/>{epicenter, origin_time, confidence}

        Worker->>DB: INSERT alert<br/>(is_triangulated=True)

        Worker->>Redis: PUBLISH quake_alerts<br/>{type: TRIANGULATED, epicenter, ETA}

        Redis->>WS: Broadcast
        WS->>App: TRIANGULATED alert

        App->>App: Calculate ETA from user GPS<br/>to epicenter (wave speed ~6 km/s)

        App->>App: Show EarlyWarningBanner<br/>with countdown timer

    else < 3 nodes (single-node detection)
        Worker->>Worker: Standard single-node alert flow
    end
```
