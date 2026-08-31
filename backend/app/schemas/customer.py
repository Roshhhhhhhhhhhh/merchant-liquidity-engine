from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class CustomerBase(BaseModel):
    name: str
    company_name: str
    email: str
    phone: Optional[str] = None
    gstin: Optional[str] = None
    credit_limit: Decimal
    credit_terms_days: int = 30
    total_revenue: Decimal = Decimal("0.00")
    customer_tier: str = "Standard"  # Enterprise, Tier-1, Standard
    payment_score: int = 80


class CustomerResponse(CustomerBase):
    id: str
    merchant_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CustomerSummary(BaseModel):
    total_customers: int
    enterprise_count: int
    tier_1_count: int
    standard_count: int
    total_credit_granted: Decimal
    total_outstanding_exposure: Decimal
    avg_payment_score: Decimal


class CustomerListResponse(BaseModel):
    summary: CustomerSummary
    customers: List[CustomerResponse]
