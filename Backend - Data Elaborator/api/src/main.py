"""
Earthquake Monitoring System API
--------------------------------
Main entry point for the backend application. 
This FastAPI application handles:
1. Management of Zones and IoT Devices (Misurators).
2. Data ingestion from sensors (Misurations).
3. Real-time analysis for seismic alert detection.
"""

import sys
import os

# Ensure the parent directory is in the python path for module resolution
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from fastapi import FastAPI, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from typing import List, Optional
from datetime import datetime, timedelta
from .database import get_db, engine
import models
import schemas

# Initialize Database Schema
models.Base.metadata.create_all(bind=engine)

# --- Configuration Constants ---
# Minimum number of anomalous readings required to trigger an alert
ALERT_THRESHOLD = 10  
# Time window to consider for the alert threshold (sliding window)
ALERT_TIME_WINDOW_SECONDS = 5  

# Define the application instance
app = FastAPI(
    title="Earthquake Monitoring System",
    description="Backend API for managing seismic sensors and detecting anomalies in real-time.",
    version="1.0.0"
)

# ==========================================
# ALERT SYSTEM ENDPOINTS
# ==========================================

@app.get("/alerts/{zone_id}", response_model=schemas.AlertResponse)
def check_earthquake_alert(
    zone_id: int, 
    db: Session = Depends(get_db)
):
    """
    Evaluates seismic activity in a specific zone to detect potential earthquakes.

    Algorithm:
    Counts the number of high-value measurements received from ALL active sensors 
    in the target zone within the last N seconds.

    Args:
        zone_id (int): The ID of the zone to monitor.

    Returns:
        AlertResponse: Object containing boolean detection status and metadata.
    """
    
    # 1. Validate Zone existence
    zone = db.query(models.Zone).filter(models.Zone.id == zone_id).first()
    if zone is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Zone with ID {zone_id} not found."
        )
    
    # 2. Define the time window
    time_threshold = datetime.utcnow() - timedelta(seconds=ALERT_TIME_WINDOW_SECONDS)
    
    # 3. Aggregation Query
    # Efficiently counts records using a JOIN between Misuration and Misurator.
    # Filters by: Zone ID, Time Window, and Active Status of the sensor.
    measurement_count = db.query(func.count(models.Misuration.id))\
        .join(models.Misuration.misurator)\
        .filter(
            models.Misurator.zone_id == zone_id,
            models.Misuration.created_at >= time_threshold,
            models.Misurator.active == True
        ).scalar()
    
    # 4. Threshold Logic
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
# ZONE MANAGEMENT
# ==========================================

@app.get("/zones/", response_model=List[schemas.Zone])
def get_zones(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """Retrieves a paginated list of all registered zones."""
    return db.query(models.Zone).offset(skip).limit(limit).all()

@app.post("/zones/", response_model=schemas.Zone, status_code=status.HTTP_201_CREATED)
def create_zone(
    zone: schemas.ZoneCreate, 
    db: Session = Depends(get_db)
):
    """Registers a new geographical zone."""
    db_zone = models.Zone(**zone.model_dump())
    db.add(db_zone)
    db.commit()
    db.refresh(db_zone)
    return db_zone

@app.get("/zones/{zone_id}", response_model=schemas.Zone)
def get_zone(
    zone_id: int, 
    db: Session = Depends(get_db)
):
    """Retrieves details of a specific zone by ID."""
    zone = db.query(models.Zone).filter(models.Zone.id == zone_id).first()
    if zone is None:
        raise HTTPException(status_code=404, detail="Zone not found")
    return zone

@app.put("/zones/{zone_id}", response_model=schemas.Zone)
def update_zone(
    zone_id: int, 
    zone_update: schemas.ZoneUpdate, 
    db: Session = Depends(get_db)
):
    """Updates the attributes of an existing zone."""
    db_zone = db.query(models.Zone).filter(models.Zone.id == zone_id).first()
    if db_zone is None:
        raise HTTPException(status_code=404, detail="Zone not found")
    
    update_data = zone_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_zone, field, value)
    
    db.commit()
    db.refresh(db_zone)
    return db_zone

@app.delete("/zones/{zone_id}")
def delete_zone(
    zone_id: int, 
    db: Session = Depends(get_db)
):
    """
    Deletes a zone. 
    WARNING: This cascades delete to all associated Misurators and Misurations.
    """
    db_zone = db.query(models.Zone).filter(models.Zone.id == zone_id).first()
    if db_zone is None:
        raise HTTPException(status_code=404, detail="Zone not found")
    
    db.delete(db_zone)
    db.commit()
    return {"message": "Zone deleted successfully"}

# ==========================================
# MISURATOR (SENSOR) MANAGEMENT
# ==========================================

@app.get("/misurators/", response_model=List[schemas.Misurator])
def get_misurators(
    skip: int = 0, 
    limit: int = 100, 
    active: Optional[bool] = None,
    zone_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Retrieves a list of sensors with optional filtering by status or zone."""
    query = db.query(models.Misurator)
    
    if active is not None:
        query = query.filter(models.Misurator.active == active)
    if zone_id is not None:
        query = query.filter(models.Misurator.zone_id == zone_id)
    
    return query.offset(skip).limit(limit).all()

@app.post("/misurators/", response_model=schemas.Misurator, status_code=status.HTTP_201_CREATED)
def create_misurator(
    misurator: schemas.MisuratorCreate, 
    db: Session = Depends(get_db)
):
    """Registers a new sensor device in a specific zone."""
    # Integrity Check: Ensure the referenced zone exists
    zone = db.query(models.Zone).filter(models.Zone.id == misurator.zone_id).first()
    if zone is None:
        raise HTTPException(status_code=400, detail="Referenced Zone ID does not exist")
    
    db_misurator = models.Misurator(**misurator.model_dump())
    db.add(db_misurator)
    db.commit()
    db.refresh(db_misurator)
    return db_misurator

@app.get("/misurators/{misurator_id}", response_model=schemas.Misurator)
def get_misurator(
    misurator_id: int, 
    db: Session = Depends(get_db)
):
    """Retrieves details of a specific sensor."""
    misurator = db.query(models.Misurator).filter(models.Misurator.id == misurator_id).first()
    if misurator is None:
        raise HTTPException(status_code=404, detail="Misurator not found")
    return misurator

@app.put("/misurators/{misurator_id}", response_model=schemas.Misurator)
def update_misurator(
    misurator_id: int, 
    misurator_update: schemas.MisuratorUpdate, 
    db: Session = Depends(get_db)
):
    """Updates sensor configuration (e.g., moving to a new zone)."""
    db_misurator = db.query(models.Misurator).filter(models.Misurator.id == misurator_id).first()
    if db_misurator is None:
        raise HTTPException(status_code=404, detail="Misurator not found")
    
    if misurator_update.zone_id is not None:
        # Validate new zone existence
        zone = db.query(models.Zone).filter(models.Zone.id == misurator_update.zone_id).first()
        if zone is None:
            raise HTTPException(status_code=400, detail="New Zone ID does not exist")
    
    update_data = misurator_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_misurator, field, value)
    
    db.commit()
    db.refresh(db_misurator)
    return db_misurator

@app.put("/misurators/{misurator_id}/activate")
def activate_misurator(misurator_id: int, db: Session = Depends(get_db)):
    """Sets a sensor status to Active."""
    misurator = db.query(models.Misurator).filter(models.Misurator.id == misurator_id).first()
    if misurator is None:
        raise HTTPException(status_code=404, detail="Misurator not found")
    
    misurator.active = True
    db.commit()
    return {"message": "Misurator activated successfully"}

@app.put("/misurators/{misurator_id}/deactivate")
def deactivate_misurator(misurator_id: int, db: Session = Depends(get_db)):
    """Sets a sensor status to Inactive (data will be ignored in alerts)."""
    misurator = db.query(models.Misurator).filter(models.Misurator.id == misurator_id).first()
    if misurator is None:
        raise HTTPException(status_code=404, detail="Misurator not found")
    
    misurator.active = False
    db.commit()
    return {"message": "Misurator deactivated successfully"}

# ==========================================
# MISURATIONS (DATA INGESTION)
# ==========================================

@app.get("/misurations/", response_model=List[schemas.Misuration])
def get_misurations(
    skip: int = 0, 
    limit: int = 100, 
    misurator_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """Retrieves historical data with optional time-range and device filtering."""
    query = db.query(models.Misuration)
    
    if misurator_id is not None:
        query = query.filter(models.Misuration.misurator_id == misurator_id)
    if start_date is not None:
        query = query.filter(models.Misuration.created_at >= start_date)
    if end_date is not None:
        query = query.filter(models.Misuration.created_at <= end_date)
    
    return query.order_by(models.Misuration.created_at.desc()).offset(skip).limit(limit).all()

@app.post("/misurations/", response_model=schemas.Misuration, status_code=status.HTTP_201_CREATED)
def create_misuration(
    misuration: schemas.MisurationCreate, 
    db: Session = Depends(get_db)
):
    """
    Ingests a new data point from a sensor.
    Validation: Rejects data from non-existent or inactive sensors.
    """
    misurator = db.query(models.Misurator).filter(models.Misurator.id == misuration.misurator_id).first()
    
    if misurator is None:
        raise HTTPException(status_code=400, detail="Misurator ID not found")
    if not misurator.active:
        raise HTTPException(status_code=400, detail="Cannot accept data from an inactive Misurator")
    
    db_misuration = models.Misuration(**misuration.model_dump())
    db.add(db_misuration)
    db.commit()
    db.refresh(db_misuration)
    return db_misuration

@app.get("/misurations/{misuration_id}", response_model=schemas.Misuration)
def get_misuration(
    misuration_id: int, 
    db: Session = Depends(get_db)
):
    """Retrieves a single data point by ID."""
    misuration = db.query(models.Misuration).filter(models.Misuration.id == misuration_id).first()
    if misuration is None:
        raise HTTPException(status_code=404, detail="Misuration not found")
    return misuration

# ==========================================
# RELATIONSHIP & STATISTICS ENDPOINTS
# ==========================================

@app.get("/zones/{zone_id}/misurators", response_model=List[schemas.Misurator])
def get_zone_misurators(zone_id: int, db: Session = Depends(get_db)):
    """Returns all sensors installed in a specific zone."""
    zone = db.query(models.Zone).filter(models.Zone.id == zone_id).first()
    if zone is None:
        raise HTTPException(status_code=404, detail="Zone not found")
    return zone.misurators # Uses SQLAlchemy relationship

@app.get("/misurators/{misurator_id}/misurations", response_model=List[schemas.Misuration])
def get_misurator_misurations(
    misurator_id: int, 
    hours: int = Query(24, description="Lookback period in hours"),
    db: Session = Depends(get_db)
):
    """Returns recent data points for a specific sensor."""
    misurator = db.query(models.Misurator).filter(models.Misurator.id == misurator_id).first()
    if misurator is None:
        raise HTTPException(status_code=404, detail="Misurator not found")
    
    since_time = datetime.now() - timedelta(hours=hours)
    
    # Utilizing relationship filtering could be an alternative, but direct query is explicit here
    return db.query(models.Misuration).filter(
        models.Misuration.misurator_id == misurator_id,
        models.Misuration.created_at >= since_time
    ).order_by(models.Misuration.created_at.desc()).all()

@app.get("/stats/zones")
def get_zones_stats(db: Session = Depends(get_db)):
    """
    Computes aggregated statistics for all zones.
    Returns counts of devices and timestamp of the last received data packet.
    """
    zones = db.query(models.Zone).all()
    stats = []
    
    for zone in zones:
        # Utilizing relationships for cleaner counts
        total_misurators = len(zone.misurators)
        active_misurators = sum(1 for m in zone.misurators if m.active)
        
        # Optimize: Get only the latest misuration via join
        last_misuration = db.query(models.Misuration)\
            .join(models.Misurator)\
            .filter(models.Misurator.zone_id == zone.id)\
            .order_by(models.Misuration.created_at.desc())\
            .first()
        
        stats.append({
            "zone_id": zone.id,
            "city": zone.city,
            "active_misurators": active_misurators,
            "total_misurators": total_misurators,
            "last_misuration": last_misuration.created_at if last_misuration else None
        })
    
    return stats

@app.get("/stats/misurators/{misurator_id}")
def get_misurator_stats(
    misurator_id: int,
    days: int = Query(7, description="Lookback period in days"),
    db: Session = Depends(get_db)
):
    """
    Computes statistical metrics (Min, Max, Avg) for a sensor over a given period.
    """
    misurator = db.query(models.Misurator).filter(models.Misurator.id == misurator_id).first()
    if misurator is None:
        raise HTTPException(status_code=404, detail="Misurator not found")
    
    since_date = datetime.now() - timedelta(days=days)
    misurations = db.query(models.Misuration).filter(
        models.Misuration.misurator_id == misurator_id,
        models.Misuration.created_at >= since_date
    ).all()
    
    if not misurations:
        return {
            "misurator_id": misurator_id,
            "total_misurations": 0,
            "avg_value": None,
            "min_value": None,
            "max_value": None
        }
    
    values = [m.value for m in misurations]
    
    return {
        "misurator_id": misurator_id,
        "total_misurations": len(misurations),
        "avg_value": sum(values) / len(values),
        "min_value": min(values),
        "max_value": max(values),
        "period_days": days
    }

# ==========================================
# SYSTEM HEALTH CHECKS
# ==========================================

@app.get("/")
def read_root():
    """Root endpoint providing API version and map."""
    return {
        "message": "Earthquake Monitoring System API",
        "version": "1.0.0",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    """
    Performs a deep health check ensuring Database connectivity.
    Used by container orchestrators (e.g., Docker/K8s) to verify availability.
    """
    try:
        # Lightweight query to verify DB connection
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database connection failed: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)