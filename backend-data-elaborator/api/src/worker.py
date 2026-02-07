"""
QuakeGuard Background Worker
-----------------------------
Consumes seismic events from the Redis queue, persists data to PostgreSQL,
and detects critical seismic thresholds to generate persistent Alerts.
"""

import json
import redis
import time
from datetime import datetime
from src.database import SessionLocal
from src.models import Misuration, Alert

# --- CONFIGURATION ---
REDIS_HOST = 'redis'
REDIS_PORT = 6379
ALERT_THRESHOLD = 50       # Number of sensors triggering within the window to raise an alarm
ALERT_WINDOW_SECONDS = 10  # Rolling time window for the counter
ALERT_COOLDOWN = 60        # Seconds to wait before raising another alarm for the same zone

# Synchronous Redis client for the worker loop
redis_sync = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)

def run_worker():
    """
    Continuous loop consuming messages from the 'seismic_events' queue.
    Uses BRPOP (Blocking Right Pop) for efficient resource utilization.
    """
    print(f"👷 Worker started. Threshold: {ALERT_THRESHOLD} events / {ALERT_WINDOW_SECONDS}s")
    
    while True:
        try:
            # Blocking pop from the tail of the list (waits until data is available)
            _, data = redis_sync.brpop("seismic_events")
            event = json.loads(data)
            
            zone_id = event['zone_id']
            
            with SessionLocal() as db:
                # 1. Persist raw measurement to PostgreSQL
                new_misuration = Misuration(
                    value=event['value'],
                    misurator_id=event['misurator_id']
                    # created_at is handled automatically by DB default
                )
                db.add(new_misuration)
                
                # 2. Update real-time alert counter in Redis
                # Key: "zone:{id}:alerts" -> Increments with every high-vibration event
                zone_counter_key = f"zone:{zone_id}:alerts"
                
                pipe = redis_sync.pipeline()
                pipe.incr(zone_counter_key)
                pipe.expire(zone_counter_key, ALERT_WINDOW_SECONDS) 
                # Execute and get the new counter value
                results = pipe.execute()
                current_count = results[0]

                # 3. Check Threshold & Generate Alert
                if current_count >= ALERT_THRESHOLD:
                    # Check if we are in a "cooldown" period to avoid spamming the DB
                    cooldown_key = f"zone:{zone_id}:alarm_cooldown"
                    
                    if not redis_sync.exists(cooldown_key):
                        print(f"🚨 CRITICAL ALARM! Zone {zone_id} has {current_count} events!")
                        
                        # Create persistent Alert record
                        new_alert = Alert(
                            zone_id=zone_id,
                            severity=float(current_count) / 10.0, # Example severity logic
                            message=f"Seismic Swarm Detected: {current_count} sensors triggered.",
                            timestamp=datetime.utcnow()
                        )
                        db.add(new_alert)
                        
                        # Set cooldown flag (expires in 60s)
                        redis_sync.setex(cooldown_key, ALERT_COOLDOWN, "active")
                
                db.commit()
                
        except Exception as e:
            print(f"❌ Error processing event: {str(e)}")
            time.sleep(1) # Prevent rapid-fire errors if DB/Redis connection drops

if __name__ == "__main__":
    # Optional: Wait for DB to be ready script could be added here similar to main.py
    # but usually the main API holds the fort until DB is up.
    time.sleep(5) # Give services a moment to warm up
    run_worker()