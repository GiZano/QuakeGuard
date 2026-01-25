"""
Pydantic Schemas (Data Transfer Objects)
----------------------------------------
This module defines the Pydantic models used for request validation 
and response serialization. It mirrors the SQLAlchemy models but adds 
type safety and validation logic for the API layer.
"""

from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

# ==========================================
# ZONE SCHEMAS
# ==========================================

class ZoneBase(BaseModel):
    """Shared properties for Zone."""
    city: str 

class ZoneCreate(ZoneBase):
    """Properties to receive on Zone creation."""
    pass 

class ZoneUpdate(BaseModel):
    """Properties to receive on Zone update."""
    city: Optional[str] = None

class Zone(ZoneBase):
    """Properties to return to client (ORM representation)."""
    id: int

    # Configuration to allow creation from ORM objects
    model_config = ConfigDict(from_attributes=True)


# ==========================================
# MISURATOR (SENSOR) SCHEMAS
# ==========================================

class MisuratorBase(BaseModel):
    """Shared properties for Misurator (Sensor)."""
    active: bool 
    zone_id: int

class MisuratorCreate(MisuratorBase):
    """Properties to receive on Misurator creation."""
    pass 

class MisuratorUpdate(BaseModel):
    """Properties to receive on Misurator update."""
    active:  Optional[bool] = None
    zone_id: Optional[int] = None

class Misurator(MisuratorBase):
    """Properties to return to client (ORM representation)."""
    id: int

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# MISURATION (DATA POINT) SCHEMAS
# ==========================================

class MisurationBase(BaseModel):
    """Shared properties for Misuration."""
    value: int
    misurator_id: int

class MisurationCreate(MisurationBase): 
    """Properties to receive on data ingestion."""
    pass

class MisurationUpdate(BaseModel):
    """Properties to receive on data update (rarely used for time-series)."""
    value: Optional[int] = None
    misurator_id: Optional[int] = None

class Misuration(MisurationBase):
    """Properties to return to client (ORM representation)."""
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# AGGREGATED / NESTED SCHEMAS
# ==========================================
# These schemas enable nested JSON responses (e.g., getting a Zone with all its Sensors)

class MisuratorWithZone(Misurator):
    """Misurator response including Zone details."""
    zone: Optional[Zone] = None

class MisurationWithMisurator(Misuration):
    """Misuration response including Sensor details."""
    misurator: Optional[Misurator] = None

class MisuratorWithMisurations(Misurator):
    """Misurator response including historical data points."""
    misurations: List[Misuration] = []

class ZoneWithMisurators(Zone):
    """Zone response including list of installed sensors."""
    misurators: List[Misurator] = []


# ==========================================
# ANALYTICS & ALERTS SCHEMAS
# ==========================================

class ZoneStats(BaseModel):
    """DTO for aggregated Zone statistics."""
    zone_id: int
    city: str
    active_misurators: int
    total_misurators: int
    avg_misuration_value: Optional[float] = None
    last_misuration: Optional[datetime] = None

class AlertResponse(BaseModel):
    """DTO for Earthquake Alert System response."""
    zone_id: int
    is_earthquake_detected: bool
    measurement_count: int
    threshold: int
    time_window_seconds: int
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# CIRCULAR REFERENCE HANDLING
# ==========================================
# Pydantic v2 method to resolve forward references in nested models.

ZoneWithMisurators.model_rebuild()
MisuratorWithMisurations.model_rebuild()
MisurationWithMisurator.model_rebuild()