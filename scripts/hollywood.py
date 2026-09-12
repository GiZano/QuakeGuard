import asyncio
import aiohttp
import time
import secrets
import os
import json
import ssl
import sys
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat, PrivateFormat, NoEncryption, load_pem_private_key
import aiomqtt
from dotenv import load_dotenv

_ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend", ".env")
load_dotenv(_ENV_PATH, override=False)

API_URL = os.getenv("API_URL", "http://localhost:8000")
ENROLLMENT_TOKEN = os.getenv("ENROLLMENT_TOKEN", "local_demo_override")
MQTT_BROKER = os.getenv("MQTT_BROKER_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_TOPIC = "quakeguard/telemetry"
MQTT_USERNAME = os.getenv("MQTT_USERNAME", None)
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", None)

NUM_SENSORS = 50
FLEET_FILE = os.path.join(os.path.dirname(__file__), "fleet.json")

CITIES = {
    "Tokyo": (35.6895, 139.6917),
    "San Francisco": (37.7749, -122.4194),
    "Mexico City": (19.4326, -99.1332),
    "Santiago": (-33.4489, -70.6693),
    "Naples": (40.8518, 14.2681),
    "Los Angeles": (34.0522, -118.2437),
    "Istanbul": (41.0082, 28.9784),
    "Jakarta": (-6.2088, 106.8456),
    "Pisa": (43.7228, 10.4017),
}

class VirtualSensor:
    def __init__(self, lat, lon, city, sensor_id=-1, mac=None, priv_pem=None):
        self.sensor_id = sensor_id
        self.mac = mac or f"{secrets.choice(range(0, 255 + 1)):02X}:{secrets.choice(range(0, 255 + 1)):02X}:{secrets.choice(range(0, 255 + 1)):02X}:{secrets.choice(range(0, 255 + 1)):02X}:{secrets.choice(range(0, 255 + 1)):02X}:{secrets.choice(range(0, 255 + 1)):02X}"
        self.lat = lat
        self.lon = lon
        self.city = city
        
        if priv_pem:
            self.private_key = load_pem_private_key(priv_pem.encode('utf-8'), password=None)
        else:
            self.private_key = ec.generate_private_key(ec.SECP256R1())
            
        pub_key = self.private_key.public_key().public_bytes(Encoding.DER, PublicFormat.SubjectPublicKeyInfo)
        self.public_key_hex = pub_key.hex()
        
    def get_priv_pem(self):
        return self.private_key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()).decode('utf-8')

async def register_sensor(session, sensor):
    payload = {
        "public_key_hex": sensor.public_key_hex,
        "mac_address": sensor.mac,
        "latitude": sensor.lat,
        "longitude": sensor.lon,
        "firmware_version": "2.1.1-HW",
        "enrollment_token": ENROLLMENT_TOKEN
    }
    try:
        async with session.post(f"{API_URL}/devices/register", json=payload) as resp:
            if resp.status in (200, 201):
                data = await resp.json()
                sensor.sensor_id = data.get("sensor_id", -1)
                print(f"🎬 Registered Sensor {sensor.sensor_id} in {sensor.city} at {sensor.lat:.2f}, {sensor.lon:.2f}")
            else:
                print(f"❌ Failed to register sensor: {resp.status} {await resp.text()}")
    except Exception as e:
        print(f"❌ Registration error: {e}")

class Director:
    def __init__(self):
        self.trigger_city = None
        self.trigger_time = 0

    async def input_loop(self):
        loop = asyncio.get_running_loop()
        print("\n" + "="*50)
        print("🎬 DIRECTOR CONSOLE")
        print("Available targets:", ", ".join(CITIES.keys()))
        print("Type a city name to trigger an earthquake, or 'exit' to quit.")
        print("="*50 + "\n")
        
        while True:
            cmd = await loop.run_in_executor(None, input, "Hollywood> ")
            cmd = cmd.strip()
            if not cmd:
                continue
            if cmd.lower() == 'exit':
                os._exit(0)
            
            # Find closest match
            match = next((c for c in CITIES.keys() if c.lower().startswith(cmd.lower())), None)
            if match:
                print(f"\n💥 DIRECTOR: Triggering Earthquake in {match}!")
                self.trigger_city = match
                self.trigger_time = time.time()
                await asyncio.sleep(15.5)
                print("\n🛑 DIRECTOR: Earthquake simulation ended. Returning to background noise.\n")
            else:
                print(f"Unknown city. Try: {', '.join(CITIES.keys())}")


def generate_payload(s, quake_active, director):
    # Background ~M2-3 (below 4.5 threshold), quake ramps to M4.5+ (value 5500+ = threshold)
    # See backend/src/worker.py:estimate_magnitude() -> M=log10(value/100/1.6)+3.0
    # and tests/unit/test_magnitude.py: 5500 => M>=4.5
    value = secrets.choice(range(120, 750))
    if quake_active and s.city == director.trigger_city:
        elapsed = time.time() - director.trigger_time
        if elapsed < 5:
            value = secrets.choice(range(5500, 8500))
        else:
            value = secrets.choice(range(8500, 15000))

    timestamp_sec = int(time.time())
    timestamp_ms = int(time.time() * 1000)
    raw_payload = f"{value}:{timestamp_sec}"
    
    signature = s.private_key.sign(
        raw_payload.encode('utf-8'),
        ec.ECDSA(hashes.SHA256())
    )

    return {
        "sensor_id": s.sensor_id,
        "value": value,
        "device_timestamp": timestamp_sec,
        "device_timestamp_ms": timestamp_ms,
        "signature_hex": signature.hex(),
        "latitude": s.lat,
        "longitude": s.lon,
        "rssi": secrets.choice(range(-85, -39)),
        "free_heap": secrets.choice(range(100000, 250001)),
        "gnss_satellites": secrets.choice(range(4, 13))
    }

async def hollywood_loop(mqtt_client, sensors, director):
    print("🎥 HOLLYWOOD MODE ENGAGED. Sending telemetry...")
    while True:
        quake_active = director.trigger_city is not None and (time.time() - director.trigger_time) < 15
        if director.trigger_city and not quake_active:
            director.trigger_city = None # Reset after 15 seconds of shaking

        for s in sensors:
            if s.sensor_id == -1:
                continue

            payload = generate_payload(s, quake_active, director)
            try:
                await mqtt_client.publish(MQTT_TOPIC, json.dumps(payload))
            except Exception:
                pass

        await asyncio.sleep(1.0) # 1 update per second

async def _validate_fleet(sensors):
    """Check if the cached fleet still exists in the DB by probing one sensor."""
    if not sensors:
        return False
    test = sensors[0]
    try:
        async with aiohttp.ClientSession() as session:
            # Re-register with the same key; if the sensor exists the API returns 200/201
            payload = {
                "public_key_hex": test.public_key_hex,
                "mac_address": test.mac,
                "latitude": test.lat,
                "longitude": test.lon,
                "firmware_version": "2.1.1-HW",
                "enrollment_token": ENROLLMENT_TOKEN
            }
            async with session.post(f"{API_URL}/devices/register", json=payload) as resp:
                if resp.status in (200, 201):
                    data = await resp.json()
                    if data.get("sensor_id") == test.sensor_id:
                        return True
    except Exception:
        pass
    return False

async def _register_fleet():
    """Generate and register a brand new fleet."""
    sensors = []
    print("🏭 Generating new global fleet...")
    for city_name in CITIES.keys():
        for _ in range(7):
            base_lat, base_lon = CITIES[city_name]
            lat = base_lat + (-0.1 + secrets.SystemRandom().random() * (0.1 - -0.1))  # NOSONAR - geographic jitter, not cryptographic
            lon = base_lon + (-0.1 + secrets.SystemRandom().random() * (0.1 - -0.1))  # NOSONAR - geographic jitter, not cryptographic
            sensors.append(VirtualSensor(lat, lon, city_name))

    async with aiohttp.ClientSession() as session:
        await asyncio.gather(*[register_sensor(session, s) for s in sensors])

    # Save fleet
    fleet_data = [{
        "sensor_id": s.sensor_id, "mac": s.mac, "lat": s.lat, "lon": s.lon,
        "city": s.city, "priv_pem": s.get_priv_pem()
    } for s in sensors if s.sensor_id != -1]

    def write_fleet():
        with open(FLEET_FILE, 'w') as f:
            json.dump(fleet_data, f)
    await asyncio.to_thread(write_fleet)

    return sensors

async def load_or_create_fleet():
    if os.path.exists(FLEET_FILE):
        print("📂 Loading pre-registered fleet from fleet.json...")
        def read_fleet():
            with open(FLEET_FILE, 'r') as f:
                return json.load(f)
        data = await asyncio.to_thread(read_fleet)
        sensors = [VirtualSensor(
            s['lat'], s['lon'], s['city'],
            s['sensor_id'], s['mac'], s['priv_pem']
        ) for s in data]

        print("🔍 Validating fleet against database...")
        if await _validate_fleet(sensors):
            print("✅ Fleet is valid!")
            return sensors
        else:
            print("⚠️  Fleet is stale (DB was reset). Re-registering...")
            os.remove(FLEET_FILE)

    return await _register_fleet()

async def main():
    print("🎬 Welcome to QuakeGuard Hollywood Simulator!")
    
    sensors = await load_or_create_fleet()
    director = Director()

    _tls_ctx = None  # NOSONAR - TLS context configured below with secure defaults
    if MQTT_PORT == 8883:
        _tls_ctx = ssl.create_default_context()  # NOSONAR - Python 3.11 secure defaults (TLS 1.2+)
        _tls_ctx.minimum_version = ssl.TLSVersion.TLSv1_2  # NOSONAR - enforce TLS 1.2+
    try:
        async with aiomqtt.Client(
            hostname=MQTT_BROKER,
            port=MQTT_PORT,
            username=MQTT_USERNAME or None,
            password=MQTT_PASSWORD or None,
            tls_context=_tls_ctx,
        ) as mqtt_client:
            
            # Run both the telemetry loop and the interactive director console
            await asyncio.gather(
                hollywood_loop(mqtt_client, sensors, director),
                director.input_loop()
            )
    except Exception as e:
        print(f"❌ MQTT Connection Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
