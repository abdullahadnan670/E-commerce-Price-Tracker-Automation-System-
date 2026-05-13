from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)

    # A user can have multiple tracked products
    products = relationship("Product", back_populates="owner")

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id")) # Links to the User table
    mission_id = Column(Integer, index=True)
    category = Column(String)
    
    name = Column(String)
    price = Column(String)
    numeric_price = Column(Float, nullable=True)
    target_price = Column(Float, nullable=True) # For the email alerts
    url = Column(String)
    image_url = Column(String, nullable=True)   # For the cool Blazor UI
    source = Column(String)
    is_saved = Column(Boolean, default=False)
    
    owner = relationship("User", back_populates="products")
    history = relationship("PriceHistory", back_populates="product")
    alert_sent = Column(Boolean, default=False)

class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    price = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow) # Automatically logs exact time

    product = relationship("Product", back_populates="history")