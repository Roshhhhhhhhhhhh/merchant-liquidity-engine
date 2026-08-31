import datetime
from sqlalchemy import Column, String, DateTime, Numeric, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.database.base import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String(50), primary_key=True, index=True)
    merchant_id = Column(String(50), ForeignKey("merchants.id"), nullable=False, index=True)
    customer_id = Column(String(50), ForeignKey("customers.id"), nullable=False, index=True)
    product_id = Column(String(50), ForeignKey("products.id"), nullable=False, index=True)
    reference_id = Column(String(100), unique=True, index=True, nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(14, 2), nullable=False)
    gross_value = Column(Numeric(14, 2), nullable=False)
    cost_value = Column(Numeric(14, 2), nullable=False)
    net_margin_pct = Column(Numeric(6, 2), nullable=False)
    payment_status = Column(String(30), default="Captured", nullable=False)  # Captured, Pending, Refunded, Failed
    settlement_status = Column(String(30), default="Settled", nullable=False)  # Settled, In Transit, Pending
    payment_method = Column(String(50), default="NEFT/RTGS", nullable=False)
    channel = Column(String(50), default="Direct B2B", nullable=False)
    source = Column(String(50), default="direct_b2b", nullable=False)  # direct_b2b, agentic_negotiation
    negotiation_id = Column(String(50), nullable=True, index=True)
    payment_order_id = Column(String(50), nullable=True, index=True)
    razorpay_payment_id = Column(String(100), nullable=True, index=True)
    razorpay_order_id = Column(String(100), nullable=True, index=True)
    paid_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False, index=True)

    merchant = relationship("Merchant", back_populates="transactions")
    customer = relationship("Customer", back_populates="transactions")
    product = relationship("Product", back_populates="transactions")
