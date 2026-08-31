import datetime
from sqlalchemy import Column, String, DateTime, Numeric, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database.base import Base


class EconomicSnapshot(Base):
    __tablename__ = "economic_snapshots"

    id = Column(String(50), primary_key=True, index=True)
    merchant_id = Column(String(50), ForeignKey("merchants.id"), nullable=False, index=True)
    snapshot_date = Column(DateTime, nullable=False, index=True)
    cash_balance = Column(Numeric(14, 2), nullable=False)
    total_receivables = Column(Numeric(14, 2), nullable=False)
    total_payables = Column(Numeric(14, 2), nullable=False)
    inventory_value = Column(Numeric(14, 2), nullable=False)
    aging_inventory_value = Column(Numeric(14, 2), nullable=False)
    gross_margin_pct = Column(Numeric(6, 2), nullable=False)
    cash_runway_days = Column(Integer, nullable=False)
    quick_ratio = Column(Numeric(6, 2), nullable=False)
    current_ratio = Column(Numeric(6, 2), nullable=False)
    working_capital = Column(Numeric(14, 2), nullable=False)
    dso_days = Column(Integer, default=42, nullable=False)  # Days Sales Outstanding
    dpo_days = Column(Integer, default=35, nullable=False)  # Days Payable Outstanding
    dio_days = Column(Integer, default=58, nullable=False)  # Days Inventory Outstanding
    cash_conversion_cycle = Column(Integer, default=65, nullable=False)  # DIO + DSO - DPO
    liquidity_stress_score = Column(Integer, default=50, nullable=False)  # 0 (Relaxed) to 100 (Severe Stress)
    event_marker = Column(String(200), nullable=True)  # e.g. "Bulk Vendor Settlement", "Delayed L&T Collection"
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    merchant = relationship("Merchant", back_populates="snapshots")
