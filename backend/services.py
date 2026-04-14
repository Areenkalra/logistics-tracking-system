import math
import datetime
import random
from typing import Optional

class NotificationService:
    @staticmethod
    def send_sms(phone: str, message: str):
        # Mock Twilio Implementation
        if not phone:
            return
        print(f"\n[TWILIO-MOCK] Sending SMS to +91-{phone}")
        print(f"-------------\n{message}\n-------------\n")

    @staticmethod
    def send_email(email: str, subject: str, body: str):
        # Mock SendGrid Implementation
        if not email:
            return
        print(f"\n[SENDGRID-MOCK] Dispatching Email to '{email}'")
        print(f"Subject: {subject}")
        print(f"Body:\n{body}\n-------------\n")

class ML_ETAPredictor:
    """A simulated ML-based ETA predictor for visual 'wow' factor."""
    @staticmethod
    def predict_hours(distance: float, weight: float, pkg_type: str) -> float:
        # Simple simulated weights for different package types
        type_multiplier = {
            "EXPRESS": 0.8,
            "STANDARD": 1.2,
            "FRAGILE": 1.5
        }
        mult = type_multiplier.get(pkg_type.upper(), 1.0)
        
        # Base speed 60km/h + variation based on weight
        speed = 60.0 - (weight * 0.2) 
        if speed < 30.0: speed = 30.0
        
        base_hours = distance / speed
        return base_hours * mult + random.uniform(1.0, 4.0) # Random variance for 'realism'

class ETAService:
    @staticmethod
    def haversine(lat1, lon1, lat2, lon2):
        if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
            return 500.0
        R = 6371.0 # Earth radius
        dLat = math.radians(lat2 - lat1)
        dLon = math.radians(lon2 - lon1)
        a = math.sin(dLat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    @staticmethod
    def calculate_eta(origin_lat: float, origin_lng: float, dest_lat: float, dest_lng: float, weight: float = 1.0, pkg_type: str = "STANDARD") -> datetime.datetime:
        distance_km = ETAService.haversine(origin_lat, origin_lng, dest_lat, dest_lng)
        
        # Use our "ML" predictor
        predicted_hours = ML_ETAPredictor.predict_hours(distance_km, weight, pkg_type)
        
        # Add 12 hours for hub processing organically
        total_hours = predicted_hours + 12.0
        
        return datetime.datetime.utcnow() + datetime.timedelta(hours=total_hours)

class LiveLocationService:
    @staticmethod
    def simulate_movement(current_lat: float, current_lng: float, dest_lat: float, dest_lng: float, step_size: float = 0.05):
        """Calculates the next step in simulated movement towards a destination."""
        if current_lat is None or dest_lat is None: return current_lat, current_lng
        
        d_lat = dest_lat - current_lat
        d_lng = dest_lng - current_lng
        dist = math.sqrt(d_lat**2 + d_lng**2)
        
        if dist < step_size:
            return dest_lat, dest_lng
        
        new_lat = current_lat + (d_lat / dist) * step_size
        new_lng = current_lng + (d_lng / dist) * step_size
        return new_lat, new_lng
