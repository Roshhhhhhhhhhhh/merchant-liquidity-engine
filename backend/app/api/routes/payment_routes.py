from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.payment import (
    PaymentConfigStatusResponse,
    PaymentOrderCreateRequest,
    PaymentOrderResponse,
    PaymentVerifyRequest,
    PaymentVerifyResponse,
    PaymentDetailsResponse,
    WebhookResponse,
)
from app.services.payment_service import PaymentService, RazorpayService

router = APIRouter(tags=["Payments & Settlement"])


@router.get("/status", response_model=PaymentConfigStatusResponse, summary="Get Razorpay Payment Integration Configuration Status")
def get_payment_status():
    """
    Returns public Razorpay configuration status (configured boolean & environment)
    without exposing any sensitive credentials or secrets.
    """
    return RazorpayService.get_status()


@router.post("/orders", response_model=PaymentOrderResponse, summary="Create Razorpay Test Mode Order from Accepted Negotiation")

def create_payment_order(
    payload: PaymentOrderCreateRequest,
    db: Session = Depends(get_db),
):
    """
    Creates a Razorpay Test Mode Order from an ACCEPTED negotiation session.
    The order amount is strictly derived from the immutable accepted commercial offer.
    """
    try:
        return PaymentService.create_payment_order(db=db, negotiation_id=payload.negotiation_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create payment order: {str(e)}")


@router.post("/verify", response_model=PaymentVerifyResponse, summary="Verify Razorpay Payment Signature & Execute Economic Settlement")
def verify_payment(
    payload: PaymentVerifyRequest,
    db: Session = Depends(get_db),
):
    """
    Cryptographically verifies the Razorpay payment signature.
    Atomically executes the transaction, decrements warehouse inventory, updates merchant cash/receivables,
    recalculates the Economic Twin, and returns Before vs After balance sheet impact.
    """
    try:
        return PaymentService.verify_payment_and_execute(db=db, payload=payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Payment execution failed: {str(e)}")


@router.get("/negotiation/{negotiation_id}", summary="Get Payment Order for a Negotiation Session")
def get_payment_by_negotiation(
    negotiation_id: str,
    db: Session = Depends(get_db),
):
    """
    Retrieves the active or completed payment order associated with a negotiation session.
    """
    from app.models.payment import PaymentOrder
    payment_order = (
        db.query(PaymentOrder)
        .filter(PaymentOrder.negotiation_id == negotiation_id)
        .order_by(PaymentOrder.created_at.desc())
        .first()
    )
    if not payment_order:
        raise HTTPException(status_code=404, detail=f"No payment order found for negotiation '{negotiation_id}'.")

    from app.services.formatters import format_inr
    return {
        "id": payment_order.id,
        "negotiation_id": payment_order.negotiation_id,
        "merchant_id": payment_order.merchant_id,
        "razorpay_order_id": payment_order.razorpay_order_id,
        "razorpay_payment_id": payment_order.razorpay_payment_id,
        "amount": payment_order.amount,
        "amount_formatted": format_inr(payment_order.amount),
        "currency": payment_order.currency,
        "status": payment_order.status,
        "receipt": payment_order.receipt,
        "created_at": payment_order.created_at,
        "paid_at": payment_order.paid_at,
        "projected_evc": payment_order.projected_evc,
        "realized_evc": payment_order.realized_evc,
    }


@router.get("/{payment_order_id}", summary="Get Payment Order Details")
def get_payment_order(
    payment_order_id: str,
    db: Session = Depends(get_db),
):
    """
    Retrieves payment order details by payment order ID.
    """
    from app.models.payment import PaymentOrder
    payment_order = db.query(PaymentOrder).filter(PaymentOrder.id == payment_order_id).first()
    if not payment_order:
        raise HTTPException(status_code=404, detail=f"Payment order '{payment_order_id}' not found.")

    from app.services.formatters import format_inr
    return {
        "id": payment_order.id,
        "negotiation_id": payment_order.negotiation_id,
        "merchant_id": payment_order.merchant_id,
        "razorpay_order_id": payment_order.razorpay_order_id,
        "razorpay_payment_id": payment_order.razorpay_payment_id,
        "amount": payment_order.amount,
        "amount_formatted": format_inr(payment_order.amount),
        "currency": payment_order.currency,
        "status": payment_order.status,
        "receipt": payment_order.receipt,
        "created_at": payment_order.created_at,
        "paid_at": payment_order.paid_at,
        "projected_evc": payment_order.projected_evc,
        "realized_evc": payment_order.realized_evc,
    }


@router.post("/razorpay", response_model=WebhookResponse, summary="Razorpay Webhook Handler with Idempotency")
@router.post("/razorpay/webhook", response_model=WebhookResponse, summary="Razorpay Webhook Handler with Idempotency (Legacy Alias)")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """
    Receives incoming Razorpay webhook events, validates cryptographic authenticity,
    and applies idempotent payment confirmation without duplicate state transitions.
    
    NOTE: A missing signature in production is an error condition. The webhook MUST include
    the X-Razorpay-Signature header. No fallback to mock signatures for unsigned requests.
    """
    body_bytes = await request.body()
    sig = x_razorpay_signature
    
    if not sig:
        raise HTTPException(status_code=401, detail="Missing X-Razorpay-Signature header. Webhook signature is required.")

    try:
        result = PaymentService.process_webhook(db=db, raw_body_bytes=body_bytes, signature=sig)
        return WebhookResponse(
            status=result["status"],
            event_id=result["event_id"],
            processed=result["processed"],
            message=result["message"],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Webhook processing error: {str(e)}")
