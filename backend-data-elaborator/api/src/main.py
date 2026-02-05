"""
QuakeFinder Ingestion API
-------------------------
Handles high-throughput IoT data ingestion from ESP32 sensors.
Implements asynchronous request handling and ECDSA signature verification.
"""

import json
import asyncio
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from redis import asyncio as aioredis
from ecdsa import VerifyingKey, NIST256p, BadSignatureError

from src.database import get_db
import src.models as models
import src.schemas as schemas

app = FastAPI(title="QuakeFinder Ingestion Service")

# Initialize asynchronous Redis client
redis_client = aioredis.from_url("redis://redis:6379/0", decode_responses=True)

def verify_device_signature(public_key_hex: str, message: str, signature_hex: str) -> bool:
    """
    Verifies the ECDSA signature sent by the IoT device.
    CPU-bound operation; should be offloaded to an executor in async contexts.
    """
    try:
        vk = VerifyingKey.from_string(bytes.fromhex(public_key_hex), curve=NIST256p)
        return vk.verify(bytes.fromhex(signature_hex), message.encode())
    except (BadSignatureError, ValueError):
        return False

@app.post("/misurations/", status_code=status.HTTP_202_ACCEPTED)
async def create_misuration_async(
    misuration: schemas.MisurationCreate, 
    db: Session = Depends(get_db)
):
    """
    Asynchronously handles incoming seismic data.
    - Validates the sensor identity and status.
    - Verifies the digital signature using a thread pool executor.
    - Queues the validated payload into Redis for background processing.
    """
    # Fetch misurator metadata (optimization: consider caching this in Redis)
    misurator = db.query(models.Misurator).filter(models.Misurator.id == misuration.misurator_id).first()
    
    if not misurator or not misurator.active:
        raise HTTPException(status_code=403, detail="Sensor is unauthorized or inactive")

    # Offload CPU-bound signature verification to a thread pool
    loop = asyncio.get_event_loop()
    message = f"{misuration.value}:{misuration.device_timestamp}"
    
    is_valid = await loop.run_in_executor(
        None, 
        verify_device_signature, 
        misurator.public_key_hex, 
        message, 
        misuration.signature_hex
    )

    if not is_valid:
        raise HTTPException(status_code=401, detail="Invalid digital signature")

    # Prepare payload for the background worker
    payload = misuration.model_dump()
    payload['zone_id'] = misurator.zone_id 
    
    # Enqueue data into Redis list 'seismic_events'
    await redis_client.lpush("seismic_events", json.dumps(payload))
    
    return {"status": "accepted", "detail": "Data enqueued for background processing"}