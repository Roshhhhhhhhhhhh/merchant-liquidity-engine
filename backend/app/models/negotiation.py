from datetime import datetime
from sqlalchemy import Column, String, Numeric, Integer, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database.base import Base


class NegotiationSession(Base):
    """
    Represents an ongoing or completed commercial negotiation session between
    an AI Buyer Agent and the Merchant Liquidity Agent.
    """
    __tablename__ = "negotiation_sessions"

    id = Column(String(50), primary_key=True, index=True)
    merchant_id = Column(String(50), ForeignKey("merchants.id"), nullable=False, index=True)
    buyer_id = Column(String(100), nullable=False, default="buyer_enterprise_procure")
    status = Column(
        String(50),
        nullable=False,
        default="REQUESTED",
        index=True,
    )  # REQUESTED, ANALYZING, OFFERED, BUYER_COUNTERED, RE_EVALUATING, COUNTER_OFFERED, ACCEPTED, REJECTED, EXPIRED
    buyer_request_data = Column(Text, nullable=True)  # JSON serialized BuyerRequest
    current_offer_id = Column(String(50), nullable=True)
    round_number = Column(Integer, default=1, nullable=False)
    max_rounds = Column(Integer, default=5, nullable=False)
    final_agreement_data = Column(Text, nullable=True)  # JSON serialized agreement if accepted
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    merchant = relationship("Merchant", backref="negotiations")
    messages = relationship("NegotiationMessage", back_populates="session", cascade="all, delete-orphan", order_by="NegotiationMessage.created_at.asc()")
    offers = relationship("NegotiationOffer", back_populates="session", cascade="all, delete-orphan", order_by="NegotiationOffer.created_at.asc()")
    traces = relationship("AgentTrace", back_populates="session", cascade="all, delete-orphan", order_by="AgentTrace.timestamp.asc()")


class NegotiationMessage(Base):
    """
    A single structured communication event in the negotiation timeline.
    """
    __tablename__ = "negotiation_messages"

    id = Column(String(50), primary_key=True, index=True)
    session_id = Column(String(50), ForeignKey("negotiation_sessions.id"), nullable=False, index=True)
    sender = Column(String(20), nullable=False)  # buyer, merchant, system
    message_type = Column(String(50), nullable=False)  # request, analysis, offer, counter, acceptance, rejection, system_notice
    round_number = Column(Integer, default=1, nullable=False)
    raw_message = Column(Text, nullable=False)
    structured_data = Column(Text, nullable=True)  # JSON payload
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    session = relationship("NegotiationSession", back_populates="messages")


class NegotiationOffer(Base):
    """
    A formal commercial proposal generated deterministically by the Merchant Engine.
    """
    __tablename__ = "negotiation_offers"

    id = Column(String(50), primary_key=True, index=True)
    session_id = Column(String(50), ForeignKey("negotiation_sessions.id"), nullable=False, index=True)
    candidate_id = Column(String(50), nullable=True)
    round_number = Column(Integer, default=1, nullable=False)
    product_id = Column(String(50), nullable=False)
    product_name = Column(String(150), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(14, 2), nullable=False)
    gross_value = Column(Numeric(14, 2), nullable=False)
    payment_timing_days = Column(Integer, default=0, nullable=False)
    delivery_days = Column(Integer, default=5, nullable=False)
    economic_value = Column(Numeric(14, 2), nullable=False)
    economic_value_breakdown = Column(Text, nullable=True)
    current_pressure_score = Column(Integer, nullable=False)
    projected_pressure_score = Column(Integer, nullable=False)
    pressure_score_delta = Column(Integer, nullable=False)
    status = Column(String(30), default="OFFERED", nullable=False)  # OFFERED, COUNTERED, ACCEPTED, REJECTED
    strategy_tag = Column(String(50), nullable=True)
    rationale = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    session = relationship("NegotiationSession", back_populates="offers")


class AgentTrace(Base):
    """
    Observability audit trace logging every agent action, tool invocation, and decision step.
    """
    __tablename__ = "agent_traces"

    id = Column(String(50), primary_key=True, index=True)
    session_id = Column(String(50), ForeignKey("negotiation_sessions.id"), nullable=False, index=True)
    round_number = Column(Integer, default=1, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    agent = Column(String(50), nullable=False)  # AI Buyer Agent, Merchant Agent, Economic Engine, Optimizer
    action = Column(String(100), nullable=False)
    tool_called = Column(String(100), nullable=True)
    tool_input = Column(Text, nullable=True)
    tool_output_summary = Column(Text, nullable=True)
    decision = Column(Text, nullable=True)
    result = Column(String(50), nullable=True)  # SUCCESS, REJECTED, ACCEPTED, COUNTERED

    session = relationship("NegotiationSession", back_populates="traces")
