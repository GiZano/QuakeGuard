### Importing Modules ###

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from fastapi import FastAPI, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from datetime import datetime, timedelta
from .database import get_db, engine
import models
import schemas

# Create tables if they don't exist
models.Base.metadata.create_all(bind=engine)

# Define the app
app = FastAPI(
    title="Earthquake Monitoring System",
    description="API to manage zones, misurators and alert_misurations",
    version="1.0.0"
)

### Zone endpoints ###

# Get all zones
@app.get("/zones/", response_model=List[schemas.Zone])
def get_zones(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """
    Get all zones

    Parameters:
    - N/A

    Returns:
    - List of all zones
    """
    zones = db.query(models.Zone).offset(skip).limit(limit).all()
    return zones

# Create a new zone
@app.post("/zones/", response_model=schemas.Zone, status_code=status.HTTP_201_CREATED)
def create_zone(
    zone: schemas.ZoneCreate, 
    db: Session = Depends(get_db)
):
    """
    Create a new zone

    Parameters:
    - City

    Returns:
    - Newly Created Zone
    """
    db_zone = models.Zone(**zone.model_dump())
    db.add(db_zone)
    db.commit()
    db.refresh(db_zone)
    return db_zone

# Get specific zone by id
@app.get("/zones/{zone_id}", response_model=schemas.Zone)
def get_zone(
    zone_id: int, 
    db: Session = Depends(get_db)
):
    """
    Get a specific zone by id

    Parameters
    - Zone ID

    Returns
    - Single Zone
    """
    zone = db.query(models.Zone).filter(models.Zone.id == zone_id).first()
    if zone is None:
        raise HTTPException(
            status_code=404, 
            detail="Zone Not Found"
        )
    return zone

# Update Zone
@app.put("/zones/{zone_id}", response_model=schemas.Zone)
def update_zone(
    zone_id: int, 
    zone_update: schemas.ZoneUpdate, 
    db: Session = Depends(get_db)
):
    """
    Update a zone by id

    Parameters:
    - Zone ID
    - City

    Returns:
    - Updated Zone
    """

    db_zone = db.query(models.Zone).filter(models.Zone.id == zone_id).first()
    if db_zone is None:
        raise HTTPException(
            status_code=404, 
            detail="Zone Not Found"
        )
    
    # Update only given fields
    update_data = zone_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_zone, field, value)
    
    db.commit()
    db.refresh(db_zone)
    return db_zone

# Delete Zone
@app.delete("/zones/{zone_id}")
def delete_zone(
    zone_id: int, 
    db: Session = Depends(get_db)
):
    """
    Delete a Zone

    Parameters:
    - Zone ID
    
    Returns:
    - Succesfulness msg
    """

    db_zone = db.query(models.Zone).filter(models.Zone.id == zone_id).first()
    if db_zone is None:
        raise HTTPException(
            status_code=404, 
            detail="Zone Not Found"
        )
    
    db.delete(db_zone)
    db.commit()
    return {"message": "Zone eliminated succesfully!"}

### Misurators endpoints ###

# Get all misurators
@app.get("/misurators/", response_model=List[schemas.Misurator])
def get_misurators(
    skip: int = 0, 
    limit: int = 100, 
    active: Optional[bool] = None,
    zone_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Get all misurators with optional filters

    Parameters:
    - Skip
    - Limit
    - Active
    - Zone_id

    Returns:
    - List of Misurators
    """

    query = db.query(models.Misurator)
    
    if active is not None:
        query = query.filter(models.Misurator.active == active)
    if zone_id is not None:
        query = query.filter(models.Misurator.zone_id == zone_id)
    
    misurators = query.offset(skip).limit(limit).all()
    return misurators

# Create new misurator
@app.post("/misurators/", response_model=schemas.Misurator, status_code=status.HTTP_201_CREATED)
def create_misurator(
    misurator: schemas.MisuratorCreate, 
    db: Session = Depends(get_db)
):
    """
    Create new misurator

    Parameters:
    - active
    - zone_id

    Returns:
    - Created Misurator
    """

    # Check if zone exits
    zone = db.query(models.Zone).filter(models.Zone.id == misurator.zone_id).first()
    if zone is None:
        raise HTTPException(
            status_code=400, 
            detail="Zone Not Found"
        )
    
    db_misurator = models.Misurator(**misurator.model_dump())
    db.add(db_misurator)
    db.commit()
    db.refresh(db_misurator)
    return db_misurator

# Get specific misurator
@app.get("/misurators/{misurator_id}", response_model=schemas.Misurator)
def get_misurator(
    misurator_id: int, 
    db: Session = Depends(get_db)
):
    """
    Get specific misurator by id

    Parameters:
    - Misurator ID

    Returns:
    - Specific Misurator
    """

    misurator = db.query(models.Misurator).filter(models.Misurator.id == misurator_id).first()
    if misurator is None:
        raise HTTPException(
            status_code=404, 
            detail="Misurator Not Found"
        )
    return misurator

# Update misurator
@app.put("/misurators/{misurator_id}", response_model=schemas.Misurator)
def update_misurator(
    misurator_id: int, 
    misurator_update: schemas.MisuratorUpdate, 
    db: Session = Depends(get_db)
):
    """
    Update Misurator

    Parameters:
    - active
    - zone_id

    Returns:
    - Updated Misurator
    """

    db_misurator = db.query(models.Misurator).filter(models.Misurator.id == misurator_id).first()
    if db_misurator is None:
        raise HTTPException(
            status_code=404, 
            detail="Misurator Not Found"
        )
    
    # If updating zone, check if it exists
    if misurator_update.zone_id is not None:
        zone = db.query(models.Zone).filter(models.Zone.id == misurator_update.zone_id).first()
        if zone is None:
            raise HTTPException(
                status_code=400, 
                detail="Zone Not Found"
            )
    
    # Update only given fields
    update_data = misurator_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_misurator, field, value)
    
    db.commit()
    db.refresh(db_misurator)
    return db_misurator

# Activate misurator
@app.put("/misurators/{misurator_id}/activate")
def activate_misurator(
    misurator_id: int, 
    db: Session = Depends(get_db)
):
    """
    Activate misurator

    Parameters:
    - Misurator ID

    Returns:
    - Succesfulness msg
    """

    misurator = db.query(models.Misurator).filter(models.Misurator.id == misurator_id).first()
    if misurator is None:
        raise HTTPException(
            status_code=404, 
            detail="Misurator Not Found"
        )
    
    misurator.active = True
    db.commit()
    return {"message": "Misurator activated succesfully"}

# Deactivate misurator
@app.put("/misurators/{misurator_id}/deactivate")
def deactivate_misurator(
    misurator_id: int, 
    db: Session = Depends(get_db)
):
    """
    Deactivate misurator

    Parameters:
    - Misurator ID

    Returns:
    - Succesfullness msg
    """

    misurator = db.query(models.Misurator).filter(models.Misurator.id == misurator_id).first()
    if misurator is None:
        raise HTTPException(
            status_code=404, 
            detail="Misurator Not Found"
        )
    
    misurator.active = False
    db.commit()
    return {"message": "Misurator deactivated succesfully"}

### Misurations endpoints ###

# Get all misurations
@app.get("/misurations/", response_model=List[schemas.Misuration])
def get_misurations(
    skip: int = 0, 
    limit: int = 100, 
    misurator_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """
    Get all misurations with optional filters

    Parameters:
    - Skip  (skip x records)
    - Limit (maximum records)

    Returns:
    - List of all zones
    """
    query = db.query(models.Misuration)
    
    if misurator_id is not None:
        query = query.filter(models.Misuration.misurator_id == misurator_id)
    if start_date is not None:
        query = query.filter(models.Misuration.created_at >= start_date)
    if end_date is not None:
        query = query.filter(models.Misuration.created_at <= end_date)
    
    misurations = query.order_by(models.Misuration.created_at.desc()).offset(skip).limit(limit).all()
    return misurations

# Create new misuration
@app.post("/misurations/", response_model=schemas.Misuration, status_code=status.HTTP_201_CREATED)
def create_misuration(
    misuration: schemas.MisurationCreate, 
    db: Session = Depends(get_db)
):
    """
    Create a new misuration

    Parameters:
    - value
    - misurator_id

    Returns:
    - Created Misuration
    """

    # Check if misurator exists and is active
    misurator = db.query(models.Misurator).filter(models.Misurator.id == misuration.misurator_id).first()
    if misurator is None:
        raise HTTPException(
            status_code=400, 
            detail="Misurator Not Found"
        )
    if not misurator.active:
        raise HTTPException(
            status_code=400, 
            detail="Misurator Not Active"
        )
    
    db_misuration = models.Misuration(**misuration.model_dump())
    db.add(db_misuration)
    db.commit()
    db.refresh(db_misuration)
    return db_misuration

# Get specific misuration
@app.get("/misurations/{misuration_id}", response_model=schemas.Misuration)
def get_misuration(
    misuration_id: int, 
    db: Session = Depends(get_db)
):
    """
    Get specific misuration by id

    Parameters:
    - Misuration ID

    Returns:
    - Specific Misuration
    """

    misuration = db.query(models.Misuration).filter(models.Misuration.id == misuration_id).first()
    if misuration is None:
        raise HTTPException(
            status_code=404, 
            detail="Misuration Not Found"
        )
    return misuration

### Relationships Endpoints ###

# Get all misurators of a specific zone
@app.get("/zones/{zone_id}/misurators", response_model=List[schemas.Misurator])
def get_zone_misurators(
    zone_id: int, 
    db: Session = Depends(get_db)
):
    """
    Get all misurators of a specific zone

    Parameters:
    - zone_id

    Returns:
    - List of all Misurators of a specific Zone
    """

    zone = db.query(models.Zone).filter(models.Zone.id == zone_id).first()
    if zone is None:
        raise HTTPException(
            status_code=404, 
            detail="Zone Not Found"
        )
    
    misurators = db.query(models.Misurator).filter(models.Misurator.zone_id == zone_id).all()
    return misurators

# Get all misurations of a specific misurator
@app.get("/misurators/{misurator_id}/misurations", response_model=List[schemas.Misuration])
def get_misurator_misurations(
    misurator_id: int, 
    hours: Optional[int] = Query(24, description="Last X hours"),
    db: Session = Depends(get_db)
):
    """
    Get all misurations of a specific misurator

    Parameters:
    - misurator_id
    - hours

    Returns:
    - List of all Misurations of specific Misurator in the last X Hours
    """

    misurator = db.query(models.Misurator).filter(models.Misurator.id == misurator_id).first()
    if misurator is None:
        raise HTTPException(
            status_code=404, 
            detail="Misurator Not Found"
        )
    
    since_time = datetime.now() - timedelta(hours=hours)
    misurations = db.query(models.Misuration).filter(
        models.Misuration.misurator_id == misurator_id,
        models.Misuration.created_at >= since_time
    ).order_by(models.Misuration.created_at.desc()).all()
    
    return misurations

### Statistics Endpoints ###

# Get statistics of zones
@app.get("/stats/zones")
def get_zones_stats(db: Session = Depends(get_db)):
    """
    Get statistics for all zones

    Parameters:
    - N/A

    Returns:
    - total zones
    - total misurators
    - total active misurators
    """
    zones = db.query(models.Zone).all()
    stats = []
    
    for zone in zones:
        misurators = db.query(models.Misurator).filter(models.Misurator.zone_id == zone.id)
        active_misurators = misurators.filter(models.Misurator.active == True).count()
        total_misurators = misurators.count()
        
        # Last misuration for this zone
        last_misuration = db.query(models.Misuration).join(models.Misurator).filter(
            models.Misurator.zone_id == zone.id
        ).order_by(models.Misuration.created_at.desc()).first()
        
        stats.append({
            "zone_id": zone.id,
            "city": zone.city,
            "active_misurators": active_misurators,
            "total_misurators": total_misurators,
            "last_misuration": last_misuration.created_at if last_misuration else None
        })
    
    return stats

# Get stats of a specific misurator
@app.get("/stats/misurators/{misurator_id}")
def get_misurator_stats(
    misurator_id: int,
    days: int = Query(7, description="Last x days"),
    db: Session = Depends(get_db)
):
    """
    Gets stats of a specific misurator

    Parameters:
    - Misurator ID

    Returns:
    - misurator_id
    - total_misurations
    - avg_value
    - min_value
    - max_value
    - period_days

    """
    misurator = db.query(models.Misurator).filter(models.Misurator.id == misurator_id).first()
    if misurator is None:
        raise HTTPException(
            status_code=404, 
            detail="Misurator Not Found"
        )
    
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

### Health Check ###

# Root check
@app.get("/")
def read_root():
    return {
        "message": "Earthquake Monitoring System",
        "version": "1.0.0",
        "endpoints": {
            "zones": "/zones/",
            "misurators": "/misurators/",
            "misurations": "/misurations/",
            "stats": "/stats/zones"
        }
    }

# Health endpoint
@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    """
    Application and Database health check

    Parameters:
    - N/A

    Returns:
    - status
    - connection
    - timestamp
    """
    try:
        # Database connection test
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