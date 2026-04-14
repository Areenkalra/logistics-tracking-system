from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime
from models import ShippingStatus, UserRole

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: UserRole
    phone: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int

    class Config:
        from_attributes = True

class HubBase(BaseModel):
    name: str
    lat: float
    lng: float

class HubCreate(HubBase):
    pass

class HubResponse(HubBase):
    id: int

    class Config:
        from_attributes = True

class TrackingEventBase(BaseModel):
    status: ShippingStatus
    location_name: str
    lat: float
    lng: float
    description: Optional[str] = None
    hub_id: Optional[int] = None

class TrackingEventCreate(TrackingEventBase):
    pass

class TrackingEventResponse(TrackingEventBase):
    id: int
    shipment_id: int
    timestamp: datetime

    class Config:
        from_attributes = True

class ShipmentBase(BaseModel):
    origin: str
    destination: str
    weight: float
    type: str # FRAGILE, EXPRESS, STANDARD
    customer_email: str
    customer_phone: str

class ShipmentCreate(ShipmentBase):
    pass

class ShipmentResponse(ShipmentBase):
    id: int
    tracking_code: str
    current_status: ShippingStatus
    created_at: datetime
    events: List[TrackingEventResponse] = []
    customer_email: str
    customer_phone: str
    weight: float
    type: str
    current_lat: Optional[float] = None
    current_lng: Optional[float] = None
    estimated_delivery_date: Optional[datetime] = None

    class Config:
        from_attributes = True

class AuditLogResponse(BaseModel):
    id: int
    user_id: int
    action: str
    target_shipment: str
    details: str
    timestamp: datetime

    class Config:
        from_attributes = True
