from datetime import datetime
from sqlalchemy import Column, String, Numeric, Integer, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database.base import Base


class Scenario(Base):
    __tablename__ = "scenarios"

    id = Column(String(50), primary_key=True, index=True)
    merchant_id = Column(String(50), ForeignKey("merchants.id"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="Simulated")  # Simulated, Accepted, Archived
    request_data = Column(Text, nullable=False)  # JSON string of BuyerRequestModel
    recommended_candidate_id = Column(String(50), nullable=True)
    explanation = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    merchant = relationship("Merchant")
    candidates = relationship("ScenarioCandidate", back_populates="scenario", cascade="all, delete-orphan", order_by="ScenarioCandidate.rank")


class ScenarioCandidate(Base):
    __tablename__ = "scenario_candidates"

    id = Column(String(50), primary_key=True, index=True)
    scenario_id = Column(String(50), ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False, index=True)
    label = Column(String(100), nullable=False)  # Deal A, Deal B, Deal C, Deal D
    is_recommended = Column(Boolean, default=False, nullable=False)
    rank = Column(Integer, default=1, nullable=False)
    action_type = Column(String(50), nullable=False)  # sale, price_change, bundle, liquidation
    action_data = Column(Text, nullable=False)  # JSON payload
    
    # Financial Measures
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(14, 2), nullable=False)
    gross_value = Column(Numeric(14, 2), nullable=False)
    estimated_cogs = Column(Numeric(14, 2), nullable=False)
    contribution_margin = Column(Numeric(14, 2), nullable=False)
    margin_pct = Column(Numeric(6, 2), nullable=False)
    payment_timing_days = Column(Integer, default=0, nullable=False)
    delivery_days = Column(Integer, default=5, nullable=False)
    
    # Impact Measures
    cash_impact = Column(Numeric(14, 2), nullable=False)
    inventory_impact = Column(Numeric(14, 2), nullable=False)
    aging_inventory_impact = Column(Numeric(14, 2), default=0, nullable=False)
    receivable_impact = Column(Numeric(14, 2), default=0, nullable=False)
    capacity_impact_pct = Column(Numeric(6, 2), default=0, nullable=False)
    days_inventory_coverage = Column(Numeric(6, 1), default=30.0, nullable=False)
    stockout_risk = Column(String(50), default="Low", nullable=False)

    # Economic Value & Pressure
    economic_value = Column(Numeric(14, 2), nullable=False)
    economic_value_breakdown = Column(Text, nullable=False)  # JSON string
    current_pressure_score = Column(Integer, nullable=False)
    projected_pressure_score = Column(Integer, nullable=False)
    pressure_score_delta = Column(Integer, nullable=False)
    projected_state = Column(String(50), nullable=False)  # Strong, Healthy, Watch, Stressed, Critical
    projected_state_data = Column(Text, nullable=False)  # JSON string
    explanation = Column(Text, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    scenario = relationship("Scenario", back_populates="candidates")
