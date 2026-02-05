from database import engine, Base
from models import Zone, Misurator, Misuration
from sqlalchemy.orm import Session

def init_database():
    # Create tables
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables succesfully created!")

    # Put example data
    print("Inserting example data")
    db = Session(bind=engine)

    try:
        # Create Zones
        zone1 = Zone(city="Milano")
        zone2 = Zone(city="Bergamo")
        zone3 = Zone(city="Treviglio")
        zone4 = Zone(city="Cologno al Serio")

        db.add_all([zone1, zone2, zone3])
        db.commit()

        # Create Misurators
        misurator1 = Misurator(active=False, zone_id=4)
        misurator2 = Misurator(active=False, zone_id=4)

        db.add_all([misurator1, misurator2])
        db.commit()

        # Create Misurations
        misuration1 = Misuration(value=100, misurator_id=1)
        misuration2 = Misuration(value=200, misurator_id=2)

        db.add_all([misuration1, misuration2])
        db.commit()

        print("Example data succesfully loaded!")

    except Exception as e:
        print(f"Error caught while inserting data: {e}")
        db.rollback()

    finally:
        db.close()

if __name__ == "__main__":
    init_database()