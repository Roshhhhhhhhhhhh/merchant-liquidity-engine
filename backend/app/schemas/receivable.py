from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class ReceivableBase(BaseModel):
    customer_id: str
    invoice_number: str
    amount: Decimal
    paid_amount: Decimal = Decimal("0.00")
    balance_due: Decimal
    issue_date: datetime
    due_date: datetime
    status: str = "Current"  # Current, Due Soon, Overdue, Severely Overdue
    days_overdue: int = 0
    notes: Optional[str] = None


class ReceivableResponse(ReceivableBase):
    id: str
    merchant_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReceivableWithCustomer(ReceivableBase):
    id: str
    merchant_id: str
    customer_name: str
    customer_company: str
    customer_tier: str
    amount_formatted: str
    balance_due_formatted: str
    days_outstanding: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AgingBucket(BaseModel):
    bucket: str
    min_days: int
    max_days: Optional[int] = None
    count: int
    amount: Decimal
    amount_formatted: str
    percentage: Decimal
    status: str  # Healthy, Watch, Warning, Critical


class ReceivablesSummary(BaseModel):
    total_outstanding: Decimal
    total_outstanding_formatted: str
    due_this_week: Decimal
    due_this_week_formatted: str
    total_overdue: Decimal
    total_overdue_formatted: str
    severely_overdue: Decimal
    severely_overdue_formatted: str
    average_dso_days: int
    current_count: int
    due_soon_count: int
    overdue_count: int
    severely_overdue_count: int
    aging_buckets: List[AgingBucket]


class ReceivablesListResponse(BaseModel):
    summary: ReceivablesSummary
    items: List[ReceivableWithCustomer]
