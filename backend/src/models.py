"""
Database Models Definition
--------------------------
Defines the SQLAlchemy ORM models.
Updated to support Device Provisioning (MAC Address & Firmware Version).
"""

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey, Float, Text,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from src.database import Base

ZONE_FK = "zones.id"

class Zone(Base):
    __tablename__ = "zones"

    id = Column(Integer, primary_key=True, index=True)
    city = Column(String(100), nullable=False, unique=True)
    
    # Auditability timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # PostGIS Polygon boundary for automatic sensor assignment
    geom = Column(Geometry('POLYGON', srid=4326), nullable=True)

    # Relationships
    sensors = relationship("Sensor", back_populates="zone", cascade="all, delete-orphan")


class Sensor(Base):
    """
    IoT Sensor Device.
    Includes Security (ECDSA Key) and Hardware Identity (MAC, Firmware).
    """
    __tablename__ = "sensors"

    id = Column(Integer, primary_key=True, index=True)
    active = Column(Boolean, default=True, nullable=False)
    
    # Foreign Key
    zone_id = Column(Integer, ForeignKey(ZONE_FK), nullable=False)

    # --- GPS Configuration ---
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    location = Column(Geometry('POINT', srid=4326), nullable=True)
    # GNSS-ready: last reliable fix timestamp . Null until the first fix.
    last_fix_at = Column(DateTime(timezone=True), nullable=True)

    # --- SECURITY & IDENTITY ---
    # The public key is the primary cryptographic identity
    public_key_hex = Column(String, nullable=False, unique=True, index=True)
    
    mac_address = Column(String(17), nullable=True, unique=True, index=True)

    # Relationships
    zone = relationship("Zone", back_populates="sensors")
    readings = relationship("Reading", back_populates="sensor", cascade="all, delete-orphan")


class Reading(Base):
    __tablename__ = "readings"

    # Composite PK (id, recorded_at): TimescaleDB requires the partitioning
    # column to be part of every primary/unique key of the hypertable.
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    recorded_at = Column(DateTime(timezone=True), primary_key=True, server_default=func.now(), nullable=False, index=True)
    value = Column(Integer, nullable=False)
    
    # GNSS-ready: event coordinates captured at ingestion  so the worker
    # can fragment cooldowns per-area and v2.0 can correlate nodes spatially.
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    # System Telemetry (v2.1.0 Grafana Observability)
    latency_ms = Column(Integer, nullable=True)
    free_heap = Column(Integer, nullable=True)
    rssi = Column(Integer, nullable=True)
    gnss_satellites = Column(Integer, nullable=True)
    
    sensor_id = Column(Integer, ForeignKey("sensors.id"), nullable=False)

    sensor = relationship("Sensor", back_populates="readings")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(Integer, ForeignKey(ZONE_FK), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    magnitude = Column(Float, nullable=False) 
    message = Column(String(255), nullable=True)

    # Triangulation (v2.0)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    origin_time = Column(DateTime(timezone=True), nullable=True)
    is_triangulated = Column(Boolean, default=False, nullable=False)

    zone = relationship("Zone")


class EmergencyReport(Base):
    """
    AI-generated emergency report for a confirmed Alert.

    `status` is an explicit state machine (PENDING -> COMPLETED | FAILED) so the
    mobile client can render a "AI Report Unavailable" badge on FAILED instead of
    hanging indefinitely on a pending job.
    """
    __tablename__ = "emergency_reports"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("alerts.id"), nullable=False, unique=True, index=True)
    zone_id = Column(Integer, ForeignKey(ZONE_FK), nullable=False)
    magnitude = Column(Float, nullable=False)

    # State machine: PENDING / COMPLETED / FAILED
    status = Column(String(16), nullable=False, default="PENDING", server_default="PENDING", index=True)

    summary = Column(Text, nullable=True)
    recommendations = Column(Text, nullable=True)
    model_used = Column(String(64), nullable=True)
    error = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    alert = relationship("Alert", backref="emergency_report")

    def __init__(self, **kwargs):
        """Apply the PENDING default at construction time so the state machine is
        observable before the row is flushed to the database."""
        kwargs.setdefault("status", "PENDING")
        super().__init__(**kwargs)