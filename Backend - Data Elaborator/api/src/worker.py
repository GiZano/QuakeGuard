"""
QuakeFinder Background Worker
-----------------------------
Consumes seismic events from the Redis queue, persists data to PostgreSQL,
and updates real-time alert counters in the caching layer.
"""

import json
import redis
import time
from src.database import SessionLocal
from src.models import Misuration

# Synchronous Redis client for the worker loop
redis_sync = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)

def run_worker():
    """
    Continuous loop consuming messages from the 'seismic_events' queue.
    Uses BRPOP (Blocking Right Pop) for efficient resource utilization.
    """
    print("Worker started. Listening for seismic events...")
    
    while True:
        try:
            # Blocking pop from the tail of the list
            _, data = redis_sync.brpop("seismic_events")
            event = json.loads(data)
            
            with SessionLocal() as db:
                # 1. Persist measurement to PostgreSQL
                new_misuration = Misuration(
                    value=event['value'],
                    misurator_id=event['misurator_id']
                )
                db.add(new_misuration)
                
                # 2. Update real-time alert counter in Redis
                # Increments the counter for the specific zone with a 10s expiration
                zone_key = f"zone:{event['zone_id']}:alerts"
                pipeline = redis_sync.pipeline()
                pipeline.incr(zone_key)
                pipeline.expire(zone_key, 10)
                pipeline.execute()
                
                db.commit()
                
        except Exception as e:
            print(f"Error processing event: {str(e)}")
            time.sleep(1) # Prevent rapid-fire errors if DB/Redis connection drops

if __name__ == "__main__":
    run_worker()