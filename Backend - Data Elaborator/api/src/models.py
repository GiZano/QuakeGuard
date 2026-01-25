"""
Database Models Definition
--------------------------
This module defines the SQLAlchemy ORM models for the Earthquake Monitoring System.
It establishes the schema for Zones, Misurators (Sensors), and Misurations (Data points),
including relationships and foreign key constraints to ensure data integrity.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from src.database import Base

class Zone(Base):
    """
    Represents a geographical zone (e.g., a city or district).
    """
    __tablename__ = "zones"

    id = Column(Integer, primary_key=True, index=True)
    city = Column(String(100), nullable=False)

    # Relationships
    # 'cascade' ensures that if a Zone is deleted, all associated Misurators are also removed.
    misurators = relationship("Misurator", back_populates="zone", cascade="all, delete-orphan")


class Misurator(Base):
    """
    Represents a physical IoT sensor device installed in a specific Zone.
    """
    __tablename__ = "misurators"

    id = Column(Integer, primary_key=True, index=True)
    active = Column(Boolean, default=True, nullable=False)
    
    # Foreign Key: Links the sensor to a specific Zone
    zone_id = Column(Integer, ForeignKey("zones.id"), nullable=False)

    # Relationships
    zone = relationship("Zone", back_populates="misurators")
    misurations = relationship("Misuration", back_populates="misurator", cascade="all, delete-orphan")


class Misuration(Base):
    """
    Represents a single data point (acceleration/vibration) recorded by a Misurator.
    """
    __tablename__ = "misurations"

    id = Column(Integer, primary_key=True, index=True)
    
    # Indexed for performance on time-series queries (critical for alert system)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    value = Column(Integer, nullable=False)
    
    # Foreign Key: Links the data point to the source device
    misurator_id = Column(Integer, ForeignKey("misurators.id"), nullable=False)

    # Relationships
    misurator = relationship("Misurator", back_populates="misurations")