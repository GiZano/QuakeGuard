import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from dotenv import load_dotenv

_ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend", ".env")
load_dotenv(_ENV_PATH, override=False)

POSTGRES_USER = os.getenv("POSTGRES_USER", "quake_admin")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "quake_pass")
POSTGRES_DB = os.getenv("POSTGRES_DB", "quakeguard")
DATABASE_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@localhost:5432/{POSTGRES_DB}"

CITIES = [
    {"name": "Tokyo", "lat": 35.6895, "lon": 139.6917, "radius": 2.0},
    {"name": "San Francisco", "lat": 37.7749, "lon": -122.4194, "radius": 2.0},
    {"name": "Mexico City", "lat": 19.4326, "lon": -99.1332, "radius": 2.0},
    {"name": "Santiago", "lat": -33.4489, "lon": -70.6693, "radius": 2.0},
    {"name": "Naples", "lat": 40.8518, "lon": 14.2681, "radius": 2.0},
    {"name": "Los Angeles", "lat": 34.0522, "lon": -118.2437, "radius": 2.0},
    {"name": "Istanbul", "lat": 41.0082, "lon": 28.9784, "radius": 2.0},
    {"name": "Jakarta", "lat": -6.2088, "lon": 106.8456, "radius": 2.0},
]

async def seed():
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        for city in CITIES:
            # Create a simple polygon (bounding box) around the city
            lat = city["lat"]
            lon = city["lon"]
            r = city["radius"]
            
            # WKT Polygon: minLon minLat, maxLon minLat, maxLon maxLat, minLon maxLat, minLon minLat
            polygon_wkt = f"POLYGON(({lon-r} {lat-r}, {lon+r} {lat-r}, {lon+r} {lat+r}, {lon-r} {lat+r}, {lon-r} {lat-r}))"
            
            # Insert or update
            query = text("""
                INSERT INTO zones (city, geom) 
                VALUES (:city, ST_GeomFromText(:wkt, 4326))
                ON CONFLICT (city) DO UPDATE SET geom = EXCLUDED.geom
            """)
            await session.execute(query, {"city": city["name"], "wkt": polygon_wkt})
            print(f"✅ Seeded Zone: {city['name']}")
        
        await session.commit()
    print("🌍 World Zones successfully seeded!")

if __name__ == "__main__":
    asyncio.run(seed())
