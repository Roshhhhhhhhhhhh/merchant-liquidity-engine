import datetime
from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.orm import relationship
from app.database.base import Base


class Merchant(Base):
    __tablename__ = "merchants"

    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    trade_name = Column(String(200), nullable=False)
    gst_number = Column(String(20), nullable=False)
    industry = Column(String(100), nullable=False)
    address = Column(Text, nullable=True)
    base_currency = Column(String(10), default="INR", nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

    products = relationship("Product", back_populates="merchant", cascade="all, delete-orphan")
    customers = relationship("Customer", back_populates="merchant", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="merchant", cascade="all, delete-orphan")
    receivables = relationship("Receivable", back_populates="merchant", cascade="all, delete-orphan")
    payables = relationship("Payable", back_populates="merchant", cascade="all, delete-orphan")
    snapshots = relationship("EconomicSnapshot", back_populates="merchant", cascade="all, delete-orphan")
    activities = relationship("ActivityEvent", back_populates="merchant", cascade="all, delete-orphan")
