from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class BuyerRequest(BaseModel):
    """
    Structured purchase intent extracted from natural language or direct form input.
    """
    buyer_id: str = Field(default="buyer_enterprise_procure", description="Identifier of the purchasing entity")
    intent: str = Field(default="bulk_purchase", description="Buyer intent: bulk_purchase, spot_order, inventory_clearance")
    product_requirements: Optional[List[str]] = Field(default_factory=list, description="Specific SKU names or categories")
    product_id: Optional[str] = Field(default=None, description="Direct target Product ID if resolved")
    product_name: Optional[str] = Field(default=None, description="Resolved Product Name")
    quantity: int = Field(..., gt=0, description="Requested unit quantity")
    maximum_budget: Decimal = Field(..., gt=0, description="Total maximum budgetary ceiling in INR")
    maximum_delivery_days: int = Field(default=6, gt=0, description="Maximum acceptable delivery lead time in days")
    preferred_payment_days: int = Field(default=0, ge=0, description="Preferred credit terms (0=Immediate, 7, 15, 30, 45)")
    preferred_products: Optional[List[str]] = Field(default_factory=list)
    constraints: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional buyer policies or constraints")
    raw_inquiry_text: Optional[str] = Field(default=None, description="Original natural language message")


class BuyerConstraintModel(BaseModel):
    """
    Internal rules governing the AI Buyer Agent's negotiation stance.
    """
    budget_ceiling: Decimal
    min_quantity: int
    max_delivery_days: int
    preferred_payment_days: int = 0
    negotiation_tolerance_pct: Decimal = Decimal("5.0")  # Max % buyer will stretch budget for optimal value


class NegotiationOfferModel(BaseModel):
    id: str
    session_id: str
    candidate_id: Optional[str] = None
    round_number: int
    product_id: str
    product_name: str
    quantity: int
    unit_price: Decimal
    gross_value: Decimal
    gross_value_formatted: str
    payment_timing_days: int
    delivery_days: int
    economic_value: Decimal
    economic_value_formatted: str
    current_pressure_score: int
    projected_pressure_score: int
    pressure_score_delta: int
    status: str  # OFFERED, COUNTERED, ACCEPTED, REJECTED
    strategy_tag: Optional[str] = None
    rationale: Optional[str] = None
    created_at: datetime


class NegotiationMessageModel(BaseModel):
    id: str
    session_id: str
    sender: str  # buyer, merchant, system
    message_type: str  # request, analysis, offer, counter, acceptance, rejection, system_notice
    round_number: int
    raw_message: str
    structured_data: Optional[Dict[str, Any]] = None
    created_at: datetime


class AgentTraceModel(BaseModel):
    id: str
    session_id: str
    round_number: int
    timestamp: datetime
    agent: str  # AI Buyer Agent, Merchant Agent, Economic Engine, Optimizer
    action: str
    tool_called: Optional[str] = None
    tool_input: Optional[Dict[str, Any]] = None
    tool_output_summary: Optional[str] = None
    decision: Optional[str] = None
    result: Optional[str] = None


class NegotiationSessionResponse(BaseModel):
    id: str
    merchant_id: str
    buyer_id: str
    status: str
    round_number: int
    max_rounds: int
    buyer_request: BuyerRequest
    current_offer: Optional[NegotiationOfferModel] = None
    messages: List[NegotiationMessageModel] = []
    offers: List[NegotiationOfferModel] = []
    traces: List[AgentTraceModel] = []
    agent_mode: str = "fallback"  # live_llm, fallback
    final_agreement: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class NegotiationListItem(BaseModel):
    id: str
    merchant_id: str
    buyer_id: str
    status: str
    round_number: int
    requested_quantity: int
    maximum_budget: Decimal
    maximum_budget_formatted: str
    current_offer_amount: Optional[Decimal] = None
    current_offer_amount_formatted: Optional[str] = None
    economic_value: Optional[Decimal] = None
    economic_value_formatted: Optional[str] = None
    created_at: datetime


class NegotiationListResponse(BaseModel):
    total_sessions: int
    sessions: List[NegotiationListItem]


class ParseBuyerRequestInput(BaseModel):
    message: str = Field(..., min_length=3, description="Natural language purchase request")
    buyer_id: Optional[str] = Field(default="buyer_enterprise_procure")


class StartNegotiationRequest(BaseModel):
    merchant_id: Optional[str] = None
    buyer_request: BuyerRequest


class BuyerCounterRequest(BaseModel):
    counter_message: Optional[str] = None
    target_budget: Optional[Decimal] = None
    requested_quantity: Optional[int] = None
    preferred_payment_days: Optional[int] = None
    max_delivery_days: Optional[int] = None


class DemoNegotiationRequest(BaseModel):
    merchant_id: Optional[str] = None
    scenario_preset: Optional[str] = Field(default="standard_valve_inquiry")
