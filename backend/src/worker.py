import json
import math
import os
import socket
import time
from datetime import datetime, timezone
import redis
from sqlalchemy.orm import Session
from src.database import SessionLocal, engine
from src.geo import COOLDOWN_KEY_PREFIX
from src.triangulation import triangulate_epicenter
from src.ingest import (
    READINGS_STREAM,
    READINGS_GROUP,
    CONSUMER_PREFIX,
    BATCH_SIZE,
    BLOCK_MS,
    ensure_group,
    read_batch,
    ack,
    move_to_dlq,
    recover_pending,
)
from src.models import Reading, Alert, EmergencyReport, Zone

# Redis Config
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
redis_sync = redis.from_url(REDIS_URL, decode_responses=True)

# AI Report integration
AI_REPORT_QUEUE = os.getenv("AI_REPORT_QUEUE", "ai_report_queue")
# Gate: when False (or unset), the worker skips AI report creation/enqueue entirely.
# The Ollama + ai-worker containers run behind the `ai` compose profile.
AI_REPORT_ENABLED = os.getenv("AI_REPORT_ENABLED", "false").strip().lower() in ("1", "true", "yes", "on")

# Seismic Calibration Constants (Tunable via Environment)
K_CALIBRATION = float(os.getenv("K_CALIBRATION", "1.6"))  # MyShake-style MEMS calibration factor
B_OFFSET = float(os.getenv("B_OFFSET", "3.0"))            # Empirical offset, anchor: PGA 0.07 m/s² ≈ M3.85
SENSOR_SCALE = float(os.getenv("SENSOR_SCALE", "100.0"))  # Raw value to m/s² conversion factor

def estimate_magnitude(sensor_value: int) -> float:
    """
    Estimates IoT magnitude from STA-based peak acceleration.
    Formula: M_IoT = log10(PGA_calib) + b
    Based on MyShake-style MEMS network approach.
    Reference: Zanotti, G. (2026) - QuakeGuard Magnitude Estimation Note.
    """
    pga_m_s2 = sensor_value / SENSOR_SCALE
    pga_calib = pga_m_s2 / K_CALIBRATION
    
    # Guard against log10(0) or negative values
    if pga_calib <= 0:
        return 0.0
    
    magnitude = math.log10(pga_calib) + B_OFFSET
    
    # Clamp to physically meaningful range for MEMS sensors
    return max(0.0, min(magnitude, 9.9))

def _handle_triangulation(event: dict, magnitude: float, buffer_key: str):
    if not buffer_key or event.get("latitude") is None:
        return None
        
    trigger_data = {
        "sensor_id": event.get("sensor_id"),
        "latitude": event.get("latitude"),
        "longitude": event.get("longitude"),
        "magnitude": magnitude,
        "timestamp": event.get("timestamp", datetime.now(timezone.utc).isoformat())
    }
    length = redis_sync.rpush(buffer_key, json.dumps(trigger_data))
    if length == 1:
        redis_sync.expire(buffer_key, 60)
    
    if length == 3:
        raw_triggers = redis_sync.lrange(buffer_key, 0, -1)
        triggers = [json.loads(t) for t in raw_triggers]
        try:
            return triangulate_epicenter(triggers)
        except Exception as e:
            print(f"❌ Triangulation failed: {e}", flush=True)
    return None

def _enrich_event(event: dict, db: Session) -> dict:
    """Stage one reading (+ optional alert) into the session. Returns a resolution
    dict consumed by ``_finish_alerts`` after the shared commit. No commit here so
    a whole stream batch can be flushed in a single transaction."""
    new_entry = Reading(
        value=event.get("value"),
        sensor_id=event.get("sensor_id"),
        latitude=event.get("latitude"),
        longitude=event.get("longitude"),
        free_heap=event.get("free_heap"),
        rssi=event.get("rssi"),
        gnss_satellites=event.get("gnss_satellites"),
        latency_ms=event.get("latency_ms"),
    )
    db.add(new_entry)

    sensor_value = event.get("value", 0)
    magnitude = estimate_magnitude(sensor_value)
    zone_id = event.get("zone_id", 0)
    alert_entry = None
    triangulation_data = None

    if magnitude >= 4.5:
        area_key = event.get("sensor_geohash") or event.get("geohash")
        if area_key:
            cooldown_key = f"{COOLDOWN_KEY_PREFIX}:{area_key}"
            buffer_key = f"triangulation_buffer:{area_key}"
        else:
            cooldown_key = f"{COOLDOWN_KEY_PREFIX}:zone:{zone_id}"
            buffer_key = None

        if redis_sync.set(cooldown_key, "active", nx=True, ex=60):
            alert_entry = Alert(
                zone_id=zone_id,
                magnitude=magnitude,
                message=f"High seismic activity detected (Sensor {event.get('sensor_id')})!"
            )
            db.add(alert_entry)
        else:
            print(f"🚫 ALERT SUPPRESSED: area '{area_key or zone_id}' is in 60s cooldown.", flush=True)
            
        triangulation_data = _handle_triangulation(event, magnitude, buffer_key)

    return {
        "event": event,
        "magnitude": magnitude,
        "zone_id": zone_id,
        "sensor_id": event.get("sensor_id"),
        "alert": alert_entry,
        "triangulation_data": triangulation_data,
    }

def _finish_alerts(db: Session, resolutions: list) -> None:
    """After the shared commit: publish any CRITICAL alert to the Redis Pub/Sub
    channel and enqueue AI report generation. Runs per-resolution (alerts are rare)."""
    for resolution in resolutions:
        alert_entry = resolution["alert"]
        triangulation_data = resolution.get("triangulation_data")
        zone_id = resolution["zone_id"]
        magnitude = resolution["magnitude"]
        sensor_id = resolution["sensor_id"]
        event = resolution["event"]
        
        # Triangulation logic: if we just hit 3 sensors, we might not have a new alert_entry
        # so we upgrade the most recent one for this zone.
        if triangulation_data:
            recent_alert = db.query(Alert).filter(Alert.zone_id == zone_id).order_by(Alert.id.desc()).first()
            if recent_alert:
                recent_alert.latitude = triangulation_data["latitude"]
                recent_alert.longitude = triangulation_data["longitude"]
                recent_alert.origin_time = datetime.fromisoformat(triangulation_data["origin_time"])
                recent_alert.is_triangulated = True
                db.commit()
                db.refresh(recent_alert)
                
                alert_payload = {
                    "type": "TRIANGULATED",
                    "alert_id": recent_alert.id,
                    "zone_id": zone_id,
                    "magnitude": round(recent_alert.magnitude, 1),
                    "message": "Epicenter Triangulated!",
                    "latitude": recent_alert.latitude,
                    "longitude": recent_alert.longitude,
                    "origin_time": recent_alert.origin_time.isoformat(),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                redis_sync.publish("quake_alerts", json.dumps(alert_payload))
                print(f"📍 TRIANGULATION PUBLISHED: Zone {zone_id} - Epicenter calculated", flush=True)
                
                if AI_REPORT_ENABLED:
                    event["triangulated_latitude"] = recent_alert.latitude
                    event["triangulated_longitude"] = recent_alert.longitude
                    event["origin_time"] = recent_alert.origin_time.isoformat()
                    enqueue_ai_report(db, event, recent_alert.id, zone_id, recent_alert.magnitude)

        if alert_entry is None:
            continue
        db.refresh(alert_entry)

        alert_payload = {
            "type": "CRITICAL",
            "alert_id": alert_entry.id,
            "zone_id": zone_id,
            "magnitude": round(magnitude, 1),
            "message": f"High seismic activity detected (Sensor {sensor_id})!",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        redis_sync.publish("quake_alerts", json.dumps(alert_payload))
        print(f"🚨 ALERT PUBLISHED: Zone {zone_id} - Mag {round(magnitude, 1)}", flush=True)

        if AI_REPORT_ENABLED:
            enqueue_ai_report(db, event, alert_entry.id, zone_id, magnitude)

def process_event(event: dict, db: Session):
    """Single-event processing (compatibility + tests). Batch workloads use
    ``process_batch`` so one transaction covers N readings."""
    resolution = _enrich_event(event, db)
    db.commit()
    _finish_alerts(db, [resolution])

def process_batch(events: list, db: Session):
    """Process a stream batch in ONE transaction. Cooldown locks are taken
    per-event (atomic Redis SET NX), DB writes are batched and committed once."""
    resolutions = [_enrich_event(event, db) for event in events]
    db.commit()
    _finish_alerts(db, resolutions)

def _resolve_zone_name(db: Session, zone_id: int) -> str:
    """Resolve zone name from zone_id, return 'Unknown Region' if not found."""
    if not zone_id:
        return "Unknown Region"
    zone = db.query(Zone).filter(Zone.id == zone_id).first()
    return zone.city if zone is not None else "Unknown Region"


def _create_pending_report(db: Session, alert_id: int, zone_id: int, magnitude: float) -> EmergencyReport:
    """Create and persist a PENDING EmergencyReport, return the saved instance."""
    report = EmergencyReport(
        alert_id=alert_id,
        zone_id=zone_id,
        magnitude=magnitude,
        status="PENDING",
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def _build_ai_payload(report: EmergencyReport, event: dict, zone_name: str) -> dict:
    """Build the AI report job payload for the queue."""
    return {
        "report_id": report.id,
        "alert_id": report.alert_id,
        "zone_id": report.zone_id,
        "zone_name": zone_name,
        "magnitude": round(report.magnitude, 1),
        "sensor_id": event.get("sensor_id"),
        "value": event.get("value"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def enqueue_ai_report(db: Session, event: dict, alert_id: int, zone_id: int, magnitude: float) -> None:
    """Create a PENDING EmergencyReport and enqueue the AI report job.

    The DB row is written first so the state machine is observable (PENDING) even
    before the dedicated AI worker processes the job. The AI worker transitions it
    to COMPLETED or FAILED and broadcasts the result over WebSocket.
    """
    zone_name = _resolve_zone_name(db, zone_id)
    report = _create_pending_report(db, alert_id, zone_id, magnitude)
    ai_payload = _build_ai_payload(report, event, zone_name)
    redis_sync.lpush(AI_REPORT_QUEUE, json.dumps(ai_payload))
    print(f"🤖 AI Report enqueued (report_id={report.id})", flush=True)

def _parse_batch(batch: list) -> list:
    """Decode raw stream entries; park malformed payloads on the DLQ."""
    pending = []
    for message_id, payload in batch:
        try:
            event = json.loads(payload)
        except Exception:
            print("❌ Malformed payload -> DLQ.", flush=True)
            try:
                move_to_dlq(redis_sync, message_id, payload, reason="malformed_json")
            except Exception as e:
                print(f"❌ DLQ write failed: {e}", flush=True)
            continue
        pending.append((message_id, event, payload))
    return pending


def _process_pending(pending: list, db: Session) -> None:
    """Persist a parsed batch in one transaction and acknowledge the stream."""
    try:
        process_batch([event for _, event, _ in pending], db)
        ack(redis_sync, [message_id for message_id, _, _ in pending])
        for _, event, _ in pending:
            print(
                f"✅ Processed sensor {event.get('sensor_id')} -> {event.get('value')} "
                f"(Mag: {estimate_magnitude(event.get('value', 0))})",
                flush=True,
            )
    except Exception as e:
        print(f"❌ Batch DB Error: {e}. Moving batch to DLQ.", flush=True)
        db.rollback()
        for message_id, _, payload in pending:
            try:
                move_to_dlq(redis_sync, message_id, payload, reason=f"process_error: {e}")
            except Exception as dlq_err:
                print(f"❌ DLQ write failed: {dlq_err}", flush=True)


def run_worker():
    consumer = f"{CONSUMER_PREFIX}-{socket.gethostname()}-{os.getpid()}"
    print(f"👷 Worker started. stream='{READINGS_STREAM}' group='{READINGS_GROUP}' consumer='{consumer}'")
    db = SessionLocal()

    # Group must exist before any XREADGROUP; idempotent.
    ensure_group(redis_sync)
    # Reclaim entries left pending by a crashed/restarted sibling (at-least-once).
    try:
        recovered = recover_pending(redis_sync, consumer)
        if recovered:
            print(f"🔁 Reclaimed {recovered} stale pending entr{'y' if recovered == 1 else 'ies'}.", flush=True)
    except Exception as e:
        print(f"⚠️ Pending recovery skipped: {e}", flush=True)

    while True:
        try:
            batch = read_batch(redis_sync, consumer, count=BATCH_SIZE, block_ms=BLOCK_MS)
            if not batch:
                continue

            pending = _parse_batch(batch)
            if not pending:
                continue

            _process_pending(pending, db)

        except Exception as e:
            print(f"❌ Redis Connection Error: {e}", flush=True)
            time.sleep(2)

if __name__ == "__main__":
    run_worker()