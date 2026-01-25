"""
Pydantic Schemas (Data Transfer Objects)
----------------------------------------
Defines request/response structures.
Includes validation for GPS coordinates.
"""

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime

# ==========================================
# ZONE SCHEMAS
# ==========================================

class ZoneBase(BaseModel):
    city: str 

class ZoneCreate(ZoneBase):
    pass 

class ZoneUpdate(BaseModel):
    city: Optional[str] = None

class Zone(ZoneBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# ==========================================
# MISURATOR (SENSOR) SCHEMAS
# ==========================================

class MisuratorBase(BaseModel):
    active: bool 
    zone_id: int

class MisuratorCreate(MisuratorBase):
    """
    Payload for creating a new sensor.
    Requires valid GPS coordinates.
    """
    latitude: float = Field(..., ge=-90, le=90, description="GPS Latitude (-90 to 90)")
    longitude: float = Field(..., ge=-180, le=180, description="GPS Longitude (-180 to 180)")

class MisuratorUpdate(BaseModel):
    active:  Optional[bool] = None
    zone_id: Optional[int] = None

class Misurator(MisuratorBase):
    """
    Response object for a sensor.
    Returns lat/lon as floats. The raw 'location' geometry is handled internally by DB.
    """
    id: int
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# MISURATION (DATA POINT) SCHEMAS
# ==========================================

class MisurationBase(BaseModel):
    value: int
    misurator_id: int

class MisurationCreate(MisurationBase): 
    pass

class MisurationUpdate(BaseModel):
    value: Optional[int] = None
    misurator_id: Optional[int] = None

class Misuration(MisurationBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ==========================================
# ANALYTICS & ALERTS SCHEMAS
# ==========================================

class ZoneStats(BaseModel):
    zone_id: int
    city: str
    active_misurators: int
    total_misurators: int
    avg_misuration_value: Optional[float] = None
    last_misuration: Optional[datetime] = None

class AlertResponse(BaseModel):
    zone_id: int
    is_earthquake_detected: bool
    measurement_count: int
    threshold: int
    time_window_seconds: int
    timestamp: datetime
    model_config = ConfigDict(from_attributes=True)