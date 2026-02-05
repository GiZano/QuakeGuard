"""
Database Configuration Module
-----------------------------
This module handles the SQLAlchemy database connection setup.
It configures the engine, session factory, and provides the dependency 
injection callable used by FastAPI path operations.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Retrieve database connection string
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("FATAL: DATABASE_URL environment variable is not set.")

# Initialize SQLAlchemy Engine
# Note: For SQLite, add argument: connect_args={"check_same_thread": False}
engine = create_engine(DATABASE_URL)

# Configure Session Factory
# autocommit=False and autoflush=False are standard for robust transaction management
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for ORM models
Base = declarative_base()

def get_db():
    """
    Dependency generator that creates a new database session for a single request
    and closes it after the request is completed.
    
    Yields:
        Session: A SQLAlchemy database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()