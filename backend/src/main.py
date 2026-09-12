"""
QuakeGuard Backend Service API
-------------------------------
Core API Gateway.
Responsibilities:
1. IoT Data Ingestion.
2. Data Retrieval (REST).
3. Real-Time Alert Distribution (Redis Pub/Sub -> WebSocket).
"""

import json
import asyncio
import time
import os
from typing import List
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from urllib.parse import urlparse

import asyncpg
from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from sqlalchemy.exc import OperationalError
from redis import asyncio as aioredis
from geoalchemy2.elements import WKTElement

# --- LOCAL MODULES ---
from src.database import get_db, engine, SessionLocal, DATABASE_URL
from src.geo import (
    COOLDOWN_PRECISION,
    ZONE_INDEX_PRECISION,
    build_zone_index,
    candidate_zone_ids,
    point_to_geohash,
)
from src import ingest
import src.models as models
import src.schemas as schemas
from src.security import verify_api_key, validate_iot_payload
from src.seed import seed_zones
from src.timescale import apply_timescale

PING_QUERY = "SELECT 1"

ZONE_NOT_FOUND = "Zone not found"

# --- SECURE CONFIGURATION ---
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

MOBILE_WS_TOKEN = os.getenv("MOBILE_WS_TOKEN")
if not MOBILE_WS_TOKEN or len(MOBILE_WS_TOKEN) < 8:
    raise RuntimeError("🚨 CRITICAL STARTUP ERROR: 'MOBILE_WS_TOKEN' environment variable is not set or too short (min 8 chars)!")

ENROLLMENT_TOKEN = os.getenv("ENROLLMENT_TOKEN")
if not ENROLLMENT_TOKEN or len(ENROLLMENT_TOKEN) < 8:
    raise RuntimeError("🚨 CRITICAL STARTUP ERROR: 'ENROLLMENT_TOKEN' environment variable is not set or too short (min 8 chars)!")

# ==========================================
# INFRASTRUCTURE INITIALIZATION
# ==========================================

def wait_for_db(retries: int = 10, delay: int = 3) -> None:
    print("Checking Database connection...")
    for i in range(retries):
        try:
            with engine.connect() as connection:
                connection.execute(text(PING_QUERY))
            print("✅ Database is up and running!")
            return
        except OperationalError:
            print(f"⏳ Waiting for DB... ({i+1}/{retries})")
            time.sleep(delay)
    raise ConnectionError("❌ DB Connection Failed after multiple retries.")

def ping_db() -> None:
    """Synchronous helper to ping the PostgreSQL database."""
    with engine.connect() as connection:
        connection.execute(text(PING_QUERY))

redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)

# ==========================================
# REAL-TIME NOTIFICATION SYSTEM (PUBSUB)
# ==========================================

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"📱 Client Connected. Active: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print(f"📱 Client Disconnected. Active: {len(self.active_connections)}")

    async def broadcast(self, message: str) -> None:
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                print(f"⚠️ Failed to broadcast to a client: {e}")
                dead_connections.append(connection)
                
        for dead in dead_connections:
            self.disconnect(dead)

manager = ConnectionManager()

async def redis_alert_listener() -> None:
    pubsub = redis_client.pubsub()
    await pubsub.subscribe("quake_alerts", "ai_reports")
    print("🎧 Redis Pub/Sub Listener active on channels: 'quake_alerts', 'ai_reports'")

    async for message in pubsub.listen():
        if message["type"] == "message":
            alert_payload = message["data"]
            await manager.broadcast(alert_payload)

@asynccontextmanager
async def lifespan(app: FastAPI):
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, wait_for_db)
    # PostGIS must exist before create_all: the models use `geometry` columns.
    # Some DB images (e.g. timescale-ha) do not run the postgis init hook, so the
    # app ensures the extension itself — idempotent and safe on stock PostGIS.
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
    await loop.run_in_executor(None, lambda: models.Base.metadata.create_all(bind=engine))

    with SessionLocal() as db:
        seed_zones(db)
        build_zone_index(db)
        # TimescaleDB hypertable + rollups (best-effort; no-op on plain PostGIS).
        try:
            apply_timescale(db)
        except Exception as e:
            print(f"⚠️ TimescaleDB migration skipped: {e}", flush=True)

    # Ensure the ingestion consumer group exists so stream reads never error.
    try:
        await ingest.ensure_group_async(redis_client)
    except Exception as e:
        print(f"⚠️ Ingest group ensure skipped: {e}", flush=True)

    listener_task = asyncio.create_task(redis_alert_listener())
    yield
    listener_task.cancel()

# Initialize FastAPI
app = FastAPI(title="QuakeGuard Backend", version="2.1.0", lifespan=lifespan)

# ==========================================
# MIDDLEWARE
# ==========================================

async def rate_limiter(request: Request):
    """Sliding-window rate limiter using Redis sorted sets. Uses X-Forwarded-For if behind proxy."""
    forwarded = request.headers.get("X-Forwarded-For")
    client_ip = forwarded.split(",")[0].strip() if forwarded else request.client.host
    now = time.time()
    window = 1.0
    key = f"rate_limit:{client_ip}"
    
    # Remove entries outside the window and add current timestamp
    await redis_client.zremrangebyscore(key, 0, now - window)
    await redis_client.zadd(key, {str(now): now})
    await redis_client.expire(key, 60)
    
    request_count = await redis_client.zcard(key)
        
    if request_count > 50:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Too many requests from this IP."
        )

def resolve_zone(db: Session, latitude: float | None, longitude: float | None) -> int:
    """
    Spatial auto-assignment helper.
    Finds the smallest containing polygon for given GPS coordinates.
    Falls back to 'Unknown Region' if no match is found or coordinates are null.

    Fast path: the Redis zone-index (geohash -> zone ids) resolves the zone for
    a coordinate without a DB round-trip. On a miss or an ambiguous multi-zone
    match we fall back to the authoritative PostGIS ST_Contains query, so the
    Redis cache is purely an optimization and can never assign a wrong zone.
    """
    if latitude is None or longitude is None:
        fallback = db.query(models.Zone).filter(models.Zone.city == "Unknown Region").first()
        return fallback.id if fallback else 1

    candidates = candidate_zone_ids(latitude, longitude, precision=ZONE_INDEX_PRECISION)
    if len(candidates) == 1:
        return candidates.pop()

    # Redis miss, empty or ambiguous match -> authoritative PostGIS query
    point = WKTElement(f"POINT({longitude} {latitude})", srid=4326)

    # Query PostGIS to find the containing polygon, ordered by smallest area first
    matched_zone = db.query(models.Zone).filter(
        func.ST_Contains(models.Zone.geom, point)
    ).order_by(func.ST_Area(models.Zone.geom).asc()).first()

    if matched_zone:
        return matched_zone.id

    # Fallback to Unknown Region
    fallback = db.query(models.Zone).filter(models.Zone.city == "Unknown Region").first()
    return fallback.id if fallback else 1  # Final failsafe

# ==========================================
# WEBSOCKET ENDPOINT
# ==========================================

@app.websocket("/ws/alerts")
async def websocket_endpoint(websocket: WebSocket):
    token = websocket.query_params.get("token")
    if token != MOBILE_WS_TOKEN:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
        
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except Exception:
        manager.disconnect(websocket)

# ==========================================
# REST API ENDPOINTS
# ==========================================

# --- HEALTH CHECK ---
@app.get("/health", tags=["Observability"])
async def health_check():
    """
    Infrastructure Observability Endpoint.
    Pings PostgreSQL and Redis concurrently to verify full system health.
    """
    health_status = {
        "status": "ok",
        "postgres": "connected",
        "redis": "connected"
    }
    http_status_code = status.HTTP_200_OK

    # 1. Define discrete async checks with error logging
    async def check_postgres():
        try:
            parsed = urlparse(DATABASE_URL)
            conn = await asyncpg.connect(
                host=parsed.hostname or "localhost",
                port=parsed.port or 5432,
                user=parsed.username,
                password=parsed.password,
                database=parsed.path.lstrip("/"),
            )
            await conn.execute(PING_QUERY)
            await conn.close()
            return True
        except Exception as e:
            print(f"❌ Health Check - Postgres Error: {e}", flush=True)
            return False

    async def check_redis():
        try:
            await redis_client.ping()
            return True
        except Exception as e:
            print(f"❌ Health Check - Redis Error: {e}", flush=True)
            return False

    # 2. Execute checks concurrently
    pg_ok, redis_ok = await asyncio.gather(check_postgres(), check_redis())

    # 3. Evaluate results
    if not pg_ok:
        health_status["status"] = "error"
        health_status["postgres"] = "disconnected"
        http_status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    if not redis_ok:
        health_status["status"] = "error"
        health_status["redis"] = "disconnected"
        http_status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    if http_status_code != status.HTTP_200_OK:
        return JSONResponse(status_code=http_status_code, content=health_status)
        
    return health_status

@app.post("/demo/trigger-earthquake", status_code=status.HTTP_200_OK, tags=["Demo"], dependencies=[Depends(verify_api_key)])
async def trigger_demo_earthquake(
    payload: schemas.DemoAlertRequest,
):
    """
    Instantly triggers a simulated TRIANGULATED earthquake alert.
    Bypasses the IoT ingestion pipeline and broadcasts directly to all connected WebSocket clients.
    """
    db = next(get_db())
    
    # We resolve the actual zone name if we can for realism
    zone = db.query(models.Zone).filter(models.Zone.id == payload.zone_id).first()
    
    lat = 45.4642
    lon = 9.1900
    if zone and zone.geom is not None:
        lon_scalar = db.scalar(func.ST_X(func.ST_Centroid(zone.geom)))
        lat_scalar = db.scalar(func.ST_Y(func.ST_Centroid(zone.geom)))
        if lon_scalar is not None and lat_scalar is not None:
            lon = float(lon_scalar)
            lat = float(lat_scalar)

    # Construct the exact payload format expected by the frontend WebSocketContext
    alert_data = {
        "type": "TRIANGULATED",
        "zone_id": payload.zone_id,
        "magnitude": payload.magnitude,
        "message": payload.message,
        "latitude": lat,
        "longitude": lon,
        "origin_time": datetime.now(timezone.utc).isoformat(),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    # Publish directly to the Redis Pub/Sub channel for live updates
    await redis_client.publish("quake_alerts", json.dumps(alert_data))


    # 1. Create an Alert record so we can link the EmergencyReport
    demo_alert = models.Alert(
        zone_id=payload.zone_id,
        magnitude=payload.magnitude,
        message=payload.message,
        latitude=alert_data["latitude"],
        longitude=alert_data["longitude"],
        is_triangulated=True,
        origin_time=datetime.now(timezone.utc)
    )
    db.add(demo_alert)
    db.commit()
    db.refresh(demo_alert)

    # 2. Create the PENDING EmergencyReport
    demo_report = models.EmergencyReport(
        alert_id=demo_alert.id,
        zone_id=payload.zone_id,
        magnitude=payload.magnitude
    )
    db.add(demo_report)
    db.commit()
    db.refresh(demo_report)

    # Also push to the AI Worker queue so the AI report gets generated
    ai_telemetry = {
        "report_id": demo_report.id,
        "alert_id": demo_alert.id,
        "zone_id": payload.zone_id,
        "zone_name": zone.city if zone else "Demo Zone", 
        "magnitude": payload.magnitude,
        "sensor_id": 999,
        "value": 1000,
        "triangulated_latitude": alert_data["latitude"],
        "triangulated_longitude": alert_data["longitude"]
    }

    await redis_client.lpush("ai_report_queue", json.dumps(ai_telemetry))
    
    # -------------------------------------------------------------
    # Inject fake readings into the database so the Mobile Graph updates
    # -------------------------------------------------------------
    from datetime import timedelta
    
    sensor = db.query(models.Sensor).filter(models.Sensor.zone_id == payload.zone_id).first()
    if not sensor:
        sensor = models.Sensor(zone_id=payload.zone_id, public_key_hex=f"demo-{int(datetime.now().timestamp())}", active=True)
        db.add(sensor)
        db.commit()
        db.refresh(sensor)
        
    demo_magnitudes = [4.0, 4.4, payload.magnitude, 4.7, 4.2]
    now_dt = datetime.now(timezone.utc)
    
    for i, mag in enumerate(demo_magnitudes):
        # Reverse engineer the raw sensor value:
        # magnitude = log10(sensorValue / 1.6) + 3.0
        # 10^(magnitude - 3.0) = sensorValue / 1.6
        raw_value = int(1.6 * (10 ** (mag - 3.0)))
        
        # Space them out by 1 second leading up to now
        record_time = now_dt - timedelta(seconds=(len(demo_magnitudes) - i - 1))
        
        reading = models.Reading(
            sensor_id=sensor.id,
            value=raw_value,
            recorded_at=record_time
        )
        db.add(reading)
        
    db.commit()

    return {
        "status": "success",
        "detail": "Demo alert broadcasted successfully",
        "payload": alert_data
    }

@app.post("/zones/", response_model=schemas.Zone, status_code=status.HTTP_201_CREATED, tags=["Registration"], dependencies=[Depends(verify_api_key)])
def create_zone(zone: schemas.ZoneCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Zone).filter(models.Zone.city == zone.city).first()
    if existing:
        return existing 
        
    db_zone = models.Zone(city=zone.city)
    db.add(db_zone)
    db.commit()
    db.refresh(db_zone)
    return db_zone

@app.get("/zones/", response_model=List[schemas.Zone], tags=["Data Retrieval"], dependencies=[Depends(verify_api_key)])
def get_zones(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    if skip < 0:
        skip = 0
    limit = min(limit, 1000)
    return db.query(models.Zone).offset(skip).limit(limit).all()

@app.get("/zones/locate", response_model=schemas.Zone, tags=["Data Retrieval"], dependencies=[Depends(verify_api_key)])
def locate_zone(latitude: float, longitude: float, db: Session = Depends(get_db)):
    """
    Resolve GPS coordinates to the smallest containing monitored zone.

    Powers the "Detect my zone" flow: the app pings this with a GPS fix and gets
    the zone back so alert alarms can be scoped to the operator's own area.
    Returns 404 when the coordinate is not covered by any monitored polygon.
    """
    matched = (
        db.query(models.Zone)
        .filter(func.ST_Contains(models.Zone.geom, WKTElement(f"POINT({longitude} {latitude})", srid=4326)))
        .order_by(func.ST_Area(models.Zone.geom).asc())
        .first()
    )
    if matched is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Coordinates not inside any monitored zone")
    return matched

def _create_sensor(db: Session, active: bool, zone_id: int | None, latitude: float | None, longitude: float | None, public_key_hex: str, mac_address: str | None = None) -> models.Sensor:
    """Create and persist a Sensor with spatial zone auto-assignment."""
    assigned_zone_id = zone_id or resolve_zone(db, latitude, longitude)
    # GNSS-ready: coordinates are optional at first boot. Store NULL geometry
    # when unknown instead of building an invalid "POINT(None None)".
    point = None
    if latitude is not None and longitude is not None:
        point = WKTElement(f"POINT({longitude} {latitude})", srid=4326)
    db_sensor = models.Sensor(
        active=active,
        zone_id=assigned_zone_id,
        latitude=latitude,
        longitude=longitude,
        location=point,
        public_key_hex=public_key_hex,
        mac_address=mac_address,
    )
    db.add(db_sensor)
    db.commit()
    db.refresh(db_sensor)
    return db_sensor

@app.post("/sensors/", response_model=schemas.Sensor, status_code=status.HTTP_201_CREATED, tags=["Registration"], dependencies=[Depends(verify_api_key)])
def create_sensor(sensor: schemas.SensorCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Sensor).filter(models.Sensor.public_key_hex == sensor.public_key_hex).first()
    if existing:
        return existing
    return _create_sensor(db, sensor.active, sensor.zone_id, sensor.latitude, sensor.longitude, sensor.public_key_hex)

@app.post("/devices/register", status_code=status.HTTP_201_CREATED, tags=["Provisioning"])
def register_device(payload: schemas.DeviceRegisterRequest, db: Session = Depends(get_db)):
    """Automated Device Handshake with Spatial Zone Assignment."""
    if payload.enrollment_token != ENROLLMENT_TOKEN:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid enrollment token")

    existing = db.query(models.Sensor).filter(
        (models.Sensor.mac_address == payload.mac_address) |
        (models.Sensor.public_key_hex == payload.public_key_hex)
    ).first()

    if existing:
        # GNSS-ready: a relocated node (or a spare re-deployed after a cold
        # boot) re-reports its real fix at handshake time. Keep the last known
        # coordinates fresh and re-assign the zone if it actually moved.
        if payload.latitude is not None and payload.longitude is not None:
            moved = (
                existing.latitude != payload.latitude
                or existing.longitude != payload.longitude
            )
            if moved:
                existing.latitude = payload.latitude
                existing.longitude = payload.longitude
                existing.location = WKTElement(
                    f"POINT({payload.longitude} {payload.latitude})", srid=4326
                )
                existing.zone_id = resolve_zone(db, payload.latitude, payload.longitude)
                db.commit()
                print(
                    f"[PROV] Sensor {existing.id} moved -> new zone_id {existing.zone_id}",
                    flush=True,
                )
        return {"sensor_id": existing.id}

    new_device = _create_sensor(db, True, None, payload.latitude, payload.longitude, payload.public_key_hex, payload.mac_address)
    return {"sensor_id": new_device.id}

@app.get("/sensors/", response_model=List[schemas.Sensor], tags=["Data Retrieval"], dependencies=[Depends(verify_api_key)])
def get_sensors(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    if skip < 0:
        skip = 0
    limit = min(limit, 1000)
    return db.query(models.Sensor).offset(skip).limit(limit).all()

@app.post("/readings/", status_code=status.HTTP_202_ACCEPTED, tags=["Ingestion"], dependencies=[Depends(rate_limiter)])
async def create_reading_async(
    # 💡 MAGIC HAPPENS HERE: validate_iot_payload handles all cryptography, replay checks, and API Key checks!
    valid_data: dict = Depends(validate_iot_payload)
):
    # Extract the validated objects returned from our security module
    reading = valid_data["reading"]
    sensor = valid_data["sensor"]
    
    # Enqueue for Worker
    payload = reading.model_dump()
    payload['zone_id'] = sensor.zone_id
    # GNSS-ready: propagate the sensor's current fix so the worker can persist
    # coordinates and fragment the cooldown lock per-area instead of per-zone.
    payload['latitude'] = sensor.latitude
    payload['longitude'] = sensor.longitude
    if sensor.latitude is not None and sensor.longitude is not None:
        payload['sensor_geohash'] = point_to_geohash(sensor.latitude, sensor.longitude, COOLDOWN_PRECISION)
        
    # --- System Telemetry: End-to-End Latency ---
    if payload.get("device_timestamp_ms"):
        payload["latency_ms"] = int(time.time() * 1000) - payload["device_timestamp_ms"]
    
    # Append to the Redis Streams ingestion bus (O(1)); the worker group drains it.
    await ingest.enqueue_reading(redis_client, json.dumps(payload))
    return {"status": "accepted"}

@app.get("/sensors/{id}/statistics", tags=["Data Retrieval"], dependencies=[Depends(verify_api_key)])
def get_sensor_statistics(id: int, db: Session = Depends(get_db)):
    # Fast path: when TimescaleDB provisioned the continuous aggregate, the
    # dashboard rollups are served from pre-computed buckets instead of a COUNT
    # scan over the hypertable.
    has_aggregate = db.execute(
        text("SELECT to_regclass('public.readings_minute') IS NOT NULL")
    ).scalar()
    if has_aggregate:
        row = db.execute(
            text(
                "SELECT COALESCE(SUM(n), 0) AS total, COALESCE(MAX(peak), 0) AS peak "
                "FROM readings_minute WHERE sensor_id = :sensor_id"
            ),
            {"sensor_id": id},
        ).one()
        return {
            "sensor_id": id,
            "total_readings": row.total,
            "peak_value": row.peak,
        }
    count = db.query(models.Reading).filter(models.Reading.sensor_id == id).count()
    return {
        "sensor_id": id,
        "total_readings": count
    }

@app.get("/readings/", response_model=List[schemas.Reading], tags=["Data Retrieval"], dependencies=[Depends(verify_api_key)])
def get_readings(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    """
    Fetch recent sensor readings. 
    Used primarily by the frontend dashboard to render the live seismograph.
    """
    if skip < 0:
        skip = 0
    limit = min(limit, 1000)
    return db.query(models.Reading).order_by(models.Reading.recorded_at.desc()).offset(skip).limit(limit).all()

@app.get("/zones/{zone_id}/readings", response_model=List[schemas.Reading], tags=["Data Retrieval"], dependencies=[Depends(verify_api_key)])
def get_zone_readings(zone_id: int, limit: int = 60, db: Session = Depends(get_db)):
    """
    Fetch the most recent readings emitted by sensors belonging to a single
    PostGIS zone. Powers the per-zone seismograph on the dashboard: each zone
    renders its own sliding window instead of mixing the whole network.
    """
    zone = db.query(models.Zone).filter(models.Zone.id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ZONE_NOT_FOUND)
    limit = max(1, min(limit, 200))
    return (
        db.query(models.Reading)
        .join(models.Sensor, models.Reading.sensor_id == models.Sensor.id)
        .filter(models.Sensor.zone_id == zone_id)
        .order_by(models.Reading.recorded_at.desc())
        .limit(limit)
        .all()
    )

@app.delete("/zones/{zone_id}/readings", tags=["Data Management"], dependencies=[Depends(verify_api_key)])
def delete_zone_readings(zone_id: int, db: Session = Depends(get_db)):
    """
    Clear the telemetry emitted by sensors belonging to a single PostGIS zone.

    Removes every reading whose sensor is assigned to the given zone so the
    per-zone seismograph can be reset without touching data from other areas.
    Returns the number of deleted readings.
    """
    zone = db.query(models.Zone).filter(models.Zone.id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ZONE_NOT_FOUND)

    sensor_ids = [
        row[0]
        for row in db.query(models.Sensor.id).filter(models.Sensor.zone_id == zone_id).all()
    ]
    deleted = 0
    if sensor_ids:
        deleted = (
            db.query(models.Reading)
            .filter(models.Reading.sensor_id.in_(sensor_ids))
            .delete(synchronize_session=False)
        )
        db.commit()
    return {"deleted": deleted}

@app.get("/zones/{zone_id}/alerts", response_model=List[schemas.Alert], tags=["Data Retrieval"], dependencies=[Depends(verify_api_key)])
def get_zone_alerts(zone_id: int, limit: int = 20, db: Session = Depends(get_db)):
    """
    Retrieve the confirmed seismic alerts raised for a specific PostGIS zone.

    Orders by most recent first so the dashboard can render an area-scoped
    alert history. Returns 404 when the zone does not exist.
    """
    zone = db.query(models.Zone).filter(models.Zone.id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ZONE_NOT_FOUND)
    limit = max(1, min(limit, 100))
    return (
        db.query(models.Alert)
        .filter(models.Alert.zone_id == zone_id)
        .order_by(models.Alert.created_at.desc())
        .limit(limit)
        .all()
    )

@app.get("/reports/{alert_id}", response_model=schemas.EmergencyReport, tags=["Data Retrieval"], dependencies=[Depends(verify_api_key)])
def get_emergency_report(alert_id: int, db: Session = Depends(get_db)):
    """
    Fetch the AI-generated emergency report attached to a confirmed alert.
    Exposes the status state machine (PENDING / COMPLETED / FAILED) so clients can
    render an explicit "AI Report Unavailable" badge instead of hanging.
    """
    report = db.query(models.EmergencyReport).filter(models.EmergencyReport.alert_id == alert_id).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No emergency report found for this alert")
    return report