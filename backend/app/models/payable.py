import datetime
from sqlalchemy import Column, String, DateTime, Numeric, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database.base import Base


class Payable(Base):
    __tablename__ = "payables"

    id = Column(String(50), primary_key=True, index=True)
    merchant_id = Column(String(50), ForeignKey("merchants.id"), nullable=False, index=True)
    vendor_name = Column(String(200), nullable=False)
    invoice_number = Column(String(100), unique=True, index=True, nullable=False)
    amount = Column(Numeric(14, 2), nullable=False)
    paid_amount = Column(Numeric(14, 2), default=0, nullable=False)
    balance_due = Column(Numeric(14, 2), nullable=False)
    issue_date = Column(DateTime, nullable=False)
    due_date = Column(DateTime, nullable=False)
    category = Column(String(100), default="Raw Materials", nullable=False)
    status = Column(String(30), default="Pending", nullable=False)  # Pending, Scheduled, Paid
    priority = Column(String(30), default="Medium", nullable=False)  # Critical, High, Medium, Low
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

    merchant = relationship("Merchant", back_populates="payables")
