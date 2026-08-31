from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.api.deps import get_current_merchant_id
from app.models.snapshot import EconomicSnapshot
from app.schemas.snapshot import (
    SnapshotTimelineResponse,
    SnapshotTrendPoint,
    EconomicSnapshotResponse,
)
from app.services.formatters import format_inr
from decimal import Decimal

router = APIRouter()


@router.get("", response_model=SnapshotTimelineResponse, summary="Get historical economic snapshots & chart timeline")
def get_snapshots(
    merchant_id: str = Depends(get_current_merchant_id),
    db: Session = Depends(get_db),
):
    snapshots = (
        db.query(EconomicSnapshot)
        .filter(EconomicSnapshot.merchant_id == merchant_id)
        .order_by(EconomicSnapshot.snapshot_date.asc())
        .all()
    )

    trend_points = []
    recent_responses = []

    for s in snapshots:
        date_str = s.snapshot_date.strftime("%Y-%m-%d")
        cash_f = float(s.cash_balance)
        rec_f = float(s.total_receivables)
        pay_f = float(s.total_payables)
        inv_f = float(s.inventory_value)
        wc_f = float(s.working_capital)

        trend_points.append(
            SnapshotTrendPoint(
                date=date_str,
                timestamp=s.snapshot_date,
                cash_balance=cash_f,
                total_receivables=rec_f,
                total_payables=pay_f,
                inventory_value=inv_f,
                working_capital=wc_f,
                cash_runway_days=s.cash_runway_days,
                liquidity_stress_score=s.liquidity_stress_score,
                event_marker=s.event_marker,
            )
        )

        recent_responses.append(
            EconomicSnapshotResponse(
                id=s.id,
                merchant_id=s.merchant_id,
                snapshot_date=s.snapshot_date,
                cash_balance=Decimal(str(s.cash_balance)),
                total_receivables=Decimal(str(s.total_receivables)),
                total_payables=Decimal(str(s.total_payables)),
                inventory_value=Decimal(str(s.inventory_value)),
                aging_inventory_value=Decimal(str(s.aging_inventory_value)),
                gross_margin_pct=Decimal(str(s.gross_margin_pct)),
                cash_runway_days=s.cash_runway_days,
                quick_ratio=Decimal(str(s.quick_ratio)),
                current_ratio=Decimal(str(s.current_ratio)),
                working_capital=Decimal(str(s.working_capital)),
                dso_days=s.dso_days,
                dpo_days=s.dpo_days,
                dio_days=s.dio_days,
                cash_conversion_cycle=s.cash_conversion_cycle,
                liquidity_stress_score=s.liquidity_stress_score,
                event_marker=s.event_marker,
                notes=s.notes,
                cash_balance_formatted=format_inr(s.cash_balance),
                receivables_formatted=format_inr(s.total_receivables),
                payables_formatted=format_inr(s.total_payables),
                inventory_formatted=format_inr(s.inventory_value),
                working_capital_formatted=format_inr(s.working_capital),
                created_at=s.created_at,
            )
        )

    # Return descending recent snapshots for easy tabular views
    recent_responses.reverse()

    start_d = snapshots[0].snapshot_date if snapshots else None
    end_d = snapshots[-1].snapshot_date if snapshots else None

    return SnapshotTimelineResponse(
        total_points=len(trend_points),
        start_date=start_d,
        end_date=end_d,
        data=trend_points,
        recent_snapshots=recent_responses,
    )
