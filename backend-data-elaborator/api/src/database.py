"""
Database Configuration Module
-----------------------------
This module establishes the SQLAlchemy connection engine and session factory.
It is configured with aggressive pooling settings to handle high-concurrency 
load testing (e.g., 100+ simultaneous connections) without exhausting the queue.
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

# ==========================================
# ENGINE CONFIGURATION
# ==========================================
# We configure the connection pool to handle the stress test load.
# Formula: Total Capacity = pool_size + max_overflow
# Target: 100 concurrent requests from the script.
engine = create_engine(
    DATABASE_URL,
    # 1. pool_size: The number of connections to keep open inside the connection pool.
    #    Increased to 40 to maintain a high baseline of readiness.
    pool_size=40,

    # 2. max_overflow: The number of connections to allow in excess of pool_size.
    #    Set to 60. Total capacity = 40 + 60 = 100 connections.
    #    This ensures we cover the burst of 100 requests from your script.
    max_overflow=60,

    # 3. pool_timeout: The number of seconds to wait before giving up on getting a connection.
    #    Increased to 60s to prevent TimeoutErrors during heavy congestion.
    pool_timeout=60,

    # 4. pool_pre_ping: Enables "pessimistic disconnect handling".
    #    The engine will test the connection liveness before returning it.
    #    Prevents "server closed the connection unexpectedly" errors.
    pool_pre_ping=True,
    
    # 5. pool_recycle: Recycle connections every hour (3600s) to prevent stale connections.
    pool_recycle=3600
)

# ==========================================
# SESSION FACTORY
# ==========================================
# autocommit=False: We manually commit transactions to ensure atomicity.
# autoflush=False: We manually flush to control when data is sent to the DB.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all ORM models to inherit from
Base = declarative_base()

def get_db():
    """
    Dependency generator for FastAPI path operations.
    Creates a new database session for each request and ensures it is closed 
    regardless of whether the request succeeds or fails.
    
    Yields:
        Session: A SQLAlchemy database session attached to the connection pool.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()