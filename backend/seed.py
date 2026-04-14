from database import engine, SessionLocal
import models
import auth
import random
import uuid
from services import ETAService

# Indian Coordinates
LOCATIONS = [
    {"name": "Delhi", "lat": 28.7041, "lng": 77.1025},
    {"name": "Mumbai", "lat": 19.0760, "lng": 72.8777},
    {"name": "Bangalore", "lat": 12.9716, "lng": 77.5946},
    {"name": "Chennai", "lat": 13.0827, "lng": 80.2707},
    {"name": "Kolkata", "lat": 22.5726, "lng": 88.3639},
    {"name": "Hyderabad", "lat": 17.3850, "lng": 78.4867},
]

def seed_db():
    print("Creating tables...")
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    print("Clearing existing data...")
    db.query(models.TrackingEvent).delete()
    db.query(models.Shipment).delete()
    db.query(models.User).delete()
    db.query(models.Hub).delete()
    db.commit()

    print("Creating default users...")
    admin = models.User(email="admin@orbit.in", full_name="System Admin", hashed_password=auth.get_password_hash("admin123"), role=models.UserRole.ADMIN)
    operator = models.User(email="op@orbit.in", full_name="Delhi Operator", hashed_password=auth.get_password_hash("op123"), role=models.UserRole.OPERATOR)
    customer = models.User(email="customer@gmail.com", full_name="Rahul", hashed_password=auth.get_password_hash("cust123"), role=models.UserRole.CUSTOMER, phone="9876543210")
    db.add_all([admin, operator, customer])
    db.commit()

    print("Creating Indian Hubs...")
    db_hubs = []
    for loc in LOCATIONS:
        hub = models.Hub(name=f"{loc['name']} Master Hub", lat=loc["lat"], lng=loc["lng"])
        db.add(hub)
        db_hubs.append(hub)
    db.commit()

    print("Generating mock shipments...")
    
    # Predefined samples
    sample_data = [
        {"code": "TRK-SAMPLE01", "origin": LOCATIONS[0], "dest": LOCATIONS[1], "status": models.ShippingStatus.IN_TRANSIT, "email": "sample1@gmail.com"},
        {"code": "TRK-SAMPLE02", "origin": LOCATIONS[2], "dest": LOCATIONS[3], "status": models.ShippingStatus.DELIVERED, "email": "sample2@gmail.com"},
    ]

    for s_info in sample_data:
        origin = s_info["origin"]
        dest = s_info["dest"]
        eta = ETAService.calculate_eta(origin["lat"], origin["lng"], dest["lat"], dest["lng"])
        
        db_s = models.Shipment(
            tracking_code=s_info["code"],
            customer_email=s_info["email"],
            customer_phone="9988776655",
            origin=origin["name"],
            destination=dest["name"],
            weight=5.0,
            type="EXPRESS",
            current_status=s_info["status"],
            current_lat=origin["lat"],
            current_lng=origin["lng"],
            estimated_delivery_date=eta,
            customer_id=customer.id
        )
        db.add(db_s)
        db.commit()
        db.refresh(db_s)

        # Initial event
        db.add(models.TrackingEvent(
            shipment_id=db_s.id, status=models.ShippingStatus.CREATED,
            location_name=origin["name"], lat=origin["lat"], lng=origin["lng"],
            description="Shipment label created."
        ))
        
        if s_info["status"] != models.ShippingStatus.CREATED:
             db.add(models.TrackingEvent(
                shipment_id=db_s.id, status=models.ShippingStatus.IN_TRANSIT,
                location_name=f"{origin['name']} Hub", lat=origin["lat"]+0.1, lng=origin["lng"]+0.1,
                description="Package scanned at Regional Hub."
            ))
             db_s.current_lat = origin["lat"]+0.1
             db_s.current_lng = origin["lng"]+0.1
        
        if s_info["status"] == models.ShippingStatus.DELIVERED:
            db.add(models.TrackingEvent(
                shipment_id=db_s.id, status=models.ShippingStatus.DELIVERED,
                location_name=dest["name"], lat=dest["lat"], lng=dest["lng"],
                description="Package delivered successfully."
            ))
            db_s.current_lat = dest["lat"]
            db_s.current_lng = dest["lng"]

    for i in range(5):
        origin = random.choice(LOCATIONS)
        destination = random.choice([loc for loc in LOCATIONS if loc["name"] != origin["name"]])
        
        db_shipment = models.Shipment(
            tracking_code=f"TRK-{uuid.uuid4().hex[:8].upper()}",
            customer_email="customer@gmail.com" if i % 2 == 0 else f"test{i}@gmail.com",
            customer_phone="9876543210" if i % 2 == 0 else f"999999999{i}",
            origin=origin["name"],
            destination=destination["name"],
            weight=round(random.uniform(1.0, 50.0), 2),
            type=random.choice(["STANDARD", "EXPRESS", "FRAGILE"]),
            current_status=models.ShippingStatus.CREATED,
            customer_id=customer.id if i % 2 == 0 else None
        )
        db.add(db_shipment)
        db.commit()
        db.refresh(db_shipment)
        
        # Initial event
        init_event = models.TrackingEvent(
            shipment_id=db_shipment.id,
            status=models.ShippingStatus.CREATED,
            location_name=origin["name"],
            lat=origin["lat"],
            lng=origin["lng"],
            description="Shipment label created electronically."
        )
        db.add(init_event)
        
        target_status = random.choice([models.ShippingStatus.IN_TRANSIT, models.ShippingStatus.OUT_FOR_DELIVERY, models.ShippingStatus.DELIVERED, models.ShippingStatus.CREATED])
        if target_status == models.ShippingStatus.CREATED:
            db.commit()
            continue
            
        evt1 = models.TrackingEvent(
            shipment_id=db_shipment.id,
            status=models.ShippingStatus.IN_TRANSIT,
            location_name=f"{origin['name']} Hub",
            lat=origin["lat"] + random.uniform(-0.05, 0.05),
            lng=origin["lng"] + random.uniform(-0.05, 0.05),
            description="Package scanned at regional hub."
        )
        db.add(evt1)
        db_shipment.current_status = models.ShippingStatus.IN_TRANSIT
        
        if target_status in [models.ShippingStatus.OUT_FOR_DELIVERY, models.ShippingStatus.DELIVERED]:
            evt2 = models.TrackingEvent(
                shipment_id=db_shipment.id,
                status=models.ShippingStatus.OUT_FOR_DELIVERY,
                location_name=f"{destination['name']} Local Facility",
                lat=destination["lat"] + random.uniform(-0.02, 0.02),
                lng=destination["lng"] + random.uniform(-0.02, 0.02),
                description="Package is out for delivery."
            )
            db.add(evt2)
            db_shipment.current_status = models.ShippingStatus.OUT_FOR_DELIVERY
            
        if target_status == models.ShippingStatus.DELIVERED:
            evt3 = models.TrackingEvent(
                shipment_id=db_shipment.id,
                status=models.ShippingStatus.DELIVERED,
                location_name=destination["name"],
                lat=destination["lat"],
                lng=destination["lng"],
                description="Package securely delivered to recipient."
            )
            db.add(evt3)
            db_shipment.current_status = models.ShippingStatus.DELIVERED
            
        db.commit()

    print("Seed complete! Indian dataset loaded.")
    db.close()

if __name__ == "__main__":
    seed_db()
