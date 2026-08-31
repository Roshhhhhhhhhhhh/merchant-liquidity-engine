from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class TransactionBase(BaseModel):
    customer_id: str
    product_id: str
    reference_id: str
    quantity: int
    unit_price: Decimal
    gross_value: Decimal
    cost_value: Decimal
    net_margin_pct: Decimal
    payment_status: str = "Captured"  # Captured, Pending, Refunded, Failed
    settlement_status: str = "Settled"  # Settled, In Transit, Pending
    payment_method: str = "NEFT/RTGS"
    channel: str = "Direct B2B"
    source: Optional[str] = "direct"
    negotiation_id: Optional[str] = None
    payment_order_id: Optional[str] = None
    razorpay_payment_id: Optional[str] = None
    razorpay_order_id: Optional[str] = None
    paid_at: Optional[datetime] = None


class TransactionResponse(TransactionBase):
    id: str
    merchant_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TransactionWithDetails(TransactionBase):
    id: str
    merchant_id: str
    customer_name: str
    customer_company: str
    product_name: str
    product_sku: str
    product_category: str
    gross_value_formatted: str
    unit_price_formatted: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TransactionSummary(BaseModel):
    total_transactions: int
    total_gross_volume: Decimal
    total_gross_volume_formatted: str
    settled_volume: Decimal
    settled_volume_formatted: str
    in_transit_volume: Decimal
    in_transit_volume_formatted: str
    pending_volume: Decimal
    pending_volume_formatted: str
    avg_order_value: Decimal
    avg_order_value_formatted: str
    avg_gross_margin_pct: Decimal


class TransactionListResponse(BaseModel):
    summary: TransactionSummary
    items: List[TransactionWithDetails]
