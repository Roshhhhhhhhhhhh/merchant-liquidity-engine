from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.api.deps import get_current_merchant_id
from app.models.payable import Payable
from app.schemas.payable import (
    PayableResponse,
    PayablesSummary,
    PayablesListResponse,
)
from app.services.formatters import format_inr

router = APIRouter()


@router.get("", response_model=PayablesListResponse, summary="Get payables obligations")
def get_payables(
    status: Optional[str] = Query(None, description="Filter by status: Pending, Scheduled, Paid"),
    priority: Optional[str] = Query(None, description="Filter by priority: Critical, High, Medium, Low"),
    search: Optional[str] = Query(None, description="Search vendor name or invoice number"),
    merchant_id: str = Depends(get_current_merchant_id),
    db: Session = Depends(get_db),
):
    now = datetime.utcnow()
    twelve_days_ahead = now + timedelta(days=12)

    query = db.query(Payable).filter(Payable.merchant_id == merchant_id)
    all_payables = query.all()

    total_payables = Decimal("0.00")
    due_within_12_days = Decimal("0.00")
    critical_amount = Decimal("0.00")
    pending_count = 0
    scheduled_count = 0
    paid_count = 0
    items = []

    for p in all_payables:
        bal = Decimal(str(p.balance_due))
        total_payables += bal

        if p.status == "Pending":
            pending_count += 1
        elif p.status == "Scheduled":
            scheduled_count += 1
        elif p.status == "Paid":
            paid_count += 1

        if p.status in ("Pending", "Scheduled") and p.due_date <= twelve_days_ahead:
            due_within_12_days += bal

        if p.priority in ("Critical", "High") and p.status in ("Pending", "Scheduled"):
            critical_amount += bal

        # Filters
        if status and p.status.lower() != status.lower():
            continue
        if priority and p.priority.lower() != priority.lower():
            continue
        if search:
            s = search.lower()
            if s not in p.vendor_name.lower() and s not in p.invoice_number.lower():
                continue

        days_until_due = (p.due_date - now).days if p.due_date else 0

        items.append(
            PayableResponse(
                id=p.id,
                merchant_id=p.merchant_id,
                vendor_name=p.vendor_name,
                invoice_number=p.invoice_number,
                amount=Decimal(str(p.amount)),
                paid_amount=Decimal(str(p.paid_amount)),
                balance_due=bal,
                issue_date=p.issue_date,
                due_date=p.due_date,
                category=p.category,
                status=p.status,
                priority=p.priority,
                notes=p.notes,
                amount_formatted=format_inr(p.amount),
                balance_due_formatted=format_inr(bal),
                days_until_due=days_until_due,
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
        )

    items.sort(key=lambda x: x.due_date)

    summary = PayablesSummary(
        total_payables=total_payables,
        total_payables_formatted=format_inr(total_payables),
        due_within_12_days=due_within_12_days,
        due_within_12_days_formatted=format_inr(due_within_12_days),
        critical_priority_amount=critical_amount,
        critical_priority_formatted=format_inr(critical_amount),
        average_dpo_days=35,
        pending_count=pending_count,
        scheduled_count=scheduled_count,
        paid_count=paid_count,
    )

    return PayablesListResponse(summary=summary, items=items)
