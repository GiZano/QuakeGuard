# Graph Report - QuakeGuard  (2026-10-02)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 1198 nodes · 2206 edges · 78 communities (53 shown, 25 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 75 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `a2d84c49`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- models.py
- security.py
- ai_report_worker.py
- package.json
- test_api.py
- schemas.py
- expo
- dependencies
- main.cpp
- GnssModule
- map.tsx
- WebSocketContext.tsx
- index.tsx
- geo.py
- index.ts
- hollywood.py
- worker.py
- timescale.py
- SeismicDetector
- process_event
- usePreferencesStore
- metrics.py
- calibrate_io.py
- _client
- _enrich_event
- stress_test.py
- SerialFallback.h
- CryptoContext
- mqtt_subscriber.py
- test_timescale.py
- synthetic.py
- devDependencies
- orchestrator.py
- test_geo_integration.py
- estimate_magnitude
- DetectionCore.h
- quakeguard-demo.js
- main.py
- triangulate_epicenter
- RetentionRing
- settings.tsx
- serial_bridge.py
- pytest
- candidate_zone_ids
- point_to_geohash
- Session
- RingBuffer
- download_esm.py
- _create_sensor
- key_gen.py
- calibrate.py
- quakeguard_init.sh script
- time
- zone_covering_geohashes
- rules
- devices.tsx
- tsconfig.json
- ConnectionManager
- _is_group_exists
- VirtualSensor
- health_check
- run_malformed_burst
- .test_loop_moves_batch_error_to_dlq_and_continues
- EarlyWarningBanner.tsx
- rate_limiter
- get_test_zone
- hollywood.sh
- ollama-entrypoint.sh
- convert_diagrams.sh

## God Nodes (most connected - your core abstractions)
1. `SeismicDetector` - 25 edges
2. `GnssModule` - 21 edges
3. `EmergencyReport` - 20 edges
4. `MonitorScreen()` - 20 edges
5. `useAppTheme()` - 20 edges
6. `ReadingCreate` - 17 edges
7. `point_to_geohash()` - 17 edges
8. `usePreferencesStore` - 17 edges
9. `Zone` - 16 edges
10. `estimate_magnitude()` - 16 edges

## Surprising Connections (you probably didn't know these)
- `_finish_alerts()` --uses--> `Alert`  [INFERRED]
  backend/src/worker.py → backend/src/models.py
- `mark_failed()` --uses--> `EmergencyReport`  [INFERRED]
  backend/src/ai_report_worker.py → backend/src/models.py
- `process_ai_event()` --uses--> `EmergencyReport`  [INFERRED]
  backend/src/ai_report_worker.py → backend/src/models.py
- `publish_report()` --uses--> `EmergencyReport`  [INFERRED]
  backend/src/ai_report_worker.py → backend/src/models.py
- `_build_ai_payload()` --uses--> `EmergencyReport`  [INFERRED]
  backend/src/worker.py → backend/src/models.py

## Import Cycles
- None detected.

## Communities (78 total, 25 thin omitted)

### Community 0 - "models.py"
Cohesion: 0.05
Nodes (23): delete_zone_readings(), get_zone_alerts(), get_zone_readings(), trigger_demo_earthquake(), Alert, EmergencyReport, Reading, Sensor (+15 more)

### Community 1 - "security.py"
Cohesion: 0.05
Nodes (21): ensure_zone(), estimate_magnitude(), headers(), _magnitude_flag(), main(), normalize(), register_sensor(), sample_value() (+13 more)

### Community 2 - "ai_report_worker.py"
Cohesion: 0.07
Nodes (15): mark_failed(), process_ai_event(), publish_report(), run_ai_worker(), build_prompt(), generate_report(), parse_report(), _make_report() (+7 more)

### Community 3 - "package.json"
Cohesion: 0.06
Nodes (37): queryClient, RootLayout(), WebSocketProvider(), isNewerVersion(), useUpdateChecker(), main, name, private (+29 more)

### Community 4 - "test_api.py"
Cohesion: 0.06
Nodes (11): get_db(), allow_redis(), auth_headers(), client(), override_db(), rate_limited_redis(), TestDeviceRegistration, TestHealthEndpoint (+3 more)

### Community 5 - "schemas.py"
Cohesion: 0.12
Nodes (17): Alert, DemoAlertRequest, DeviceRegisterRequest, EmergencyReport, Reading, Sensor, SensorBase, SensorCreate (+9 more)

### Community 6 - "expo"
Cohesion: 0.06
Nodes (31): backgroundColor, foregroundImage, adaptiveIcon, edgeToEdgeEnabled, package, permissions, predictiveBackGestureEnabled, typedRoutes (+23 more)

### Community 7 - "dependencies"
Cohesion: 0.06
Nodes (32): dependencies, axios, expo, expo-asset, expo-audio, expo-camera, expo-constants, expo-device (+24 more)

### Community 8 - "main.cpp"
Cohesion: 0.10
Nodes (10): deliverEvent(), drainRetention(), gnssTask(), loop(), networkTask(), SeismicEvent, event_millis, magnitude (+2 more)

### Community 9 - "GnssModule"
Cohesion: 0.10
Nodes (17): GnssFix, age_ms, from_storage, latitude, longitude, valid, GnssModule, gps_ (+9 more)

### Community 10 - "map.tsx"
Cohesion: 0.12
Nodes (20): styles, CalloutStats(), createStyles(), MapScreen(), SensorCalloutDetails(), ThemeColors, createStyles(), ErrorBanner() (+12 more)

### Community 11 - "WebSocketContext.tsx"
Cohesion: 0.11
Nodes (17): ALARM_SOURCE, ensurePlayer(), playAlarm(), stopAlarm(), API_BASE_URL, IOT_API_KEY, MOBILE_WS_TOKEN, AlertMessage (+9 more)

### Community 12 - "index.tsx"
Cohesion: 0.16
Nodes (22): AiReportCard(), AlertBanner(), createStyles(), HeroSection(), MonitorScreen(), NetworkChart(), ThemeColors, TopBar() (+14 more)

### Community 13 - "geo.py"
Cohesion: 0.14
Nodes (8): _cell_indices_to_geohash(), _cell_wkt(), _cells_in_bbox(), _cell_geohash(), geohash_bounds(), _refine_axis(), TestCellsInBbox, TestGeohashBounds

### Community 14 - "index.ts"
Cohesion: 0.17
Nodes (16): DevicesIcon(), MapIcon(), MonitorIcon(), SettingsIcon(), TabLayout(), ThemeState, AppColors, COLORS (+8 more)

### Community 15 - "hollywood.py"
Cohesion: 0.14
Nodes (9): Director, generate_payload(), hollywood_loop(), load_or_create_fleet(), main(), _register_fleet(), register_sensor(), _validate_fleet() (+1 more)

### Community 16 - "worker.py"
Cohesion: 0.17
Nodes (8): ack(), ensure_group(), move_to_dlq(), read_batch(), recover_pending(), _parse_batch(), _process_pending(), run_worker()

### Community 17 - "timescale.py"
Cohesion: 0.20
Nodes (12): _add_telemetry_columns(), _apply_compression(), _apply_retention(), apply_timescale(), _create_continuous_aggregate(), _create_hypertable(), _enable_extension(), _run_aggregate_step() (+4 more)

### Community 18 - "SeismicDetector"
Cohesion: 0.10
Nodes (20): SeismicDetector, alarmStartMs_, COOLDOWN_MS, DEFAULT_HPF_ALPHA, DEFAULT_LTA_FLOOR, DEFAULT_NOISE_FLOOR, DEFAULT_TRIGGER_RATIO, filtered_ (+12 more)

### Community 19 - "process_event"
Cohesion: 0.17
Nodes (3): process_event(), _mock_zone(), TestProcessEvent

### Community 20 - "usePreferencesStore"
Cohesion: 0.17
Nodes (14): apiClient, useRecentReadings(), useSensors(), useZoneReadings(), fetchSensorStatistics(), SensorStatisticsResponse, useSensorStatistics(), Alert (+6 more)

### Community 21 - "metrics.py"
Cohesion: 0.16
Nodes (8): compute_metrics(), EventScore, GroundTruth, MetricsSummary, roc_curve(), RocPoint, score_event(), TriggerPoint

### Community 22 - "calibrate_io.py"
Cohesion: 0.15
Nodes (6): Accelerogram, load_validation_set(), read_accelerogram(), resolve_within_root(), main(), plot_roc()

### Community 23 - "_client"
Cohesion: 0.18
Nodes (7): _client(), TestAck, TestEnqueueReading, TestEnsureGroup, TestMoveToDlq, TestReadBatch, TestRecoverPending

### Community 24 - "_enrich_event"
Cohesion: 0.17
Nodes (8): _build_ai_payload(), _create_pending_report(), enqueue_ai_report(), _enrich_event(), _finish_alerts(), _handle_triangulation(), process_batch(), _resolve_zone_name()

### Community 25 - "stress_test.py"
Cohesion: 0.24
Nodes (10): get_sensor_readings(), listen_for_alerts(), main(), publish_measurement(), register_sensor(), run_ai_dedup_test(), run_load_test(), run_security_test() (+2 more)

### Community 26 - "SerialFallback.h"
Cohesion: 0.21
Nodes (9): buildSerialFrame(), decidePath(), DeliveryPath, MQTT, RETAIN, SERIAL_CDC, testFailures(), main() (+1 more)

### Community 27 - "CryptoContext"
Cohesion: 0.15
Nodes (9): calibrateADXL345(), CryptoContext, ctr_drbg_, entropy_, pk_context_, ledBootTest(), performProvisioning(), resetTask() (+1 more)

### Community 29 - "test_timescale.py"
Cohesion: 0.24
Nodes (6): _db_with_execute(), FakeResult, _ok_execute(), TestApplyTimescale, fake_execute(), fake_execute()

### Community 30 - "synthetic.py"
Cohesion: 0.17
Nodes (4): build_synthetic_dataset(), main(), RealisticSynthetic, write_accelerogram_csv()

### Community 31 - "devDependencies"
Cohesion: 0.12
Nodes (15): devDependencies, eslint, eslint-config-expo, jest, react-test-renderer, ts-jest, @types/jest, @types/react (+7 more)

### Community 32 - "orchestrator.py"
Cohesion: 0.16
Nodes (5): evaluate(), build_cli(), DetectionError, DetectionResult, run_detector()

### Community 33 - "test_geo_integration.py"
Cohesion: 0.22
Nodes (6): build_zone_index(), clear_zone_index(), resolve_zone(), infra_available(), TestResolveZoneReal, zone_name_of()

### Community 35 - "DetectionCore.h"
Cohesion: 0.20
Nodes (4): sensorTask(), main(), tMs(), main()

### Community 36 - "quakeguard-demo.js"
Cohesion: 0.18
Nodes (6): aiSeverity(), loadHistory(), log(), nowStamp(), renderAiReport(), renderFeed()

### Community 37 - "main.py"
Cohesion: 0.19
Nodes (4): lifespan(), ping_db(), redis_alert_listener(), wait_for_db()

### Community 38 - "triangulate_epicenter"
Cohesion: 0.28
Nodes (8): haversine_distance(), triangulate_epicenter(), test_haversine_distance(), test_triangulate_epicenter_insufficient_data(), test_triangulate_epicenter_isoformat_parsing(), test_triangulate_epicenter_magnitude_bias(), test_triangulate_epicenter_origin_time(), test_triangulate_epicenter_weighted_centroid()

### Community 39 - "RetentionRing"
Cohesion: 0.18
Nodes (7): RetentionRing, buffer_, count_, head_, SerialEvent, timestamp, value

### Community 40 - "settings.tsx"
Cohesion: 0.31
Nodes (11): useZones(), createStyles(), SettingsScreen(), Zone, AlertHistoryList(), createStyles(), useAlertStore, useThemeStore (+3 more)

### Community 41 - "serial_bridge.py"
Cohesion: 0.24
Nodes (5): forward(), main(), parse_frame(), _run(), _validate_api_url()

### Community 43 - "candidate_zone_ids"
Cohesion: 0.24
Nodes (3): candidate_zone_ids(), TestZoneIndexFastPath, TestCandidateZoneIds

### Community 44 - "point_to_geohash"
Cohesion: 0.25
Nodes (3): point_to_geohash(), TestGeohashVsPostGIS, TestPointToGeohash

### Community 45 - "Session"
Cohesion: 0.27
Nodes (6): get_emergency_report(), get_readings(), get_sensor_statistics(), get_sensors(), get_zones(), locate_zone()

### Community 46 - "RingBuffer"
Cohesion: 0.20
Nodes (5): RingBuffer, buffer, count, head, sum

### Community 47 - "download_esm.py"
Cohesion: 0.24
Nodes (3): download_and_process(), main(), write_accelerogram_csv()

### Community 48 - "_create_sensor"
Cohesion: 0.22
Nodes (5): enqueue_reading(), create_reading_async(), _create_sensor(), create_zone(), register_device()

### Community 50 - "calibrate.py"
Cohesion: 0.27
Nodes (4): calibrate(), f1(), _fmt_latency(), main()

### Community 51 - "quakeguard_init.sh script"
Cohesion: 0.29
Nodes (7): prompt_choice(), prompt_yes_no(), generate_secrets.sh script, print_menu(), print_qr(), quakeguard_init.sh script, tunnel_init.sh script

### Community 53 - "zone_covering_geohashes"
Cohesion: 0.28
Nodes (3): _zone_bbox(), zone_covering_geohashes(), TestZoneCoveringGeohashes

### Community 54 - "rules"
Cohesion: 0.22
Nodes (8): extends, rules, body-max-line-length, footer-max-line-length, header-max-length, scope-enum, type-enum, @commitlint/config-conventional

### Community 55 - "devices.tsx"
Cohesion: 0.31
Nodes (7): createStyles(), DevicesScreen(), DeviceStore, PairedDevice, useDeviceStore, react-native-safe-area-context, zustand

### Community 56 - "tsconfig.json"
Cohesion: 0.25
Nodes (7): compilerOptions, paths, strict, types, extends, include, expo/tsconfig.base

### Community 63 - "EarlyWarningBanner.tsx"
Cohesion: 0.83
Nodes (3): createStyles(), EarlyWarningBanner(), haversine()

## Knowledge Gaps
- **188 isolated node(s):** `ThemeColors`, `Props`, `Props`, `ThemeTokens`, `WebSocketContextType` (+183 more)
  These have ≤1 connection - possible missing edges. (Counts symbols only; 489 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **25 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `SeismicDetector` connect `SeismicDetector` to `DetectionCore.h`, `RingBuffer`?**
  _High betweenness centrality (0.028) - this node is a cross-community bridge._
- **Are the 7 inferred relationships involving `EmergencyReport` (e.g. with `mark_failed()` and `process_ai_event()`) actually correct?**
  _`EmergencyReport` has 7 INFERRED edges - model-reasoned connections that need verification._
- **What connects `ThemeColors`, `Props`, `Props` to the rest of the system?**
  _188 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `models.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05028305028305028 - nodes in this community are weakly interconnected._
- **Should `security.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05223880597014925 - nodes in this community are weakly interconnected._
- **Should `ai_report_worker.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06938775510204082 - nodes in this community are weakly interconnected._
- **Should `package.json` be split into smaller, more focused modules?**
  _Cohesion score 0.059233449477351915 - nodes in this community are weakly interconnected._