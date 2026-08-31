import json
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.api.deps import get_current_merchant_id
from app.models.activity import ActivityEvent
from app.schemas.activity import (
    ActivityListResponse,
    ActivityEventResponse,
    ActivitySummary,
)

router = APIRouter()


@router.get("", response_model=ActivityListResponse, summary="Get activity events feed")
def get_activity(
    category: Optional[str] = Query(None, description="Filter by event category: Liquidity, Inventory, Receivables, Payables, Transactions, Demand"),
    severity: Optional[str] = Query(None, description="Filter by severity: Info, Low, Medium, High, Critical"),
    merchant_id: str = Depends(get_current_merchant_id),
    db: Session = Depends(get_db),
):
    query = (
        db.query(ActivityEvent)
        .filter(ActivityEvent.merchant_id == merchant_id)
        .order_by(ActivityEvent.created_at.desc())
    )

    all_events = query.all()

    crit = 0
    high = 0
    med = 0
    info = 0
    categories = set()
    items = []

    for a in all_events:
        categories.add(a.category)
        if a.severity == "Critical":
            crit += 1
        elif a.severity == "High":
            high += 1
        elif a.severity == "Medium":
            med += 1
        else:
            info += 1

        if category and a.category.lower() != category.lower():
            continue
        if severity and a.severity.lower() != severity.lower():
            continue

        meta_parsed = None
        if a.metadata_json:
            try:
                meta_parsed = json.loads(a.metadata_json)
            except Exception:
                meta_parsed = None

        items.append(
            ActivityEventResponse(
                id=a.id,
                merchant_id=a.merchant_id,
                event_type=a.event_type,
                category=a.category,
                title=a.title,
                description=a.description,
                severity=a.severity,
                metadata_json=a.metadata_json,
                parsed_metadata=meta_parsed,
                created_at=a.created_at,
            )
        )

    summary = ActivitySummary(
        total_events=len(all_events),
        critical_count=crit,
        high_count=high,
        medium_count=med,
        info_count=info,
        categories=sorted(list(categories)),
    )

    return ActivityListResponse(summary=summary, events=items)
