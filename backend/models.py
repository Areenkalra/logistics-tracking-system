from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from database import Base
import datetime
import enum

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String) # e.g., "STATUS_UPDATE"
    target_shipment = Column(String)
    details = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    OPERATOR = "OPERATOR"
    CUSTOMER = "CUSTOMER"

class ShippingStatus(str, enum.Enum):
    CREATED = "CREATED"
    PICKED = "PICKED"
    IN_TRANSIT = "IN_TRANSIT"
    OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    full_name = Column(String)
    hashed_password = Column(String)
    role = Column(Enum(UserRole), default=UserRole.CUSTOMER)
    phone = Column(String, index=True, nullable=True)

    shipments = relationship("Shipment", back_populates="customer")

class Hub(Base):
    __tablename__ = "hubs"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    lat = Column(Float)
    lng = Column(Float)
    
class Shipment(Base):
    __tablename__ = "shipments"

    id = Column(Integer, primary_key=True, index=True)
    tracking_code = Column(String, unique=True, index=True)
    customer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    customer_email = Column(String, index=True)
    customer_phone = Column(String, index=True)
    
    origin = Column(String)
    destination = Column(String)
    weight = Column(Float)
    type = Column(String) # e.g., 'FRAGILE', 'STANDARD', 'EXPRESS'
    
    current_status = Column(Enum(ShippingStatus), default=ShippingStatus.CREATED)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    current_lat = Column(Float, nullable=True)
    current_lng = Column(Float, nullable=True)
    estimated_delivery_date = Column(DateTime, nullable=True)
    
    customer = relationship("User", back_populates="shipments")
    events = relationship("TrackingEvent", back_populates="shipment", order_by="desc(TrackingEvent.timestamp)", cascade="all, delete-orphan")

class TrackingEvent(Base):
    __tablename__ = "tracking_events"

    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id"))
    status = Column(Enum(ShippingStatus))
    location_name = Column(String)
    hub_id = Column(Integer, ForeignKey("hubs.id"), nullable=True)
    lat = Column(Float)
    lng = Column(Float)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    description = Column(String)

    shipment = relationship("Shipment", back_populates="events")
    hub = relationship("Hub")
