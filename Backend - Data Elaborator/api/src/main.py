"""
Earthquake Monitoring System API
--------------------------------
Main entry point. 
Handles Data Ingestion with ECDSA Signature Verification to prevent DOS/Spoofing.
"""

import sys
import os
import time

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from fastapi import FastAPI, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from typing import List, Optional
from datetime import datetime, timedelta
from geoalchemy2.elements import WKTElement 
from ecdsa import VerifyingKey, NIST256p, BadSignatureError

from src.database import get_db, engine
import src.models as models
import src.schemas as schemas

# Initialize Database Schema
models.Base.metadata.create_all(bind=engine)

# --- Configuration Constants ---
ALERT_THRESHOLD = 10  
ALERT_TIME_WINDOW_SECONDS = 5
MAX_TIMESTAMP_DRIFT_SECONDS = 60 # Prevent replay attacks older than 60s

app = FastAPI(
    title="Earthquake Monitoring System",
    description="Backend API with ECDSA Security and PostGIS support.",
    version="1.2.0"
)

# ==========================================
# SECURITY UTILITIES
# ==========================================

def verify_device_signature(public_key_hex: str, message: str, signature_hex: str) -> bool:
    """
    Verifies the ECDSA signature of a message using the device's public key.
    Curve: NIST256p (secp256r1)
    """
    try:
        # Import the public key from Hex
        vk = VerifyingKey.from_string(bytes.fromhex(public_key_hex), curve=NIST256p)
        # Verify the signature (decoding signature from Hex first)
        return vk.verify(bytes.fromhex(signature_hex), message.encode('utf-8'))
    except (BadSignatureError, ValueError):
        return False
    except Exception as e:
        print(f"[SECURITY ERROR] Signature verification failed: {e}")
        return False

# ==========================================
# MISURATORS (SENSORS) + REGISTRATION
# ==========================================

@app.post("/misurators/", response_model=schemas.Misurator, status_code=status.HTTP_201_CREATED)
def create_misurator(misurator: schemas.MisuratorCreate, db: Session = Depends(get_db)):
    """
    Registers a new sensor.
    Stores the ECDSA Public Key for future authentication.
    """
    zone = db.query(models.Zone).filter(models.Zone.id == misurator.zone_id).first()
    if zone is None:
        raise HTTPException(status_code=400, detail="Referenced Zone ID does not exist")
    
    # Construct WKT for PostGIS
    gps_point = f"POINT({misurator.longitude} {misurator.latitude})"
    
    db_misurator = models.Misurator(
        active=misurator.active,
        zone_id=misurator.zone_id,
        latitude=misurator.latitude,
        longitude=misurator.longitude,
        location=WKTElement(gps_point, srid=4326),
        public_key_hex=misurator.public_key_hex # Store key
    )
    
    db.add(db_misurator)
    db.commit()
    db.refresh(db_misurator)
    return db_misurator

@app.get("/misurators/", response_model=List[schemas.Misurator])
def get_misurators(
    skip: int = 0, 
    limit: int = 100, 
    active: Optional[bool] = None,
    zone_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Misurator)
    if active is not None:
        query = query.filter(models.Misurator.active == active)
    if zone_id is not None:
        query = query.filter(models.Misurator.zone_id == zone_id)
    return query.offset(skip).limit(limit).all()

# ==========================================
# MISURATIONS (SECURE DATA INGESTION)
# ==========================================

@app.post("/misurations/", response_model=schemas.Misuration, status_code=status.HTTP_201_CREATED)
def create_misuration(misuration: schemas.MisurationCreate, db: Session = Depends(get_db)):
    """
    Ingests data securely.
    1. Checks if Misurator exists and is active.
    2. Validates timestamp to prevent Replay Attacks.
    3. Verifies ECDSA signature using the stored Public Key.
    """
    
    # 1. Fetch Misurator
    misurator = db.query(models.Misurator).filter(models.Misurator.id == misuration.misurator_id).first()
    if misurator is None:
        raise HTTPException(status_code=400, detail="Misurator ID not found")
    if not misurator.active:
        raise HTTPException(status_code=400, detail="Misurator is inactive")
    if not misurator.public_key_hex:
        raise HTTPException(status_code=403, detail="Security Error: This device has no Public Key registered.")

    # 2. Check for Replay Attacks (Timestamp drift)
    # We allow a small drift (e.g., 60 seconds) between device time and server time
    server_time = time.time()
    if abs(server_time - misuration.device_timestamp) > MAX_TIMESTAMP_DRIFT_SECONDS:
         raise HTTPException(
             status_code=403, 
             detail=f"Security Error: Timestamp out of sync (Server: {server_time}, Device: {misuration.device_timestamp}). Potential replay attack."
         )

    # 3. Verify Signature
    # The message format MUST match exactly what the ESP32 signs: "value:timestamp"
    # Note: Ensure the timestamp precision (float vs int) matches exactly on both sides.
    # It is recommended to cast timestamp to int or fixed string on ESP32.
    message_to_verify = f"{misuration.value}:{misuration.device_timestamp}"
    
    is_valid = verify_device_signature(
        public_key_hex=misurator.public_key_hex,
        message=message_to_verify,
        signature_hex=misuration.signature_hex
    )

    if not is_valid:
        print(f"FAILED SIG: Msg='{message_to_verify}', Sig='{misuration.signature_hex}', Key='{misurator.public_key_hex}'")
        raise HTTPException(status_code=401, detail="Security Error: Invalid Digital Signature. Data integrity check failed.")

    # 4. Save Data (Signature is valid)
    db_misuration = models.Misuration(
        value=misuration.value,
        misurator_id=misuration.misurator_id
        # We don't save the signature itself, we just verified it.
    )
    db.add(db_misuration)
    db.commit()
    db.refresh(db_misuration)
    return db_misuration

@app.get("/misurations/", response_model=List[schemas.Misuration])
def get_misurations(
    skip: int = 0, 
    limit: int = 100, 
    misurator_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Misuration)
    if misurator_id is not None:
        query = query.filter(models.Misuration.misurator_id == misurator_id)
    return query.order_by(models.Misuration.created_at.desc()).offset(skip).limit(limit).all()

# ==========================================
# ALERT SYSTEM (Optimized)
# ==========================================

@app.get("/alerts/{zone_id}", response_model=schemas.AlertResponse)
def check_earthquake_alert(zone_id: int, db: Session = Depends(get_db)):
    """Checks for seismic activity in the specified zone."""
    zone = db.query(models.Zone).filter(models.Zone.id == zone_id).first()
    if zone is None:
        raise HTTPException(status_code=404, detail="Zone not found")
    
    time_threshold = datetime.utcnow() - timedelta(seconds=ALERT_TIME_WINDOW_SECONDS)
    
    measurement_count = db.query(func.count(models.Misuration.id))\
        .join(models.Misuration.misurator)\
        .filter(
            models.Misurator.zone_id == zone_id,
            models.Misuration.created_at >= time_threshold,
            models.Misurator.active == True
        ).scalar()
    
    is_earthquake_detected = measurement_count >= ALERT_THRESHOLD
    
    return schemas.AlertResponse(
        zone_id=zone_id,
        is_earthquake_detected=is_earthquake_detected,
        measurement_count=measurement_count,
        threshold=ALERT_THRESHOLD,
        time_window_seconds=ALERT_TIME_WINDOW_SECONDS,
        timestamp=datetime.utcnow()
    )

# ==========================================
# ZONES & HEALTH
# ==========================================

@app.get("/zones/", response_model=List[schemas.Zone])
def get_zones(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.Zone).offset(skip).limit(limit).all()

@app.post("/zones/", response_model=schemas.Zone, status_code=status.HTTP_201_CREATED)
def create_zone(zone: schemas.ZoneCreate, db: Session = Depends(get_db)):
    db_zone = models.Zone(**zone.model_dump())
    db.add(db_zone)
    db.commit()
    db.refresh(db_zone)
    return db_zone

@app.get("/zones/{zone_id}", response_model=schemas.Zone)
def get_zone(zone_id: int, db: Session = Depends(get_db)):
    zone = db.query(models.Zone).filter(models.Zone.id == zone_id).first()
    if zone is None:
        raise HTTPException(status_code=404, detail="Zone not found")
    return zone

@app.get("/")
def read_root():
    return {"message": "Earthquake Monitoring System API", "version": "1.2.0"}

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected", "timestamp": datetime.now()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)