"""
Database Models Definition
--------------------------
This module defines the SQLAlchemy ORM models for the Earthquake Monitoring System.
It integrates PostGIS geometry types for GPS location handling.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from src.database import Base

class Zone(Base):
    """
    Represents a geographical zone (e.g., a city or district).
    """
    __tablename__ = "zones"

    id = Column(Integer, primary_key=True, index=True)
    city = Column(String(100), nullable=False)

    # Relationships
    misurators = relationship("Misurator", back_populates="zone", cascade="all, delete-orphan")


class Misurator(Base):
    """
    Represents a physical IoT sensor device installed in a specific Zone.
    Includes GPS coordinates managed via PostGIS.
    """
    __tablename__ = "misurators"

    id = Column(Integer, primary_key=True, index=True)
    active = Column(Boolean, default=True, nullable=False)
    
    # Foreign Key
    zone_id = Column(Integer, ForeignKey("zones.id"), nullable=False)

    # --- GPS Configuration ---
    # We store lat/lon as floats for easy API access/debugging
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    # We store the actual spatial point for GIS queries (SRID 4326 = WGS84 Standard)
    location = Column(Geometry('POINT', srid=4326), nullable=True)

    # Relationships
    zone = relationship("Zone", back_populates="misurators")
    misurations = relationship("Misuration", back_populates="misurator", cascade="all, delete-orphan")


class Misuration(Base):
    """
    Represents a single data point (acceleration/vibration) recorded by a Misurator.
    """
    __tablename__ = "misurations"

    id = Column(Integer, primary_key=True, index=True)
    
    # Indexed for performance on time-series queries
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    value = Column(Integer, nullable=False)
    
    # Foreign Key
    misurator_id = Column(Integer, ForeignKey("misurators.id"), nullable=False)

    # Relationships
    misurator = relationship("Misurator", back_populates="misurations")