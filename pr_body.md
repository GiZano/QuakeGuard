## Overview
This PR finalizes the `v2.1.1` release for QuakeGuard. It corrects critical bugs in the mock simulation endpoint (`/demo/trigger-earthquake`), synchronizes the documentation and whitepaper with these changes, adds Pisa to the Hollywood Simulator, and performs a complete repository-wide version bump to `2.1.1` in preparation for the final release tag.

## Changes Made
* **`backend/src/main.py` & `backend/src/schemas.py`**: Fixed the `/demo/trigger-earthquake` endpoint. Epicenter coordinates are now dynamically fetched from the zone's PostGIS centroid. The mock calibration coefficient was corrected from `160` to `1.6` to align with the actual worker logic. Default magnitude was lowered to 5.0 for realistic demonstrations.
* **`scripts/seed_world_zones.py` & `scripts/hollywood.py`**: Added Pisa to the Hollywood Demo orchestration environment.
* **`firmware/esp32_config.env`**: Set static GNSS fallback coordinates to Pisa for local video recordings.
* **`docs/whitepaper/16-appendix.typ` & `QuakeGuard_Technical_Report_v2.1.1.pdf`**: Rewrote Appendix A to fully document the cascade effect of the demo endpoint (DB inserts, AI Worker trigger, fake telemetry generation). Re-compiled the Typst whitepaper.
* **Repository-wide Version Bump**: Systematically updated all versions from `2.1.0` to `2.1.1` across `package.json`, `.cff`, `.js`, `settings.tsx`, OpenAPI docs, SVGs, and `CHANGELOG.md`. Also removed a ghost "Timeseries" roadmap item that was already completed in v1.2.1.
* **`backend/tests/unit/test_schemas.py`**: Fixed a failing unit test asserting the old `7.5` magnitude default. All 157 tests now pass.

## Impact & Next Steps
This ensures the QuakeGuard demo functionality is statistically robust, spatially accurate, and safely bounded for public exhibitions. It also guarantees a completely clean `v2.1.1` release with no mismatched tags or documentation ghosts.

## Testing Performed
- [x] Ran full `pytest` suite locally on backend (`157 passed`).
- [x] Executed full version search sweep, avoiding node_modules and dependency lists (`cffi`, `paho-mqtt` undisturbed).
- [x] Recompiled `main.typ` manually to ensure PDF generation works with the new roadmap and versions.

## Related Issues
Closes QuakeGuard v2.1.1 hotfix sprint.
