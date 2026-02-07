"""
Database Models Definition
--------------------------
This module defines the SQLAlchemy ORM models for the Earthquake Monitoring System.
It integrates PostGIS geometry types for GPS location handling and defines
the schema for Zones, Sensors (Misurators), Measurements, and Alerts.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from src.database import Base

class Zone(Base):
    """
    Represents a geographical zone (e.g., a city or district).
    Acts as the parent entity for sensors and alerts.
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
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    location = Column(Geometry('POINT', srid=4326), nullable=True)

    # --- SECURITY (Ecco il pezzo mancante!) ---
    # Stores the ECDSA Public Key used to verify message signatures
    public_key_hex = Column(String, nullable=False)

    # Relationships
    zone = relationship("Zone", back_populates="misurators")
    misurations = relationship("Misuration", back_populates="misurator", cascade="all, delete-orphan")


class Misuration(Base):
    """
    Represents a single data point (acceleration/vibration) recorded by a Misurator.
    """
    __tablename__ = "misurations"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    value = Column(Integer, nullable=False)
    
    # Foreign Key
    misurator_id = Column(Integer, ForeignKey("misurators.id"), nullable=False)

    # Relationships
    misurator = relationship("Misurator", back_populates="misurations")


class Alert(Base):
    """
    Represents an aggregated/confirmed seismic event for a specific zone.
    """
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(Integer, ForeignKey("zones.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    severity = Column(Float, nullable=False) 
    message = Column(String(255), nullable=True)

    # Relationships
    zone = relationship("Zone")