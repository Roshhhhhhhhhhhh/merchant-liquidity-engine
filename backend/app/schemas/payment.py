from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class PaymentConfigStatusResponse(BaseModel):
    configured: bool
    environment: str = "sandbox"


class PaymentOrderCreateRequest(BaseModel):
    negotiation_id: str = Field(..., description="ID of the accepted negotiation session")



class PaymentOrderResponse(BaseModel):
    id: str
    negotiation_id: str
    merchant_id: str
    razorpay_order_id: str
    amount: Decimal
    amount_formatted: str
    amount_paise: int
    currency: str = "INR"
    status: str
    receipt: str
    razorpay_key_id: str
    merchant_name: str
    product_name: str
    quantity: int
    unit_price: Decimal
    created_at: datetime


class PaymentVerifyRequest(BaseModel):
    payment_order_id: str = Field(..., description="Internal payment order ID (pay_ord_...)")
    razorpay_order_id: str = Field(..., description="Razorpay order ID (order_...)")
    razorpay_payment_id: str = Field(..., description="Razorpay payment ID (pay_...)")
    razorpay_signature: str = Field(..., description="Cryptographic HMAC-SHA256 signature from Razorpay Checkout")


class EconomicMetricComparison(BaseModel):
    metric: str
    before_value: float
    after_value: float
    delta: float
    before_formatted: str
    after_formatted: str
    delta_formatted: str
    direction: str  # favorable, unfavorable, neutral


class PaymentVerifyResponse(BaseModel):
    success: bool
    payment_order_id: str
    transaction_id: str
    reference_id: str
    razorpay_payment_id: str
    amount: Decimal
    amount_formatted: str
    status: str
    settlement_status: str
    paid_at: datetime
    inventory_updated: Dict[str, Any]
    metrics_comparison: List[EconomicMetricComparison]
    projected_evc: Decimal
    projected_evc_formatted: str
    realized_evc: Decimal
    realized_evc_formatted: str
    evc_variance: Decimal
    evc_variance_formatted: str
    message: str


class PaymentDetailsResponse(BaseModel):
    id: str
    negotiation_id: str
    merchant_id: str
    razorpay_order_id: str
    razorpay_payment_id: Optional[str] = None
    amount: Decimal
    amount_formatted: str
    currency: str
    status: str
    receipt: str
    created_at: datetime
    paid_at: Optional[datetime] = None
    transaction_id: Optional[str] = None
    projected_evc: Optional[Decimal] = None
    realized_evc: Optional[Decimal] = None
    metrics_comparison: Optional[List[EconomicMetricComparison]] = None


class WebhookResponse(BaseModel):
    status: str
    event_id: str
    processed: bool
    message: str
