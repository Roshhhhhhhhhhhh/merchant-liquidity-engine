from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from app.database.session import get_db
from app.api.deps import get_current_merchant_id
from app.models.transaction import Transaction
from app.schemas.transaction import (
    TransactionListResponse,
    TransactionWithDetails,
    TransactionSummary,
)
from app.services.formatters import format_inr

router = APIRouter()


@router.get("", response_model=TransactionListResponse, summary="Get transactions log")
def get_transactions(
    payment_status: Optional[str] = Query(None, description="Filter by payment status"),
    settlement_status: Optional[str] = Query(None, description="Filter by settlement status"),
    search: Optional[str] = Query(None, description="Search transaction ref, customer, or product"),
    merchant_id: str = Depends(get_current_merchant_id),
    db: Session = Depends(get_db),
):
    query = (
        db.query(Transaction)
        .filter(Transaction.merchant_id == merchant_id)
        .options(joinedload(Transaction.customer), joinedload(Transaction.product))
        .order_by(Transaction.created_at.desc())
    )

    all_txs = query.all()

    total_gross = Decimal("0.00")
    settled_val = Decimal("0.00")
    in_transit_val = Decimal("0.00")
    pending_val = Decimal("0.00")
    margin_sum = Decimal("0.00")
    items = []

    for t in all_txs:
        gross = Decimal(str(t.gross_value))
        total_gross += gross
        margin_sum += Decimal(str(t.net_margin_pct))

        if t.settlement_status == "Settled":
            settled_val += gross
        elif t.settlement_status == "In Transit":
            in_transit_val += gross
        elif t.settlement_status == "Pending":
            pending_val += gross

        # Filter
        if payment_status and t.payment_status.lower() != payment_status.lower():
            continue
        if settlement_status and t.settlement_status.lower() != settlement_status.lower():
            continue
        if search:
            s = search.lower()
            if (
                s not in t.reference_id.lower()
                and s not in t.customer.company_name.lower()
                and s not in t.customer.name.lower()
                and s not in t.product.name.lower()
                and s not in t.product.sku.lower()
            ):
                continue

        items.append(
            TransactionWithDetails(
                id=t.id,
                merchant_id=t.merchant_id,
                customer_id=t.customer_id,
                product_id=t.product_id,
                reference_id=t.reference_id,
                quantity=t.quantity,
                unit_price=Decimal(str(t.unit_price)),
                gross_value=gross,
                cost_value=Decimal(str(t.cost_value)),
                net_margin_pct=Decimal(str(t.net_margin_pct)),
                payment_status=t.payment_status,
                settlement_status=t.settlement_status,
                payment_method=t.payment_method,
                channel=t.channel,
                customer_name=t.customer.name,
                customer_company=t.customer.company_name,
                product_name=t.product.name,
                product_sku=t.product.sku,
                product_category=t.product.category,
                gross_value_formatted=format_inr(gross),
                unit_price_formatted=format_inr(t.unit_price),
                created_at=t.created_at,
                source=t.source or "direct",
                negotiation_id=t.negotiation_id,
                payment_order_id=t.payment_order_id,
                razorpay_payment_id=t.razorpay_payment_id,
                razorpay_order_id=t.razorpay_order_id,
                paid_at=t.paid_at,
            )
        )

    count = len(all_txs)
    avg_order = (total_gross / Decimal(count)) if count > 0 else Decimal("0.00")
    avg_margin = (margin_sum / Decimal(count)) if count > 0 else Decimal("0.00")

    summary = TransactionSummary(
        total_transactions=count,
        total_gross_volume=total_gross,
        total_gross_volume_formatted=format_inr(total_gross),
        settled_volume=settled_val,
        settled_volume_formatted=format_inr(settled_val),
        in_transit_volume=in_transit_val,
        in_transit_volume_formatted=format_inr(in_transit_val),
        pending_volume=pending_val,
        pending_volume_formatted=format_inr(pending_val),
        avg_order_value=avg_order,
        avg_order_value_formatted=format_inr(avg_order),
        avg_gross_margin_pct=round(avg_margin, 1),
    )

    return TransactionListResponse(summary=summary, items=items)
