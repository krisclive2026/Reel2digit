import datetime
import uuid
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

def generate_order_number():
    return f"RTD-{datetime.datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    street_address = Column(String, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    postal_code = Column(String, nullable=True)
    country = Column(String, default="India")
    role = Column(String, default="customer")  # "customer" or "admin"
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    orders = relationship("Order", back_populates="user", cascade="all, delete-orphan")
    feedbacks = relationship("Feedback", back_populates="user")

class PricingConfig(Base):
    __tablename__ = "pricing_configs"

    id = Column(Integer, primary_key=True, index=True)
    unit_price = Column(Float, default=15.00)
    shipping_flat = Column(Float, default=8.99)
    max_cassettes = Column(Integer, default=50)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String, unique=True, index=True, default=generate_order_number)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String, default="draft")  # draft, paid, label_ready, in_transit, received, processing, completed, cancelled
    cassette_count = Column(Integer, nullable=False)
    format = Column(String, default="MP3")  # MP3 or MP4
    unit_price = Column(Float, nullable=False)
    shipping_fee = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user = relationship("User", back_populates="orders")
    cassettes = relationship("Cassette", back_populates="order", cascade="all, delete-orphan")
    shipping_label = relationship("ShippingLabel", back_populates="order", uselist=False, cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="order", cascade="all, delete-orphan")
    media_assets = relationship("MediaAsset", back_populates="order", cascade="all, delete-orphan")
    feedback = relationship("Feedback", back_populates="order", uselist=False, cascade="all, delete-orphan")

class Cassette(Base):
    __tablename__ = "cassettes"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    tag_name = Column(String, nullable=False)
    sequence = Column(Integer, nullable=False)

    order = relationship("Order", back_populates="cassettes")

class ShippingLabel(Base):
    __tablename__ = "shipping_labels"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, unique=True)
    tracking_number = Column(String, unique=True, nullable=False)
    carrier = Column(String, default="India Post")
    label_url = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    order = relationship("Order", back_populates="shipping_label")

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    amount = Column(Float, nullable=False)
    provider = Column(String, default="demo_stripe")
    status = Column(String, default="captured")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    order = relationship("Order", back_populates="payments")

class MediaAsset(Base):
    __tablename__ = "media_assets"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    cassette_id = Column(Integer, ForeignKey("cassettes.id"), nullable=True)
    file_name = Column(String, nullable=False)
    file_url = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    order = relationship("Order", back_populates="media_assets")

class Feedback(Base):
    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, unique=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1 to 5
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    order = relationship("Order", back_populates="feedback")
    user = relationship("User", back_populates="feedbacks")
