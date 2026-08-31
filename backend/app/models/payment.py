from datetime import datetime
from sqlalchemy import Column, String, DateTime, Numeric, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database.base import Base


class PaymentOrder(Base):
    """
    Represents a formal commercial payment order created from an accepted negotiation agreement.
    Links the immutable negotiation terms to Razorpay Test Mode Order identifiers and lifecycle.
    """
    __tablename__ = "payment_orders"

    id = Column(String(50), primary_key=True, index=True)
    negotiation_id = Column(String(50), ForeignKey("negotiation_sessions.id"), nullable=False, index=True)
    offer_id = Column(String(50), ForeignKey("negotiation_offers.id"), nullable=True)
    merchant_id = Column(String(50), ForeignKey("merchants.id"), nullable=False, index=True)
    razorpay_order_id = Column(String(100), unique=True, index=True, nullable=False)
    razorpay_payment_id = Column(String(100), nullable=True, index=True)
    razorpay_signature = Column(String(255), nullable=True)
    amount = Column(Numeric(14, 2), nullable=False)
    currency = Column(String(10), default="INR", nullable=False)
    status = Column(String(30), default="CREATED", nullable=False)  # CREATED, PAYMENT_PENDING, PAID, FAILED, EXPIRED, CANCELLED
    receipt = Column(String(100), unique=True, nullable=False)
    before_state_json = Column(Text, nullable=True)  # Snapshot of balance sheet before payment
    after_state_json = Column(Text, nullable=True)   # Snapshot of balance sheet after payment
    projected_evc = Column(Numeric(14, 2), nullable=True)
    realized_evc = Column(Numeric(14, 2), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    paid_at = Column(DateTime, nullable=True)

    negotiation = relationship("NegotiationSession", backref="payment_orders")
    offer = relationship("NegotiationOffer", backref="payment_orders")
    merchant = relationship("Merchant", backref="payment_orders")


class PaymentWebhookLog(Base):
    """
    Immutable audit log of all incoming Razorpay webhooks for duplicate protection and event idempotency.
    """
    __tablename__ = "payment_webhook_logs"

    id = Column(String(50), primary_key=True, index=True)
    event_id = Column(String(100), unique=True, index=True, nullable=False)
    event_type = Column(String(100), nullable=False)
    payload = Column(Text, nullable=False)
    processed = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
