from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from app.models.receivable import Receivable
from app.models.customer import Customer
from app.schemas.receivable import (
    ReceivablesSummary,
    ReceivableWithCustomer,
    ReceivablesListResponse,
    AgingBucket,
)
from app.services.formatters import format_inr


class ReceivablesService:
    @staticmethod
    def get_receivables(
        db: Session,
        merchant_id: str,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> ReceivablesListResponse:
        now = datetime.utcnow()
        week_ahead = now + timedelta(days=7)

        query = (
            db.query(Receivable)
            .join(Customer, Receivable.customer_id == Customer.id)
            .filter(Receivable.merchant_id == merchant_id)
            .options(joinedload(Receivable.customer))
        )

        all_receivables: List[Receivable] = query.all()

        total_outstanding = Decimal("0.00")
        due_this_week = Decimal("0.00")
        total_overdue = Decimal("0.00")
        severely_overdue = Decimal("0.00")

        current_count = 0
        due_soon_count = 0
        overdue_count = 0
        severely_overdue_count = 0

        # Aging buckets
        bucket_0_15 = {"count": 0, "amount": Decimal("0.00")}
        bucket_16_30 = {"count": 0, "amount": Decimal("0.00")}
        bucket_31_60 = {"count": 0, "amount": Decimal("0.00")}
        bucket_60_plus = {"count": 0, "amount": Decimal("0.00")}

        weighted_days_sum = Decimal("0.00")
        detailed_items: List[ReceivableWithCustomer] = []

        for item in all_receivables:
            customer = item.customer
            bal = Decimal(str(item.balance_due))
            total_outstanding += bal

            # Calculate days outstanding since issue
            days_outstanding = (now - item.issue_date).days if item.issue_date else 0
            if days_outstanding < 0:
                days_outstanding = 0
            weighted_days_sum += bal * Decimal(days_outstanding)

            # Bucket classification
            if days_outstanding <= 15:
                bucket_0_15["count"] += 1
                bucket_0_15["amount"] += bal
            elif days_outstanding <= 30:
                bucket_16_30["count"] += 1
                bucket_16_30["amount"] += bal
            elif days_outstanding <= 60:
                bucket_31_60["count"] += 1
                bucket_31_60["amount"] += bal
            else:
                bucket_60_plus["count"] += 1
                bucket_60_plus["amount"] += bal

            # Status classification
            if item.status == "Current":
                current_count += 1
            elif item.status == "Due Soon":
                due_soon_count += 1
            elif item.status == "Overdue":
                overdue_count += 1
                total_overdue += bal
            elif item.status == "Severely Overdue":
                severely_overdue_count += 1
                total_overdue += bal
                severely_overdue += bal

            if item.due_date and now <= item.due_date <= week_ahead and item.status in ("Current", "Due Soon"):
                due_this_week += bal

            # Filters
            if status and item.status.lower() != status.lower():
                continue
            if search:
                s = search.lower()
                if (
                    s not in customer.name.lower()
                    and s not in customer.company_name.lower()
                    and s not in item.invoice_number.lower()
                ):
                    continue

            detailed_items.append(
                ReceivableWithCustomer(
                    id=item.id,
                    merchant_id=item.merchant_id,
                    customer_id=customer.id,
                    customer_name=customer.name,
                    customer_company=customer.company_name,
                    customer_tier=customer.customer_tier,
                    invoice_number=item.invoice_number,
                    amount=Decimal(str(item.amount)),
                    paid_amount=Decimal(str(item.paid_amount)),
                    balance_due=bal,
                    amount_formatted=format_inr(item.amount),
                    balance_due_formatted=format_inr(bal),
                    issue_date=item.issue_date,
                    due_date=item.due_date,
                    days_outstanding=days_outstanding,
                    days_overdue=item.days_overdue,
                    status=item.status,
                    notes=item.notes,
                    created_at=item.created_at,
                    updated_at=item.updated_at,
                )
            )

        avg_dso = (
            int(weighted_days_sum / total_outstanding)
            if total_outstanding > 0
            else 42
        )

        def pct(amt: Decimal) -> Decimal:
            return round((amt / total_outstanding * Decimal(100)), 1) if total_outstanding > 0 else Decimal("0.0")

        aging_buckets = [
            AgingBucket(
                bucket="0-15 Days",
                min_days=0,
                max_days=15,
                count=bucket_0_15["count"],
                amount=bucket_0_15["amount"],
                amount_formatted=format_inr(bucket_0_15["amount"]),
                percentage=pct(bucket_0_15["amount"]),
                status="Healthy",
            ),
            AgingBucket(
                bucket="16-30 Days",
                min_days=16,
                max_days=30,
                count=bucket_16_30["count"],
                amount=bucket_16_30["amount"],
                amount_formatted=format_inr(bucket_16_30["amount"]),
                percentage=pct(bucket_16_30["amount"]),
                status="Watch",
            ),
            AgingBucket(
                bucket="31-60 Days",
                min_days=31,
                max_days=60,
                count=bucket_31_60["count"],
                amount=bucket_31_60["amount"],
                amount_formatted=format_inr(bucket_31_60["amount"]),
                percentage=pct(bucket_31_60["amount"]),
                status="Warning",
            ),
            AgingBucket(
                bucket="60+ Days",
                min_days=61,
                max_days=None,
                count=bucket_60_plus["count"],
                amount=bucket_60_plus["amount"],
                amount_formatted=format_inr(bucket_60_plus["amount"]),
                percentage=pct(bucket_60_plus["amount"]),
                status="Critical",
            ),
        ]

        summary = ReceivablesSummary(
            total_outstanding=total_outstanding,
            total_outstanding_formatted=format_inr(total_outstanding),
            due_this_week=due_this_week,
            due_this_week_formatted=format_inr(due_this_week),
            total_overdue=total_overdue,
            total_overdue_formatted=format_inr(total_overdue),
            severely_overdue=severely_overdue,
            severely_overdue_formatted=format_inr(severely_overdue),
            average_dso_days=avg_dso,
            current_count=current_count,
            due_soon_count=due_soon_count,
            overdue_count=overdue_count,
            severely_overdue_count=severely_overdue_count,
            aging_buckets=aging_buckets,
        )

        return ReceivablesListResponse(summary=summary, items=detailed_items)
