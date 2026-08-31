from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class PayableBase(BaseModel):
    vendor_name: str
    invoice_number: str
    amount: Decimal
    paid_amount: Decimal = Decimal("0.00")
    balance_due: Decimal
    issue_date: datetime
    due_date: datetime
    category: str = "Raw Materials"
    status: str = "Pending"  # Pending, Scheduled, Paid
    priority: str = "Medium"  # Critical, High, Medium, Low
    notes: Optional[str] = None


class PayableResponse(PayableBase):
    id: str
    merchant_id: str
    amount_formatted: str
    balance_due_formatted: str
    days_until_due: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PayablesSummary(BaseModel):
    total_payables: Decimal
    total_payables_formatted: str
    due_within_12_days: Decimal
    due_within_12_days_formatted: str
    critical_priority_amount: Decimal
    critical_priority_formatted: str
    average_dpo_days: int
    pending_count: int
    scheduled_count: int
    paid_count: int


class PayablesListResponse(BaseModel):
    summary: PayablesSummary
    items: List[PayableResponse]
