import datetime
from sqlalchemy import Column, String, DateTime, Numeric, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database.base import Base


class Receivable(Base):
    __tablename__ = "receivables"

    id = Column(String(50), primary_key=True, index=True)
    merchant_id = Column(String(50), ForeignKey("merchants.id"), nullable=False, index=True)
    customer_id = Column(String(50), ForeignKey("customers.id"), nullable=False, index=True)
    invoice_number = Column(String(100), unique=True, index=True, nullable=False)
    amount = Column(Numeric(14, 2), nullable=False)
    paid_amount = Column(Numeric(14, 2), default=0, nullable=False)
    balance_due = Column(Numeric(14, 2), nullable=False)
    issue_date = Column(DateTime, nullable=False)
    due_date = Column(DateTime, nullable=False)
    status = Column(String(30), default="Current", nullable=False, index=True)  # Current, Due Soon, Overdue, Severely Overdue
    days_overdue = Column(Integer, default=0, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

    merchant = relationship("Merchant", back_populates="receivables")
    customer = relationship("Customer", back_populates="receivables")
