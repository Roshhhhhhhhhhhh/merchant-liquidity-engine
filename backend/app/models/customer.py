import datetime
from sqlalchemy import Column, String, DateTime, Numeric, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.database.base import Base


class Customer(Base):
    __tablename__ = "customers"

    id = Column(String(50), primary_key=True, index=True)
    merchant_id = Column(String(50), ForeignKey("merchants.id"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    company_name = Column(String(200), nullable=False)
    email = Column(String(150), nullable=False)
    phone = Column(String(30), nullable=True)
    gstin = Column(String(20), nullable=True)
    credit_limit = Column(Numeric(14, 2), default=0, nullable=False)
    credit_terms_days = Column(Integer, default=30, nullable=False)
    total_revenue = Column(Numeric(14, 2), default=0, nullable=False)
    customer_tier = Column(String(30), default="Standard", nullable=False)  # Enterprise, Tier-1, Standard
    payment_score = Column(Integer, default=80, nullable=False)  # 0 to 100
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

    merchant = relationship("Merchant", back_populates="customers")
    transactions = relationship("Transaction", back_populates="customer")
    receivables = relationship("Receivable", back_populates="customer")
