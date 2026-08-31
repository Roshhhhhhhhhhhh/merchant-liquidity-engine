import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database.base import Base


class ActivityEvent(Base):
    __tablename__ = "activity_events"

    id = Column(String(50), primary_key=True, index=True)
    merchant_id = Column(String(50), ForeignKey("merchants.id"), nullable=False, index=True)
    event_type = Column(String(100), nullable=False)
    category = Column(String(50), default="General", nullable=False, index=True)  # Liquidity, Inventory, Receivables, Payables, Transactions
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String(30), default="Info", nullable=False)  # Info, Low, Medium, High, Critical
    metadata_json = Column(Text, nullable=True)  # Serialized JSON for contextual metrics
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False, index=True)

    merchant = relationship("Merchant", back_populates="activities")
