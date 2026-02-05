"""
QuakeFinder Stress Test Script
------------------------------
Performs a load test on the QuakeFinder Ingestion API.
It simulates concurrent IoT devices generating ECDSA-signed payloads
to verify the system's throughput and asynchronous processing capabilities.

Requirements:
    - aiohttp
    - ecdsa
"""

import asyncio
import aiohttp
import time
import random
from ecdsa import SigningKey, NIST256p
from typing import List, Optional, Tuple

# --- CONFIGURATION PARAMETERS ---
BASE_URL = "http://localhost:8000"
NUM_SENSORS = 100
TEST_ZONE_ID = 1
TIMEOUT_SECONDS = 10

class VirtualSensor:
    """
    Represents a simulated IoT sensor capable of generating cryptographic signatures.
    """
    def __init__(self):
        # Generate a real NIST256p (secp256r1) key pair
        self.sk = SigningKey.generate(curve=NIST256p)
        self.vk = self.sk.verifying_key
        # The public key is exported as a hex string for API registration
        self.public_key_hex = self.vk.to_string().hex()
        self.sensor_id: Optional[int] = None
        # Generate random coordinates
        self.lat = round(random.uniform(-90, 90), 6)
        self.lon = round(random.uniform(-180, 180), 6)

    def sign_message(self, message: str) -> str:
        """
        Signs a message string using the sensor's private key.
        
        Args:
            message (str): The payload content to sign (typically "value:timestamp").
            
        Returns:
            str: The ECDSA signature in hexadecimal format.
        """
        return self.sk.sign(message.encode('utf-8')).hex()

async def setup_infrastructure(session: aiohttp.ClientSession) -> List[VirtualSensor]:
    """
    Initializes the test environment:
    1. Ensures the target Zone exists.
    2. Registers the virtual sensors with the backend to whitelist their public keys.
    """
    print(f"🛠️  SETUP: Initializing infrastructure for {NUM_SENSORS} sensors...")
    
    # 1. Create or Verify Zone
    zone_payload = {"city": "StressTestCity", "id": TEST_ZONE_ID}
    async with session.post(f"{BASE_URL}/zones/", json=zone_payload) as resp:
        # Accept 200/201 (Created) or 4xx (Likely already exists)
        if resp.status not in [200, 201, 400, 422]:
            print(f"⚠️ Warning: Zone creation returned status {resp.status}")

    sensors = [VirtualSensor() for _ in range(NUM_SENSORS)]

    # 2. Register Sensors concurrently
    tasks = []
    for s in sensors:
        payload = {
            "active": True,
            "zone_id": TEST_ZONE_ID,
            "latitude": s.lat,
            "longitude": s.lon,
            "public_key_hex": s.public_key_hex
        }
        tasks.append(register_single_sensor(session, s, payload))
    
    results = await asyncio.gather(*tasks)
    
    # Filter out successfully registered sensors
    valid_sensors = [s for s in results if s is not None]
    print(f"✅ SETUP COMPLETE: {len(valid_sensors)}/{NUM_SENSORS} sensors registered and ready.\n")
    return valid_sensors

async def register_single_sensor(
    session: aiohttp.ClientSession, 
    sensor: VirtualSensor, 
    payload: dict
) -> Optional[VirtualSensor]:
    """Helper function to register a single sensor via HTTP POST."""
    try:
        async with session.post(f"{BASE_URL}/misurators/", json=payload, timeout=TIMEOUT_SECONDS) as resp:
            if resp.status == 201:
                data = await resp.json()
                sensor.sensor_id = data['id']
                return sensor
            else:
                text = await resp.text()
                print(f"❌ Registration failed: Status {resp.status} - {text}")
                return None
    except Exception as e:
        print(f"❌ Connection error during setup: {str(e)}")
        return None

async def send_measurement(
    session: aiohttp.ClientSession, 
    sensor: VirtualSensor
) -> Tuple[int, float]:
    """
    Simulates the transmission of a seismic data point.
    Constructs the payload, signs it, and sends it to the ingestion endpoint.
    
    Returns:
        Tuple[int, float]: (HTTP Status Code, Request Latency in seconds)
    """
    # Simulate high intensity vibration
    value = random.randint(200, 900)
    timestamp = time.time()
    
    # CRITICAL: The string format must match the server's verification logic exactly.
    # Format: "value:timestamp"
    message_to_sign = f"{value}:{timestamp}"
    signature = sensor.sign_message(message_to_sign)

    payload = {
        "value": value,
        "misurator_id": sensor.sensor_id,
        "device_timestamp": timestamp,
        "signature_hex": signature
    }

    start_t = time.perf_counter()
    try:
        async with session.post(f"{BASE_URL}/misurations/", json=payload, timeout=TIMEOUT_SECONDS) as resp:
            # We await the response content to ensure the request cycle is complete
            await resp.read() 
            end_t = time.perf_counter()
            return resp.status, end_t - start_t
    except Exception:
        # Return 999 to indicate a client-side exception/timeout
        return 999, 0.0

async def main():
    print(f"--- 🌋 QUAKEFINDER LOAD TEST: {NUM_SENSORS} CONCURRENT SENSORS ---")
    
    async with aiohttp.ClientSession() as session:
        # PHASE 1: Setup (Device Registration)
        sensors = await setup_infrastructure(session)
        if not sensors:
            print("❌ No sensors registered. Aborting test.")
            return

        print("⏳ Preparing payload (Thundering Herd simulation)...")
        # Create coroutines but do not schedule them yet
        tasks = [send_measurement(session, s) for s in sensors]
        
        print("🚀 FIRE! Sending concurrent requests...")
        start_time = time.perf_counter()
        
        # Execute all requests simultaneously
        results = await asyncio.gather(*tasks)
        
        total_time = time.perf_counter() - start_time

    # --- METRICS & REPORTING ---
    success_count = sum(1 for status, _ in results if status == 202)
    fail_count = sum(1 for status, _ in results if status != 202)
    
    # Calculate average latency only for successful requests or all requests
    avg_req_time = sum(t for _, t in results) / len(results) if results else 0
    rps = len(results) / total_time if total_time > 0 else 0

    print("\n" + "="*50)
    print(f"📊 FINAL TEST REPORT")
    print("="*50)
    print(f"⏱️  Total Execution Time:    {total_time:.4f} seconds")
    print(f"🚀 Throughput (RPS):        {rps:.2f} requests/sec")
    print(f"✅ Success (HTTP 202):      {success_count}")
    print(f"❌ Failures:                {fail_count}")
    print(f"🐢 Avg Request Latency:     {avg_req_time*1000:.2f} ms")
    print("="*50)

    if fail_count == 0 and success_count == len(sensors):
        print("🏆 TEST PASSED: System handled the load successfully.")
    else:
        print("⚠️ TEST FAILED or PARTIAL: Check server logs for details.")

if __name__ == "__main__":
    # Windows-specific fix for asyncio loop policy
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except AttributeError:
        pass
        
    asyncio.run(main())