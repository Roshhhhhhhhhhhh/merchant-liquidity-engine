from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.schemas.economic_state import EconomicStateModel, MetricDelta


class BuyerRequestModel(BaseModel):
    product_id: Optional[str] = Field(None, description="Requested Product ID")
    product_name: Optional[str] = Field(None, description="Requested Product Name")
    requested_quantity: int = Field(..., gt=0, description="Requested unit quantity")
    target_budget: Decimal = Field(..., ge=0, description="Target buyer total budget (INR)")
    max_delivery_days: int = Field(7, ge=1, le=90, description="Maximum acceptable delivery lead time in days")
    preferred_payment_timing_days: int = Field(0, ge=0, le=90, description="Preferred payment term in days (0=Immediate)")
    notes: Optional[str] = Field(None, description="Procurement specifications or notes")


class MerchantConstraintsModel(BaseModel):
    min_margin_pct: Decimal = Field(Decimal("15.0"), ge=0, le=100, description="Minimum acceptable gross margin percentage floor")
    max_discount_pct: Decimal = Field(Decimal("20.0"), ge=0, le=60, description="Maximum discretionary discount off catalog price")
    max_quantity_per_order: Optional[int] = Field(1000, description="Maximum fulfillment lot size per order")
    min_payment_speed_days: int = Field(0, description="Minimum payment velocity (0=Immediate allowed)")
    min_remaining_inventory_buffer: int = Field(10, description="Minimum buffer units to retain in stock")
    max_capacity_utilization_pct: Decimal = Field(Decimal("95.0"), description="Maximum allowable warehouse capacity threshold")


class EconomicValueBreakdownModel(BaseModel):
    contribution_margin_value: Decimal = Field(..., description="Calculated contribution margin (Revenue - COGS)")
    liquidity_improvement_value: Decimal = Field(..., description="Liquid cash enhancement value (weighted by urgency)")
    inventory_relief_value: Decimal = Field(..., description="Working capital unlocked from slow-moving/aging inventory")
    receivable_improvement_value: Decimal = Field(..., description="Receivables acceleration / DSO reduction benefit")
    economic_risk_cost: Decimal = Field(..., description="Default, collection lag, and carry risk penalty")
    capacity_cost: Decimal = Field(..., description="Production & warehouse bottleneck overload friction penalty")
    stockout_opportunity_cost: Decimal = Field(..., description="Future stockout risk / lost baseline sales penalty")
    total_economic_value_created: Decimal = Field(..., description="Net composite Economic Value Created (EVC)")
    weights_used: Dict[str, float] = Field(default_factory=dict, description="Model parameter weights applied")


class DealCandidateModel(BaseModel):
    id: str = Field(..., description="Candidate Identifier")
    label: str = Field(..., description="Deal Title e.g. Deal A, Deal B")
    strategy_tag: str = Field("Standard", description="Strategy Classification")
    is_recommended: bool = Field(False, description="Flag if candidate ranks #1 in Economic Value")
    rank: int = Field(1, description="Rank ordered by Economic Value Created")
    action_type: str = Field("sale", description="Underlying economic action")
    
    # Financial Terms
    quantity: int = Field(..., gt=0)
    unit_price: Decimal = Field(..., ge=0)
    gross_value: Decimal = Field(..., ge=0)
    estimated_cogs: Decimal = Field(..., ge=0)
    contribution_margin: Decimal = Field(...)
    margin_pct: Decimal = Field(...)
    discount_pct: Decimal = Field(Decimal("0.0"), ge=0)
    payment_timing_days: int = Field(0, ge=0)
    delivery_days: int = Field(5, ge=1)
    
    # Financial Impacts
    cash_impact: Decimal = Field(..., description="Immediate liquid cash delta")
    inventory_impact: Decimal = Field(..., description="Total inventory value reduction")
    aging_inventory_impact: Decimal = Field(Decimal("0.0"), description="Aging inventory value unlocked")
    receivable_impact: Decimal = Field(Decimal("0.0"), description="New outstanding receivables created")
    capacity_impact_pct: Decimal = Field(Decimal("0.0"), description="Incremental capacity utilization %")
    
    # Inventory Coverage
    days_inventory_coverage: Decimal = Field(Decimal("30.0"), description="Projected days of stock coverage remaining")
    stockout_risk: str = Field("Low", description="Stockout risk category: Low, Moderate, Constrained, Critical")

    # Economic Value & State Projection
    economic_value: Decimal = Field(..., description="Total Net Economic Value Created (INR)")
    economic_value_breakdown: EconomicValueBreakdownModel
    current_pressure_score: int = Field(..., ge=0, le=100)
    projected_pressure_score: int = Field(..., ge=0, le=100)
    pressure_score_delta: int = Field(..., description="Projected change in pressure (negative is favorable)")
    current_state: str = Field(..., description="Baseline merchant state tier")
    projected_state: str = Field(..., description="Projected merchant state tier")
    
    # Human-Readable Formatting & Explanations
    gross_value_formatted: str
    contribution_margin_formatted: str
    cash_impact_formatted: str
    inventory_impact_formatted: str
    aging_inventory_impact_formatted: str
    receivable_impact_formatted: str
    economic_value_formatted: str
    explanation: str = Field(..., description="Deterministic decision rationale for this candidate")
    deltas: List[MetricDelta] = Field(default_factory=list, description="State dimension deltas")


class ScenarioSimulateRequest(BaseModel):
    merchant_id: Optional[str] = Field(None, description="Merchant identifier")
    scenario_name: Optional[str] = Field(None, description="Optional custom name for scenario")
    request: BuyerRequestModel = Field(..., description="Prospective buyer inquiry specifications")
    constraints: Optional[MerchantConstraintsModel] = Field(default_factory=MerchantConstraintsModel, description="Merchant policy boundaries")


class ScenarioSimulateResponse(BaseModel):
    scenario_id: str
    merchant_id: str
    scenario_name: str
    request: BuyerRequestModel
    current_state: EconomicStateModel
    candidates: List[DealCandidateModel]
    recommended_candidate: DealCandidateModel
    ranking_explanation: str
    created_at: datetime


class ScenarioListItem(BaseModel):
    id: str
    merchant_id: str
    name: str
    status: str
    requested_quantity: int
    target_budget: Decimal
    target_budget_formatted: str
    recommended_deal_label: Optional[str] = None
    recommended_deal_strategy: Optional[str] = None
    economic_value: Decimal
    economic_value_formatted: str
    projected_pressure_score: int
    projected_state: str
    created_at: datetime


class ScenarioListResponse(BaseModel):
    total_scenarios: int
    scenarios: List[ScenarioListItem]


class GenerateDealsRequest(BaseModel):
    request: BuyerRequestModel
    constraints: Optional[MerchantConstraintsModel] = Field(default_factory=MerchantConstraintsModel)


class CompareDealsRequest(BaseModel):
    merchant_id: Optional[str] = None
    request: Optional[BuyerRequestModel] = None
    deals: List[Dict[str, Any]] = Field(..., description="Custom deals to evaluate and compare")


class CompareDealsResponse(BaseModel):
    merchant_id: str
    current_state: EconomicStateModel
    evaluated_deals: List[DealCandidateModel]
    recommended_deal: DealCandidateModel
    ranking_explanation: str
