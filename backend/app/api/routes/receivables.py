from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.api.deps import get_current_merchant_id
from app.models.customer import Customer
from app.schemas.receivable import ReceivablesListResponse
from app.schemas.customer import CustomerListResponse, CustomerResponse, CustomerSummary
from app.services.receivables_service import ReceivablesService
from decimal import Decimal

router = APIRouter()


@router.get("", response_model=ReceivablesListResponse, summary="Get receivables with aging summary")
def get_receivables(
    status: Optional[str] = Query(None, description="Filter by status: Current, Due Soon, Overdue, Severely Overdue"),
    search: Optional[str] = Query(None, description="Search customer name or invoice number"),
    merchant_id: str = Depends(get_current_merchant_id),
    db: Session = Depends(get_db),
):
    return ReceivablesService.get_receivables(
        db=db,
        merchant_id=merchant_id,
        status=status,
        search=search,
    )


@router.get("/customers", response_model=CustomerListResponse, summary="Get customer directory")
def get_customers(
    merchant_id: str = Depends(get_current_merchant_id),
    db: Session = Depends(get_db),
):
    customers = db.query(Customer).filter(Customer.merchant_id == merchant_id).all()
    
    total = len(customers)
    enterprise = sum(1 for c in customers if c.customer_tier == "Enterprise")
    tier_1 = sum(1 for c in customers if c.customer_tier == "Tier-1")
    standard = sum(1 for c in customers if c.customer_tier == "Standard")
    total_credit = sum(c.credit_limit for c in customers) if customers else Decimal("0.00")
    total_exposure = sum(c.total_revenue for c in customers) if customers else Decimal("0.00")
    avg_score = (sum(c.payment_score for c in customers) / total) if total > 0 else Decimal("0.0")

    summary = CustomerSummary(
        total_customers=total,
        enterprise_count=enterprise,
        tier_1_count=tier_1,
        standard_count=standard,
        total_credit_granted=Decimal(str(total_credit)),
        total_outstanding_exposure=Decimal(str(total_exposure)),
        avg_payment_score=round(Decimal(str(avg_score)), 1),
    )

    return CustomerListResponse(summary=summary, customers=customers)
