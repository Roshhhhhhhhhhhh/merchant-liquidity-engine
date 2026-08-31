from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class MerchantBase(BaseModel):
    name: str
    trade_name: str
    gst_number: str
    industry: str
    address: Optional[str] = None
    base_currency: str = "INR"


class MerchantCreate(MerchantBase):
    id: str


class MerchantResponse(MerchantBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LiquidityPressureDriver(BaseModel):
    id: str
    title: str
    impact_amount: Optional[Decimal] = None
    impact_formatted: str
    category: str  # Receivables, Inventory, Payables, Demand
    description: str
    severity: str  # Critical, Warning, Watch, Info


class DimensionState(BaseModel):
    dimension: str
    name: str
    value: Decimal
    formatted_value: str
    status: str  # Healthy, Watch, Warning, Critical, Softening
    label: str
    trend: Optional[str] = None  # Up, Down, Stable
    trend_pct: Optional[Decimal] = None
    benchmark: Optional[str] = None


class BusinessStateResponse(BaseModel):
    merchant_id: str
    merchant_name: str
    trade_name: str
    gst_number: str
    industry: str
    as_of: datetime

    # Summary Scores
    liquidity_stress_score: int  # 0 (Low Stress) to 100 (Severe Stress)
    liquidity_status: str  # Healthy, Watch, Warning, Critical
    liquidity_outlook_headline: str
    liquidity_outlook_summary: str
    drivers: List[LiquidityPressureDriver]

    # Core 10 Economic Dimensions
    cash: DimensionState
    receivables: DimensionState
    payables: DimensionState
    inventory_value: DimensionState
    aging_inventory: DimensionState
    gross_margin: DimensionState
    demand_trend: DimensionState
    customer_value: DimensionState
    fulfillment_capacity: DimensionState
    cash_runway: DimensionState

    # Working Capital & Ratios
    working_capital: Decimal
    working_capital_formatted: str
    quick_ratio: Decimal
    current_ratio: Decimal
    dso_days: int  # Days Sales Outstanding
    dpo_days: int  # Days Payable Outstanding
    dio_days: int  # Days Inventory Outstanding
    cash_conversion_cycle: int  # DIO + DSO - DPO
