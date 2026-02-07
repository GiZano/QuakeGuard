"""
QuakeGuard Backend Service API
-------------------------------
Orchestrates IoT data ingestion, system health monitoring, and data retrieval.
Implements robust error handling for cryptographic verification (SHA256, DER/RAW).
"""

import json
import asyncio
import time
import hashlib  
from datetime import datetime
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, text
from sqlalchemy.exc import OperationalError
from redis import asyncio as aioredis

# --- CRYPTO IMPORTS ---
from ecdsa import VerifyingKey, NIST256p, BadSignatureError
from ecdsa.errors import MalformedPointError
from ecdsa.util import sigdecode_der, sigdecode_string 

from geoalchemy2.elements import WKTElement

# Local imports
from src.database import get_db, engine
import src.models as models
import src.schemas as schemas

# ==========================================
# DATABASE INITIALIZATION & WAITER
# ==========================================

def wait_for_db(retries=10, delay=3):
    """
    Blocks startup until the Database is ready to accept connections.
    """
    print("Checking Database connection...")
    for i in range(retries):
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            print("✅ Database is up and running!")
            return
        except OperationalError:
            print(f"⏳ Database not ready yet... waiting {delay}s ({i+1}/{retries})")
            time.sleep(delay)
    
    raise Exception("❌ Could not connect to Database after multiple retries.")

# 1. Wait for DB
wait_for_db()

# 2. Create Tables
models.Base.metadata.create_all(bind=engine)


# Initialize FastAPI
app = FastAPI(
    title="Q Backend Service",
    description="Core API for Earthquake Alarm System: Ingestion, Alerts, and Statistics.",
    version="1.7.0"
)

# Initialize Redis
redis_client = aioredis.from_url("redis://redis:6379/0", decode_responses=True)


# --- UTILITY FUNCTIONS ---

def verify_device_signature(public_key_hex: str, message: str, signature_hex: str) -> bool:
    """
    Verifies ECDSA signature using SHA256 hashing.
    Compatible with ESP32 MbedTLS (DER) and Standard Python (RAW).
    """
    try:
        if not public_key_hex or not signature_hex:
            return False
            
        key_bytes = bytes.fromhex(public_key_hex)
        sig_bytes = bytes.fromhex(signature_hex)
        message_bytes = message.encode('utf-8')

        # 1. Load the Key (Try DER first - ESP32 Standard, fallback to RAW)
        try:
            vk = VerifyingKey.from_der(key_bytes)
        except (ValueError, MalformedPointError):
            vk = VerifyingKey.from_string(key_bytes, curve=NIST256p)
        
        # 2. Verify with SHA256 (CRITICAL: Matches ESP32's mbedtls_md_info_from_type(SHA256))
        try:
            # Try DER (ASN.1) first
            return vk.verify(sig_bytes, message_bytes, sigdecode=sigdecode_der, hashfunc=hashlib.sha256)
        except BadSignatureError:
            # Fallback to RAW string signature
            try:
                return vk.verify(sig_bytes, message_bytes, sigdecode=sigdecode_string, hashfunc=hashlib.sha256)
            except BadSignatureError:
                return False

    except Exception as e:
        print(f"⚠️ Crypto Validation Error: {str(e)}")
        return False


# ==========================================
# REGISTRATION ENDPOINTS
# ==========================================

@app.post("/zones/", response_model=schemas.Zone, status_code=status.HTTP_201_CREATED, tags=["Registration"])
def create_zone(zone: schemas.ZoneCreate, db: Session = Depends(get_db)):
    """Registers a new geographical zone."""
    existing = db.query(models.Zone).filter(models.Zone.city == zone.city).first()
    if existing:
        return existing 
    db_zone = models.Zone(city=zone.city)
    db.add(db_zone)
    db.commit()
    db.refresh(db_zone)
    return db_zone

@app.get("/zones/", response_model=List[schemas.Zone], tags=["Data Retrieval"])
def get_zones(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    List all available geographical zones.
    Useful for frontend dropdowns or sensor configuration.
    """
    return db.query(models.Zone).offset(skip).limit(limit).all()


@app.post("/misurators/", response_model=schemas.Misurator, status_code=status.HTTP_201_CREATED, tags=["Registration"])
def create_misurator(misurator: schemas.MisuratorCreate, db: Session = Depends(get_db)):
    """Registers a new IoT Sensor and its Public Key."""
    # Check if key needs update (for Dev convenience)
    # Note: In prod, you might query by public_key or hardware_id, here we simplify.
    existing = db.query(models.Misurator).filter(models.Misurator.public_key_hex == misurator.public_key_hex).first()
    if existing:
        return existing

    zone = db.query(models.Zone).filter(models.Zone.id == misurator.zone_id).first()
    if zone is None:
        raise HTTPException(status_code=404, detail="Zone not found")
    
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
    """List all registered sensors."""
    return db.query(models.Misurator).offset(skip).limit(limit).all()


# ==========================================
# INGESTION ENDPOINT
# ==========================================

@app.post("/misurations/", status_code=status.HTTP_202_ACCEPTED, tags=["Ingestion"])
async def create_misuration_async(
    misuration: schemas.MisurationCreate, 
    db: Session = Depends(get_db)
):
    """
    Receives data, verifies signature (SHA256), and queues to Redis.
    """
    misurator = db.query(models.Misurator).filter(models.Misurator.id == misuration.misurator_id).first()
    
    if not misurator or not misurator.active:
        raise HTTPException(status_code=403, detail="Sensor unauthorized or inactive")

    # CRITICAL: Reconstruct message as "value:int(timestamp)" to match ESP32
    message = f"{misuration.value}:{int(misuration.device_timestamp)}"
    
    loop = asyncio.get_event_loop()
    is_valid = await loop.run_in_executor(
        None, 
        verify_device_signature, 
        misurator.public_key_hex, 
        message, 
        misuration.signature_hex
    )

    if not is_valid:
        print(f"\n❌ SIGNATURE FAILED for Sensor {misurator.id}")
        print(f"Expected Message: {message}")
        print(f"Stored Key: {misurator.public_key_hex[:15]}...")
        print(f"Received Sig: {misuration.signature_hex[:15]}...\n")
        raise HTTPException(status_code=401, detail="Invalid digital signature")

    # Prepare payload for Worker
    payload = misuration.model_dump()
    payload['zone_id'] = misurator.zone_id 
    
    await redis_client.lpush("seismic_events", json.dumps(payload))
    
    return {"status": "accepted", "detail": "Data enqueued"}


# ==========================================
# STATISTICS & ALERTS ENDPOINTS (RESTORED)
# ==========================================

@app.get("/zones/{zone_id}/alerts", response_model=List[schemas.AlertResponse], tags=["Data Retrieval"])
def get_zone_alerts(
    zone_id: int, 
    limit: int = 10, 
    db: Session = Depends(get_db)
):
    """
    Retrieves recent seismic alerts for a specific zone.
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
    Computes statistical aggregates (AVG, MAX, MIN, COUNT) for a sensor.
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


# ==========================================
# SYSTEM HEALTH 
# ==========================================

@app.get("/health", tags=["System"])
async def health_check(db: Session = Depends(get_db)):
    """
    Checks connection status for Database and Redis.
    """
    health_status: Dict[str, Any] = {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "database": "unknown",
            "redis": "unknown"
        }
    }

    # 1. Check DB
    try:
        db.execute(func.now()) 
        health_status["services"]["database"] = "connected"
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["services"]["database"] = f"error: {str(e)}"

    # 2. Check Redis
    try:
        await redis_client.ping()
        health_status["services"]["redis"] = "connected"
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["services"]["redis"] = f"error: {str(e)}"

    if health_status["status"] != "ok":
        raise HTTPException(status_code=503, detail=health_status)

    return health_status