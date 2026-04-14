from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Request, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy.orm import Session
from sqlalchemy import text as sql_text
from typing import List, Optional
import uuid
import datetime
import json
import asyncio

import os
import models
import schemas
import auth
from database import engine, get_db
from services import ETAService, LiveLocationService
from analytics import DelayPredictor, FraudDetector, RouteOptimizer, RegionalAnalytics
from cache import cache
import events
from events import EventType, emit
from logger import app_logger
import time

models.Base.metadata.create_all(bind=engine)

# --- Rate Limiter ---
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

app = FastAPI(title="Orbit Logistics API", version="1.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# --- WebSocket Connection Manager ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"[WS] Client connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        print(f"[WS] Client disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        data = json.dumps(message)
        for connection in list(self.active_connections):
            try:
                await connection.send_text(data)
            except Exception:
                self.disconnect(connection)

manager = ConnectionManager()

@app.websocket("/ws/updates")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # Keep alive
    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def _broadcast_event(event_type: str, payload: dict):
    await manager.broadcast({"type": event_type, **payload})

# ── Health & Monitoring ──────────────────────────────────────
@app.get("/health", tags=["monitoring"])
def health_check(db: Session = Depends(get_db)):
    """Uptime check endpoint — used by Docker, Render, UptimeRobot, etc."""
    try:
        db.execute(sql_text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "error"
    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "db": db_status,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
    }


# --- Background Task Helpers ---
def _log_audit(db: Session, user_id: int, action: str, target: str, details: str):
    audit = models.AuditLog(user_id=user_id, action=action, target_shipment=target, details=details)
    db.add(audit)
    db.commit()

def _emit_event(event_type: str, payload: dict):
    emit(event_type, payload)

# ── Analytics & Smart Features ───────────────────────────────
@app.get("/api/v1/analytics/regional", tags=["analytics"])
def get_regional_analytics(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_operator)):
    """Regional delivery performance heatmap data."""
    cached = cache.get("analytics:regional")
    if cached:
        return cached
    shipments = db.query(models.Shipment).all()
    data = [{"origin": s.origin, "destination": s.destination, "current_status": s.current_status.value, "current_lat": s.current_lat, "current_lng": s.current_lng} for s in shipments]
    result = RegionalAnalytics.compute(data)
    cache.set("analytics:regional", result, ttl_seconds=60)
    return result

@app.get("/api/v1/analytics/heatmap", tags=["analytics"])
def get_heatmap_data(db: Session = Depends(get_db)):
    """Returns lat/lng points for heatmap visualization."""
    shipments = db.query(models.Shipment).filter(
        models.Shipment.current_lat.isnot(None)
    ).all()
    return [{"lat": s.current_lat, "lng": s.current_lng, "status": s.current_status.value, "tracking_code": s.tracking_code} for s in shipments]

@app.get("/api/v1/shipments/{tracking_code}/delay-risk", tags=["analytics"])
def get_delay_risk(tracking_code: str, db: Session = Depends(get_db)):
    """ML-based delay prediction for a shipment."""
    shipment = db.query(models.Shipment).filter(models.Shipment.tracking_code == tracking_code).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return DelayPredictor.predict_delay_risk(
        created_at=shipment.created_at,
        estimated_delivery=shipment.estimated_delivery_date,
        current_status=shipment.current_status.value,
        num_events=len(shipment.events)
    )

@app.get("/api/v1/shipments/{tracking_code}/fraud-check", tags=["analytics"])
def get_fraud_check(tracking_code: str, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_operator)):
    """Fraud anomaly detection for a shipment's event history."""
    shipment = db.query(models.Shipment).filter(models.Shipment.tracking_code == tracking_code).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    events_data = [{"status": e.status.value, "lat": e.lat, "lng": e.lng, "timestamp": str(e.timestamp)} for e in shipment.events]
    return FraudDetector.analyze_events(events_data)

@app.get("/api/v1/analytics/route-optimize", tags=["analytics"])
def get_optimized_route(
    origin: str, destination: str,
    db: Session = Depends(get_db)
):
    """Greedy nearest-hub route optimization between two cities."""
    origin_hub = db.query(models.Hub).filter(models.Hub.name.contains(origin)).first()
    dest_hub = db.query(models.Hub).filter(models.Hub.name.contains(destination)).first()
    if not origin_hub or not dest_hub:
        raise HTTPException(status_code=404, detail="Hub not found for origin or destination")
    intermediate_hubs = db.query(models.Hub).filter(
        models.Hub.name != origin_hub.name,
        models.Hub.name != dest_hub.name
    ).all()
    hubs_data = [{"name": h.name, "lat": h.lat, "lng": h.lng} for h in intermediate_hubs]
    route = RouteOptimizer.optimize_route(origin_hub.lat, origin_hub.lng, dest_hub.lat, dest_hub.lng, hubs_data)
    return {
        "origin": {"name": origin_hub.name, "lat": origin_hub.lat, "lng": origin_hub.lng},
        "waypoints": route,
        "destination": {"name": dest_hub.name, "lat": dest_hub.lat, "lng": dest_hub.lng}
    }

# =====================================================
# API v1 Router
# =====================================================

# --- Auth ---
@app.post("/api/v1/auth/login", response_model=schemas.Token, tags=["auth"])
@limiter.limit("10/minute")
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    access_token = auth.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/v1/auth/me", response_model=schemas.UserResponse, tags=["auth"])
def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user

# --- Dashboard KPIs (Cached) ---
@app.get("/api/v1/dashboard/kpi", tags=["dashboard"])
@limiter.limit("30/minute")
def get_dashboard_kpis(request: Request, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_operator)):
    cached = cache.get("dashboard:kpi")
    if cached:
        return cached
    
    shipments = db.query(models.Shipment).all()
    total = len(shipments)
    delivered = sum(1 for s in shipments if s.current_status == models.ShippingStatus.DELIVERED)
    pending = sum(1 for s in shipments if s.current_status == models.ShippingStatus.CREATED)
    in_transit = sum(1 for s in shipments if s.current_status not in [models.ShippingStatus.DELIVERED, models.ShippingStatus.FAILED, models.ShippingStatus.CREATED])
    failed = sum(1 for s in shipments if s.current_status == models.ShippingStatus.FAILED)
    
    total_hours = 0
    delivery_count = 0
    for s in shipments:
        if s.current_status == models.ShippingStatus.DELIVERED:
            delivery_evt = next((e for e in reversed(s.events) if e.status == models.ShippingStatus.DELIVERED), None)
            if delivery_evt:
                total_hours += (delivery_evt.timestamp - s.created_at).total_seconds() / 3600
                delivery_count += 1
    
    result = {
        "total": total, "delivered": delivered, "pending": pending,
        "in_transit": in_transit, "failed": failed,
        "avg_delivery_time_hours": round(total_hours / delivery_count, 1) if delivery_count > 0 else 0
    }
    cache.set("dashboard:kpi", result, ttl_seconds=30)
    return result

# --- Shipments (Paginated, Filtered, Sorted) ---
@app.post("/api/v1/shipments", response_model=schemas.ShipmentResponse, tags=["shipments"])
@limiter.limit("20/minute")
def create_shipment(
    request: Request,
    shipment: schemas.ShipmentCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_operator)
):
    tracking_code = f"TRK-{uuid.uuid4().hex[:8].upper()}"
    
    origin_hub = db.query(models.Hub).filter(models.Hub.name.contains(shipment.origin)).first()
    dest_hub = db.query(models.Hub).filter(models.Hub.name.contains(shipment.destination)).first()
    o_lat, o_lng = (origin_hub.lat, origin_hub.lng) if origin_hub else (20.5937, 78.9629)
    d_lat, d_lng = (dest_hub.lat, dest_hub.lng) if dest_hub else (20.5937, 78.9629)
    
    eta = ETAService.calculate_eta(o_lat, o_lng, d_lat, d_lng, shipment.weight, shipment.type)
    
    db_shipment = models.Shipment(
        tracking_code=tracking_code,
        customer_email=shipment.customer_email,
        customer_phone=shipment.customer_phone,
        origin=shipment.origin, destination=shipment.destination,
        weight=shipment.weight, type=shipment.type,
        current_status=models.ShippingStatus.CREATED,
        current_lat=o_lat, current_lng=o_lng,
        estimated_delivery_date=eta
    )
    customer = db.query(models.User).filter(models.User.email == shipment.customer_email).first()
    if customer:
        db_shipment.customer_id = customer.id
    
    db.add(db_shipment)
    db.commit()
    db.refresh(db_shipment)
    
    db.add(models.TrackingEvent(
        shipment_id=db_shipment.id, status=models.ShippingStatus.CREATED,
        location_name=shipment.origin, lat=o_lat, lng=o_lng,
        description="Shipment label created."
    ))
    db.commit()
    
    # Invalidate cache + fire events
    cache.delete("dashboard:kpi")
    event_payload = {
        "tracking_code": tracking_code, "status": "CREATED",
        "location": shipment.origin,
        "customer_email": shipment.customer_email,
        "customer_phone": shipment.customer_phone
    }
    background_tasks.add_task(_emit_event, EventType.SHIPMENT_CREATED, event_payload)
    background_tasks.add_task(_log_audit, db, current_user.id, "CREATED", tracking_code, f"New {shipment.type} shipment from {shipment.origin} to {shipment.destination}.")
    
    return db_shipment

@app.get("/api/v1/shipments", tags=["shipments"])
@limiter.limit("60/minute")
def get_shipments(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status"),
    sort_by: Optional[str] = Query("created_at", description="Sort field: created_at or weight"),
    sort_order: Optional[str] = Query("desc", description="asc or desc"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_operator)
):
    query = db.query(models.Shipment)
    
    # Filtering
    if status:
        try:
            status_enum = models.ShippingStatus[status.upper()]
            query = query.filter(models.Shipment.current_status == status_enum)
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Invalid status. Choose from: {[s.value for s in models.ShippingStatus]}")
    
    # Sorting
    sort_col = getattr(models.Shipment, sort_by, models.Shipment.created_at)
    query = query.order_by(sort_col.desc() if sort_order == "desc" else sort_col.asc())
    
    total = query.count()
    shipments = query.offset((page - 1) * per_page).limit(per_page).all()
    
    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
        "results": [schemas.ShipmentResponse.model_validate(s) for s in shipments]
    }

# --- Public Search (rate limited, cached) ---
@app.get("/api/v1/track/search", tags=["tracking"])
@limiter.limit("20/minute")
def search_shipment(request: Request, query: str, db: Session = Depends(get_db)):
    cache_key = f"track:{query}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    shipments = db.query(models.Shipment).filter(
        (models.Shipment.tracking_code == query) |
        (models.Shipment.customer_email == query) |
        (models.Shipment.customer_phone == query)
    ).all()
    
    if not shipments:
        raise HTTPException(status_code=404, detail="No shipments found.")
    
    result = [schemas.ShipmentResponse.model_validate(s) for s in shipments]
    cache.set(cache_key, [r.model_dump() for r in result], ttl_seconds=15)
    return result

@app.get("/api/v1/shipments/{tracking_code}", response_model=schemas.ShipmentResponse, tags=["shipments"])
def get_shipment(tracking_code: str, db: Session = Depends(get_db)):
    shipment = db.query(models.Shipment).filter(models.Shipment.tracking_code == tracking_code).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return shipment

@app.post("/api/v1/shipments/{tracking_code}/status", response_model=schemas.TrackingEventResponse, tags=["shipments"])
def add_tracking_event(
    tracking_code: str,
    event: schemas.TrackingEventCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_operator)
):
    shipment = db.query(models.Shipment).filter(models.Shipment.tracking_code == tracking_code).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    
    db_event = models.TrackingEvent(shipment_id=shipment.id, **event.model_dump())
    db.add(db_event)
    
    shipment.current_status = event.status
    shipment.current_lat = event.lat
    shipment.current_lng = event.lng
    db.commit()
    db.refresh(db_event)
    
    # Invalidate caches
    cache.delete("dashboard:kpi")
    cache.delete(f"track:{tracking_code}")
    cache.delete(f"track:{shipment.customer_email}")
    cache.delete(f"track:{shipment.customer_phone}")
    
    is_delivered = event.status == models.ShippingStatus.DELIVERED
    event_type = EventType.SHIPMENT_DELIVERED if is_delivered else EventType.SHIPMENT_UPDATED
    event_payload = {
        "tracking_code": tracking_code, "status": event.status.value,
        "location": event.location_name,
        "customer_email": shipment.customer_email,
        "customer_phone": shipment.customer_phone
    }
    background_tasks.add_task(_emit_event, event_type, event_payload)
    background_tasks.add_task(_log_audit, db, current_user.id, "STATUS_UPDATE", tracking_code, f"Updated to {event.status.value} at {event.location_name}")
    
    return db_event

@app.post("/api/v1/shipments/{tracking_code}/pulse", tags=["simulation"])
def simulate_live_movement(tracking_code: str, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_operator)):
    shipment = db.query(models.Shipment).filter(models.Shipment.tracking_code == tracking_code).first()
    if not shipment:
        raise HTTPException(status_code=404)
    dest_hub = db.query(models.Hub).filter(models.Hub.name.contains(shipment.destination)).first()
    if not dest_hub:
        raise HTTPException(status_code=400, detail="Destination hub coordinates unknown.")
    new_lat, new_lng = LiveLocationService.simulate_movement(
        shipment.current_lat, shipment.current_lng, dest_hub.lat, dest_hub.lng
    )
    shipment.current_lat = new_lat
    shipment.current_lng = new_lng
    db.commit()
    cache.delete(f"track:{tracking_code}")
    return {"lat": new_lat, "lng": new_lng}

# --- Audit Logs ---
@app.get("/api/v1/audit", response_model=List[schemas.AuditLogResponse], tags=["admin"])
def get_audit_logs(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_admin)
):
    query = db.query(models.AuditLog).order_by(models.AuditLog.timestamp.desc())
    total = query.count()
    logs = query.offset((page - 1) * per_page).limit(per_page).all()
    return logs
