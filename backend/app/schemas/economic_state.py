from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class DimensionStateModel(BaseModel):
    dimension: str
    name: str
    value: Decimal
    formatted_value: str
    status: str  # Healthy, Watch, Warning, Critical
    label: str
    trend: Optional[str] = "Stable"  # Up, Down, Stable
    trend_pct: Optional[Decimal] = Decimal("0.0")
    benchmark: Optional[str] = None


class PressureDriverModel(BaseModel):
    id: str
    title: str
    impact_amount: Optional[Decimal] = None
    impact_formatted: str
    category: str  # Receivables, Inventory, Payables, Demand, Margin, Liquidity
    description: str
    severity: str  # Critical, Warning, Watch, Info
    contribution_score: Decimal  # Weighted contribution to total pressure
    rank: int  # 1 = top contributor


class StateScoreModel(BaseModel):
    pressure_score: int = Field(..., ge=0, le=100)
    state: str  # Strong, Healthy, Watch, Stressed, Critical
    state_description: str
    component_scores: Dict[str, Decimal]
    component_weights: Dict[str, Decimal]


class MetricDelta(BaseModel):
    metric: str
    label: str
    before: Decimal
    after: Decimal
    absolute_change: Decimal
    percentage_change: Decimal
    direction: str  # Positive, Negative, Neutral
    unit: str = "INR"
    formatted_before: str
    formatted_after: str
    formatted_change: str


class EconomicStateModel(BaseModel):
    merchant_id: str
    merchant_name: str
    trade_name: str
    gst_number: str
    industry: str
    as_of: datetime

    # Core 10 Dimensions & Primary Financial State
    cash: DimensionStateModel
    receivables: DimensionStateModel
    payables: DimensionStateModel
    inventory_value: DimensionStateModel
    aging_inventory: DimensionStateModel
    gross_margin: DimensionStateModel
    demand_trend: DimensionStateModel
    customer_value: DimensionStateModel
    fulfillment_capacity: DimensionStateModel
    cash_runway: DimensionStateModel

    # Direct Monetary & Numeric Fields (For API consumption)
    cash_position: Decimal
    total_receivables: Decimal
    overdue_receivables: Decimal
    total_payables: Decimal
    near_term_payables: Decimal
    inventory_valuation: Decimal
    aging_inventory_value: Decimal
    available_inventory_units: int
    gross_margin_pct: Decimal
    recent_revenue: Decimal
    recent_demand_trend_pct: Decimal
    payment_velocity: Decimal  # 0.0 to 1.0
    customer_portfolio_value: Decimal
    fulfillment_capacity_pct: Decimal
    cash_runway_days: int
    cash_runway_display: str

    # Pressure & Classification
    pressure_score: int
    liquidity_stress_score: int  # Compatibility alias
    state: str  # Strong, Healthy, Watch, Stressed, Critical
    liquidity_status: str  # Healthy, Watch, Warning, Critical
    liquidity_outlook_headline: str
    liquidity_outlook_summary: str
    top_drivers: List[PressureDriverModel]
    drivers: List[PressureDriverModel]  # Compatibility alias

    # Working Capital & Key Financial Ratios
    working_capital: Decimal
    working_capital_formatted: str
    quick_ratio: Decimal
    current_ratio: Decimal
    dso_days: int
    dpo_days: int
    dio_days: int
    cash_conversion_cycle: int


class StateDriversResponse(BaseModel):
    merchant_id: str
    as_of: datetime
    pressure_score: int
    state: str
    drivers: List[PressureDriverModel]
    total_drivers_count: int


class StateHistoryPoint(BaseModel):
    date: str
    timestamp: datetime
    cash: Decimal
    receivables: Decimal
    overdue_receivables: Decimal
    payables: Decimal
    inventory: Decimal
    aging_inventory: Decimal
    gross_margin_pct: Decimal
    runway_days: int
    pressure_score: int
    state: str
    demand_trend_pct: Decimal
    working_capital: Decimal
    event_marker: Optional[str] = None


class StateHistoryResponse(BaseModel):
    merchant_id: str
    total_points: int
    start_date: str
    end_date: str
    history: List[StateHistoryPoint]


class StateDeltaResponse(BaseModel):
    merchant_id: str
    baseline_date: datetime
    current_date: datetime
    baseline_state: str
    current_state: str
    baseline_pressure_score: int
    current_pressure_score: int
    deltas: List[MetricDelta]
    summary: str


class EconomicValueModel(BaseModel):
    contribution_margin_value: Decimal
    liquidity_improvement_value: Decimal
    inventory_relief_value: Decimal
    receivable_improvement_value: Decimal
    economic_risk_cost: Decimal
    total_economic_value_created: Decimal
    assumptions: Dict[str, Any]


class EconomicActionModel(BaseModel):
    action_type: str  # change_price, accelerate_payment, liquidate_inventory, offer_discount, bundle_inventory
    target_id: Optional[str] = None  # product_id or invoice_id
    parameters: Dict[str, Any] = Field(default_factory=dict)
    description: str


class ActionEvaluationRequest(BaseModel):
    merchant_id: Optional[str] = None
    action: EconomicActionModel


class ActionEvaluationResponse(BaseModel):
    action: EconomicActionModel
    is_favorable: bool
    current_pressure_score: int
    projected_pressure_score: int
    pressure_score_delta: int
    current_state: str
    projected_state: str
    economic_value_created: EconomicValueModel
    deltas: List[MetricDelta]
    recommendation_summary: str
