"""
Event-Based Architecture
Events are emitted and processed asynchronously via FastAPI BackgroundTasks.
To upgrade to a real message broker (Celery + Redis / RabbitMQ),
replace the handler registration with celery task calls.
"""
from typing import Callable, Dict, List
from services import NotificationService
import models

# --- Event Types ---
class EventType:
    SHIPMENT_CREATED = "shipment.created"
    SHIPMENT_UPDATED = "shipment.updated"
    SHIPMENT_DELIVERED = "shipment.delivered"

# --- Simple In-Process Event Bus ---
_handlers: Dict[str, List[Callable]] = {}

def on(event_type: str, handler: Callable):
    """Register a handler for an event type."""
    if event_type not in _handlers:
        _handlers[event_type] = []
    _handlers[event_type].append(handler)

def emit(event_type: str, payload: dict):
    """Synchronously dispatch all registered handlers for an event."""
    for handler in _handlers.get(event_type, []):
        try:
            handler(payload)
        except Exception as e:
            print(f"[EVENT BUS ERROR] Handler failed for '{event_type}': {e}")

# --- Register Notification Handlers ---
def _handle_shipment_updated(payload: dict):
    tracking_code = payload.get("tracking_code")
    status = payload.get("status", "UPDATED")
    location = payload.get("location", "Unknown")
    email = payload.get("customer_email")
    phone = payload.get("customer_phone")
    
    msg = f"[Orbit Logistics] Your shipment {tracking_code} is now {status} at {location}."
    subject = f"Shipment {tracking_code} - Status Update"
    
    if email:
        NotificationService.send_email(email, subject, msg)
    if phone:
        NotificationService.send_sms(phone, msg)

def _handle_shipment_delivered(payload: dict):
    tracking_code = payload.get("tracking_code")
    email = payload.get("customer_email")
    phone = payload.get("customer_phone")
    
    msg = f"[Orbit Logistics] Great news! Your shipment {tracking_code} has been DELIVERED. Thank you for choosing Orbit Logistics!"
    subject = f"Delivery Confirmed - {tracking_code}"
    
    if email:
        NotificationService.send_email(email, subject, msg)
    if phone:
        NotificationService.send_sms(phone, msg)

# Wire up events
on(EventType.SHIPMENT_CREATED, _handle_shipment_updated)
on(EventType.SHIPMENT_UPDATED, _handle_shipment_updated)
on(EventType.SHIPMENT_DELIVERED, _handle_shipment_delivered)
