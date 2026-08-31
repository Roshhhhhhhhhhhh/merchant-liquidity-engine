from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class EconomicSnapshotBase(BaseModel):
    snapshot_date: datetime
    cash_balance: Decimal
    total_receivables: Decimal
    total_payables: Decimal
    inventory_value: Decimal
    aging_inventory_value: Decimal
    gross_margin_pct: Decimal
    cash_runway_days: int
    quick_ratio: Decimal
    current_ratio: Decimal
    working_capital: Decimal
    dso_days: int = 42
    dpo_days: int = 35
    dio_days: int = 58
    cash_conversion_cycle: int = 65
    liquidity_stress_score: int = 50
    event_marker: Optional[str] = None
    notes: Optional[str] = None


class EconomicSnapshotResponse(EconomicSnapshotBase):
    id: str
    merchant_id: str
    cash_balance_formatted: str
    receivables_formatted: str
    payables_formatted: str
    inventory_formatted: str
    working_capital_formatted: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SnapshotTrendPoint(BaseModel):
    date: str  # YYYY-MM-DD
    timestamp: datetime
    cash_balance: float
    total_receivables: float
    total_payables: float
    inventory_value: float
    working_capital: float
    cash_runway_days: int
    liquidity_stress_score: int
    event_marker: Optional[str] = None


class SnapshotTimelineResponse(BaseModel):
    total_points: int
    start_date: datetime
    end_date: datetime
    data: List[SnapshotTrendPoint]
    recent_snapshots: List[EconomicSnapshotResponse]
