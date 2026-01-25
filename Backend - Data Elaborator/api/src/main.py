"""
Earthquake Monitoring System API
--------------------------------
Main entry point. Handles GPS data ingestion via PostGIS.
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from fastapi import FastAPI, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from typing import List, Optional
from datetime import datetime, timedelta
from geoalchemy2.elements import WKTElement # Required for PostGIS insertions

from src.database import get_db, engine
import src.models as models
import src.schemas as schemas

# Initialize Database Schema
models.Base.metadata.create_all(bind=engine)

# --- Configuration Constants ---
ALERT_THRESHOLD = 10  
ALERT_TIME_WINDOW_SECONDS = 5  

app = FastAPI(
    title="Earthquake Monitoring System",
    description="Backend API with PostGIS support for seismic monitoring.",
    version="1.1.0"
)

# ==========================================
# ALERT SYSTEM
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
# ZONES
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

@app.delete("/zones/{zone_id}")
def delete_zone(zone_id: int, db: Session = Depends(get_db)):
    db_zone = db.query(models.Zone).filter(models.Zone.id == zone_id).first()
    if db_zone is None:
        raise HTTPException(status_code=404, detail="Zone not found")
    db.delete(db_zone)
    db.commit()
    return {"message": "Zone deleted successfully"}

# ==========================================
# MISURATORS (SENSORS) + GPS
# ==========================================

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

@app.post("/misurators/", response_model=schemas.Misurator, status_code=status.HTTP_201_CREATED)
def create_misurator(misurator: schemas.MisuratorCreate, db: Session = Depends(get_db)):
    """
    Registers a new sensor.
    Converts lat/lon inputs into a PostGIS Geometry Point (SRID 4326).
    """
    zone = db.query(models.Zone).filter(models.Zone.id == misurator.zone_id).first()
    if zone is None:
        raise HTTPException(status_code=400, detail="Referenced Zone ID does not exist")
    
    # Construct WKT (Well-Known Text) for PostGIS: POINT(longitude latitude)
    # Note: PostGIS uses X (Lon), Y (Lat) order.
    gps_point = f"POINT({misurator.longitude} {misurator.latitude})"
    
    db_misurator = models.Misurator(
        active=misurator.active,
        zone_id=misurator.zone_id,
        latitude=misurator.latitude,   # Stored as simple float
        longitude=misurator.longitude, # Stored as simple float
        location=WKTElement(gps_point, srid=4326) # Stored as Geometry
    )
    
    db.add(db_misurator)
    db.commit()
    db.refresh(db_misurator)
    return db_misurator

@app.get("/misurators/{misurator_id}", response_model=schemas.Misurator)
def get_misurator(misurator_id: int, db: Session = Depends(get_db)):
    misurator = db.query(models.Misurator).filter(models.Misurator.id == misurator_id).first()
    if misurator is None:
        raise HTTPException(status_code=404, detail="Misurator not found")
    return misurator

@app.put("/misurators/{misurator_id}/activate")
def activate_misurator(misurator_id: int, db: Session = Depends(get_db)):
    misurator = db.query(models.Misurator).filter(models.Misurator.id == misurator_id).first()
    if misurator is None:
        raise HTTPException(status_code=404, detail="Misurator not found")
    misurator.active = True
    db.commit()
    return {"message": "Misurator activated"}

@app.put("/misurators/{misurator_id}/deactivate")
def deactivate_misurator(misurator_id: int, db: Session = Depends(get_db)):
    misurator = db.query(models.Misurator).filter(models.Misurator.id == misurator_id).first()
    if misurator is None:
        raise HTTPException(status_code=404, detail="Misurator not found")
    misurator.active = False
    db.commit()
    return {"message": "Misurator deactivated"}

# ==========================================
# MISURATIONS (DATA)
# ==========================================

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

@app.post("/misurations/", response_model=schemas.Misuration, status_code=status.HTTP_201_CREATED)
def create_misuration(misuration: schemas.MisurationCreate, db: Session = Depends(get_db)):
    misurator = db.query(models.Misurator).filter(models.Misurator.id == misuration.misurator_id).first()
    if misurator is None:
        raise HTTPException(status_code=400, detail="Misurator ID not found")
    if not misurator.active:
        raise HTTPException(status_code=400, detail="Misurator is inactive")
    
    db_misuration = models.Misuration(**misuration.model_dump())
    db.add(db_misuration)
    db.commit()
    db.refresh(db_misuration)
    return db_misuration

# ==========================================
# HEALTH & ROOT
# ==========================================

@app.get("/")
def read_root():
    return {"message": "Earthquake Monitoring System API", "version": "1.1.0"}

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