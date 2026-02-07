"""
QuakeGuard Backend Service API
-------------------------------
Orchestrates IoT data ingestion, system health monitoring, and data retrieval.
Implements asynchronous request handling, ECDSA signature verification,
and statistical aggregation for seismic analysis.
"""

import json
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from redis import asyncio as aioredis
from ecdsa import VerifyingKey, NIST256p, BadSignatureError
from geoalchemy2.elements import WKTElement  # Essential for PostGIS

# Local imports
# KEY FIX: We import 'engine' to initialize the database tables
from src.database import get_db, engine
import src.models as models
import src.schemas as schemas

# ==========================================
# DATABASE INITIALIZATION (The Fix)
# ==========================================
# This command creates the tables (zones, misurators, alerts, etc.) 
# if they do not exist in the database.
models.Base.metadata.create_all(bind=engine)


# Initialize FastAPI with metadata
app = FastAPI(
    title="QuakeGuard Backend Service",
    description="Core API for Earthquake Alarm System: Ingestion, Alerts, and Statistics.",
    version="1.3.0"
)

# Initialize asynchronous Redis client
# Note: Ensure the Redis URL matches your Docker Compose service name
redis_client = aioredis.from_url("redis://redis:6379/0", decode_responses=True)


# --- UTILITY FUNCTIONS ---

def verify_device_signature(public_key_hex: str, message: str, signature_hex: str) -> bool:
    """
    Verifies the ECDSA signature sent by the IoT device.
    This is a CPU-bound operation and should be offloaded to an executor in async contexts.
    
    Args:
        public_key_hex (str): The device's public key in hexadecimal format.
        message (str): The original message string (value:timestamp).
        signature_hex (str): The signature to verify.

    Returns:
        bool: True if signature is valid, False otherwise.
    """
    try:
        vk = VerifyingKey.from_string(bytes.fromhex(public_key_hex), curve=NIST256p)
        return vk.verify(bytes.fromhex(signature_hex), message.encode())
    except (BadSignatureError, ValueError):
        return False


# ==========================================
# REGISTRATION ENDPOINTS (Admin / Setup)
# ==========================================

@app.post("/zones/", response_model=schemas.Zone, status_code=status.HTTP_201_CREATED, tags=["Registration"])
def create_zone(zone: schemas.ZoneCreate, db: Session = Depends(get_db)):
    """
    Registers a new geographical zone.
    Essential step before registering any sensors.
    """
    # Check if a zone with the same city name already exists to avoid duplicates
    existing_zone = db.query(models.Zone).filter(models.Zone.city == zone.city).first()
    if existing_zone:
        return existing_zone 
        
    db_zone = models.Zone(city=zone.city)
    db.add(db_zone)
    db.commit()
    db.refresh(db_zone)
    return db_zone


@app.post("/misurators/", response_model=schemas.Misurator, status_code=status.HTTP_201_CREATED, tags=["Registration"])
def create_misurator(misurator: schemas.MisuratorCreate, db: Session = Depends(get_db)):
    """
    Registers a new IoT Sensor (Misurator) and its Public Key.
    Converts lat/lon coordinates into a PostGIS Geometry point.
    """
    # Verify zone existence
    zone = db.query(models.Zone).filter(models.Zone.id == misurator.zone_id).first()
    if zone is None:
        raise HTTPException(status_code=404, detail="Zone not found")
    
    # Construct GPS point for PostGIS (WKT format: "POINT(lon lat)")
    gps_point = f"POINT({misurator.longitude} {misurator.latitude})"
    
    db_misurator = models.Misurator(
        active=misurator.active,
        zone_id=misurator.zone_id,
        latitude=misurator.latitude,
        longitude=misurator.longitude,
        location=WKTElement(gps_point, srid=4326),
        public_key_hex=misurator.public_key_hex
    )
    
    db.add(db_misurator)
    db.commit()
    db.refresh(db_misurator)
    return db_misurator


@app.get("/misurators/", response_model=List[schemas.Misurator], tags=["Data Retrieval"])
def get_misurators(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    List all registered sensors. 
    Useful for debugging and administrative dashboards.
    """
    return db.query(models.Misurator).offset(skip).limit(limit).all()


# --- INGESTION ENDPOINTS ---

@app.post("/misurations/", status_code=status.HTTP_202_ACCEPTED, tags=["Ingestion"])
async def create_misuration_async(
    misuration: schemas.MisurationCreate, 
    db: Session = Depends(get_db)
):
    """
    Asynchronously handles incoming seismic data from IoT devices.
    Validates identity via ECDSA and queues data to Redis.
    """
    # Fetch misurator metadata
    # Optimization: Consider caching this in Redis for production
    misurator = db.query(models.Misurator).filter(models.Misurator.id == misuration.misurator_id).first()
    
    if not misurator or not misurator.active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Sensor is unauthorized or inactive"
        )

    # Offload CPU-bound signature verification
    loop = asyncio.get_event_loop()
    message = f"{misuration.value}:{misuration.device_timestamp}"
    
    is_valid = await loop.run_in_executor(
        None, 
        verify_device_signature, 
        misurator.public_key_hex, 
        message, 
        misuration.signature_hex
    )

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid digital signature"
        )

    # Prepare payload for the background worker
    payload = misuration.model_dump()
    payload['zone_id'] = misurator.zone_id 
    
    # Enqueue data into Redis
    await redis_client.lpush("seismic_events", json.dumps(payload))
    
    return {"status": "accepted", "detail": "Data enqueued for background processing"}


# --- DATA RETRIEVAL & ALERTS ENDPOINTS ---

@app.get("/zones/{zone_id}/alerts", response_model=List[schemas.AlertResponse], tags=["Data Retrieval"])
def get_zone_alerts(
    zone_id: int, 
    limit: int = 10, 
    db: Session = Depends(get_db)
):
    """
    Retrieves recent seismic alerts for a specific geographical zone.
    """
    alerts = db.query(models.Alert)\
        .filter(models.Alert.zone_id == zone_id)\
        .order_by(desc(models.Alert.timestamp))\
        .limit(limit)\
        .all()
        
    return alerts if alerts else []


@app.get("/sensors/{misurator_id}/statistics", tags=["Analytics"])
def get_sensor_statistics(
    misurator_id: int, 
    db: Session = Depends(get_db)
):
    """
    Computes and retrieves statistical aggregates for a specific sensor.
    """
    sensor = db.query(models.Misurator).filter(models.Misurator.id == misurator_id).first()
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")

    stats = db.query(
        func.count(models.Misuration.id).label("count"),
        func.avg(models.Misuration.value).label("average"),
        func.max(models.Misuration.value).label("max_value"),
        func.min(models.Misuration.value).label("min_value")
    ).filter(models.Misuration.misurator_id == misurator_id).first()

    return {
        "misurator_id": misurator_id,
        "total_readings": stats.count,
        "average_value": round(stats.average, 2) if stats.average else 0.0,
        "max_recorded": stats.max_value,
        "min_recorded": stats.min_value,
        "generated_at": datetime.utcnow().isoformat()
    }


# --- SYSTEM HEALTH ENDPOINTS ---

@app.get("/health", tags=["System"])
async def health_check(db: Session = Depends(get_db)):
    """
    Performs a comprehensive health check (DB + Redis).
    """
    health_status: Dict[str, Any] = {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {"database": "unknown", "redis": "unknown"}
    }

    # Check DB
    try:
        db.execute(func.now()) 
        health_status["services"]["database"] = "connected"
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["services"]["database"] = f"error: {str(e)}"

    # Check Redis
    try:
        await redis_client.ping()
        health_status["services"]["redis"] = "connected"
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["services"]["redis"] = f"error: {str(e)}"

    if health_status["status"] != "ok":
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=health_status)

    return health_status