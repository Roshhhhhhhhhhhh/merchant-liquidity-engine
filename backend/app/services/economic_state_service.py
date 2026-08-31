import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.merchant import Merchant
from app.models.snapshot import EconomicSnapshot
from app.models.receivable import Receivable
from app.models.payable import Payable
from app.models.inventory import InventoryItem
from app.models.product import Product
from app.models.transaction import Transaction
from app.models.customer import Customer
from app.schemas.economic_state import (
    DimensionStateModel,
    PressureDriverModel,
    StateScoreModel,
    EconomicStateModel,
    StateHistoryPoint,
    StateHistoryResponse,
    StateDriversResponse,
    MetricDelta,
    StateDeltaResponse,
    EconomicValueModel,
    EconomicActionModel,
    ActionEvaluationResponse,
)
from app.services.formatters import format_inr


class EconomicModelConfig:
    # Component weights for the Economic Pressure Score (Sum = 1.0)
    WEIGHT_LIQUIDITY_RUNWAY = Decimal("0.25")
    WEIGHT_OVERDUE_RECEIVABLES = Decimal("0.20")
    WEIGHT_AGING_INVENTORY = Decimal("0.20")
    WEIGHT_NEAR_TERM_PAYABLES = Decimal("0.15")
    WEIGHT_DEMAND_TREND = Decimal("0.10")
    WEIGHT_MARGIN_COMPRESSION = Decimal("0.10")

    # Thresholds
    AGING_INVENTORY_DAYS_THRESHOLD = 45
    NEAR_TERM_PAYABLES_DAYS = 12
    TARGET_GROSS_MARGIN_PCT = Decimal("25.0")
    SAFE_RUNWAY_DAYS_BUFFER = 45

    # Classification Thresholds
    SCORE_STRONG_MAX = 24
    SCORE_HEALTHY_MAX = 44
    SCORE_WATCH_MAX = 59
    SCORE_STRESSED_MAX = 74
    # Score >= 75 is Critical


def round_decimal(val: Decimal, places: int = 2) -> Decimal:
    q = Decimal("10") ** -places
    return val.quantize(q, rounding=ROUND_HALF_UP)


class EconomicStateService:
    @classmethod
    def calculate_current_state(cls, db: Session, merchant_id: str) -> EconomicStateModel:
        merchant = db.query(Merchant).filter(Merchant.id == merchant_id).first()
        if not merchant:
            raise ValueError(f"Merchant with ID '{merchant_id}' not found.")

        now = datetime.datetime.utcnow()

        # 1. Authoritative Cash Balance (from latest snapshot ledger or cash reserve)
        latest_snapshot = (
            db.query(EconomicSnapshot)
            .filter(EconomicSnapshot.merchant_id == merchant_id)
            .order_by(EconomicSnapshot.snapshot_date.desc())
            .first()
        )
        cash_balance = (
            Decimal(str(latest_snapshot.cash_balance))
            if latest_snapshot
            else Decimal("485000.00")
        )

        # 2. Receivables Ledger Derivation
        receivables_records = (
            db.query(Receivable)
            .filter(Receivable.merchant_id == merchant_id)
            .all()
        )
        total_receivables = Decimal("0.00")
        overdue_receivables = Decimal("0.00")
        receivables_due_14d = Decimal("0.00")
        fourteen_days_ahead = now + datetime.timedelta(days=14)

        for r in receivables_records:
            bal = Decimal(str(r.balance_due))
            total_receivables += bal
            is_overdue = (
                r.status in ("Overdue", "Severely Overdue")
                or (r.due_date and r.due_date < now and bal > 0)
            )
            if is_overdue:
                overdue_receivables += bal
            elif r.due_date and now <= r.due_date <= fourteen_days_ahead and bal > 0:
                receivables_due_14d += bal

        # 3. Payables Ledger Derivation
        payables_records = (
            db.query(Payable)
            .filter(Payable.merchant_id == merchant_id)
            .all()
        )
        total_payables = Decimal("0.00")
        near_term_payables = Decimal("0.00")
        near_term_cutoff = now + datetime.timedelta(days=EconomicModelConfig.NEAR_TERM_PAYABLES_DAYS)

        for p in payables_records:
            bal = Decimal(str(p.balance_due))
            total_payables += bal
            if p.status in ("Pending", "Scheduled") and p.due_date and p.due_date <= near_term_cutoff and bal > 0:
                near_term_payables += bal

        # 4. Inventory Valuation & Aging Derivation
        inv_items = (
            db.query(InventoryItem)
            .join(Product, InventoryItem.product_id == Product.id)
            .filter(InventoryItem.merchant_id == merchant_id)
            .all()
        )
        total_inventory_val = Decimal("0.00")
        aging_inventory_val = Decimal("0.00")
        available_inventory_units = 0

        for item in inv_items:
            units = item.available_quantity
            cost = Decimal(str(item.product.unit_cost))
            item_val = Decimal(units) * cost
            available_inventory_units += units
            total_inventory_val += item_val

            if (
                item.days_in_stock > EconomicModelConfig.AGING_INVENTORY_DAYS_THRESHOLD
                or item.status in ("Aging", "Critical")
            ):
                aging_inventory_val += item_val

        # 5. Transactions & Rolling Gross Margin / Revenue Derivation
        thirty_days_ago = now - datetime.timedelta(days=30)
        recent_txs = (
            db.query(Transaction)
            .filter(
                Transaction.merchant_id == merchant_id,
                Transaction.created_at >= thirty_days_ago,
            )
            .all()
        )
        recent_gross_revenue = Decimal("0.00")
        recent_total_cogs = Decimal("0.00")
        for tx in recent_txs:
            recent_gross_revenue += Decimal(str(tx.gross_value))
            recent_total_cogs += Decimal(str(tx.cost_value))

        if recent_gross_revenue > 0:
            gross_margin_pct = round_decimal(
                ((recent_gross_revenue - recent_total_cogs) / recent_gross_revenue) * Decimal("100"), 1
            )
        elif latest_snapshot:
            gross_margin_pct = Decimal(str(latest_snapshot.gross_margin_pct))
        else:
            gross_margin_pct = Decimal("28.4")

        # 6. Demand Trend Derivation (Rolling 15-day Window Comparison)
        fifteen_days_ago = now - datetime.timedelta(days=15)
        tx_window_recent = [tx for tx in recent_txs if tx.created_at >= fifteen_days_ago]
        tx_window_previous = [tx for tx in recent_txs if tx.created_at < fifteen_days_ago]

        w_recent_rev = sum(Decimal(str(tx.gross_value)) for tx in tx_window_recent)
        w_prev_rev = sum(Decimal(str(tx.gross_value)) for tx in tx_window_previous)

        if w_prev_rev > 0:
            demand_trend_pct = round_decimal(
                ((w_recent_rev - w_prev_rev) / w_prev_rev) * Decimal("100"), 1
            )
        else:
            demand_trend_pct = Decimal("-4.2")

        # 7. Customer Portfolio & Payment Velocity
        customers = (
            db.query(Customer)
            .filter(Customer.merchant_id == merchant_id)
            .all()
        )
        total_customer_revenue = Decimal("0.00")
        total_payment_score = Decimal("0.00")
        for c in customers:
            total_customer_revenue += Decimal(str(c.total_revenue))
            total_payment_score += Decimal(str(c.payment_score))

        avg_payment_score = (
            (total_payment_score / Decimal(len(customers)))
            if customers
            else Decimal("80.0")
        )
        overdue_ratio = (
            (overdue_receivables / total_receivables)
            if total_receivables > 0
            else Decimal("0.0")
        )
        payment_velocity = round_decimal(
            max(Decimal("0.1"), min(Decimal("1.0"), (avg_payment_score / Decimal("100")) * (Decimal("1.0") - (overdue_ratio * Decimal("0.3"))))),
            2
        )

        # 8. Cash Runway Calculation (Deterministic net daily burn)
        baseline_fixed_daily_outflow = Decimal("12500.00")
        near_term_daily_payables = near_term_payables / Decimal(str(EconomicModelConfig.NEAR_TERM_PAYABLES_DAYS)) if near_term_payables > 0 else Decimal("0.00")
        expected_daily_outflow = baseline_fixed_daily_outflow + near_term_daily_payables

        expected_daily_inflow = (
            (receivables_due_14d * payment_velocity) / Decimal("14")
            if receivables_due_14d > 0
            else Decimal("0.00")
        )

        expected_daily_net_burn = expected_daily_outflow - expected_daily_inflow

        if expected_daily_net_burn > 0:
            raw_runway_days = int(cash_balance / expected_daily_net_burn)
            cash_runway_days = max(1, raw_runway_days)
            cash_runway_display = f"{cash_runway_days} Days"
        else:
            cash_runway_days = 90
            cash_runway_display = "90+ Days (Positive Cash Flow)"

        # 9. Economic Pressure Score Calculation (0 - 100)
        # Component 1: Liquidity Runway Pressure
        if cash_runway_days <= 10:
            s_liq = Decimal("100.0")
        elif cash_runway_days <= 20:
            s_liq = Decimal("85.0") + (Decimal(20 - cash_runway_days) * Decimal("1.5"))
        elif cash_runway_days <= 30:
            s_liq = Decimal("60.0") + (Decimal(30 - cash_runway_days) * Decimal("2.5"))
        elif cash_runway_days <= 45:
            s_liq = Decimal("30.0") + (Decimal(45 - cash_runway_days) * Decimal("2.0"))
        elif cash_runway_days < 60:
            s_liq = Decimal(60 - cash_runway_days) * Decimal("2.0")
        else:
            s_liq = Decimal("0.0")

        # Component 2: Overdue Receivables Pressure
        overdue_pct = (
            (overdue_receivables / total_receivables) * Decimal("100")
            if total_receivables > 0
            else Decimal("0.0")
        )
        s_rec = min(Decimal("100.0"), overdue_pct * Decimal("2.4"))

        # Component 3: Aging Inventory Pressure
        aging_pct = (
            (aging_inventory_val / total_inventory_val) * Decimal("100")
            if total_inventory_val > 0
            else Decimal("0.0")
        )
        s_inv = min(Decimal("100.0"), aging_pct * Decimal("2.8"))

        # Component 4: Near-Term Payables vs Cash
        payables_coverage_pct = (
            (near_term_payables / cash_balance) * Decimal("100")
            if cash_balance > 0
            else Decimal("100.0")
        )
        s_pay = min(Decimal("100.0"), payables_coverage_pct * Decimal("1.1"))

        # Component 5: Demand Deterioration
        if demand_trend_pct < 0:
            s_dem = min(Decimal("100.0"), abs(demand_trend_pct) * Decimal("14.0"))
        else:
            s_dem = Decimal("0.0")

        # Component 6: Margin Compression
        if gross_margin_pct < EconomicModelConfig.TARGET_GROSS_MARGIN_PCT:
            s_gm = min(Decimal("100.0"), (EconomicModelConfig.TARGET_GROSS_MARGIN_PCT - gross_margin_pct) * Decimal("12.0"))
        else:
            s_gm = Decimal("0.0")

        # Weighted Composite Score
        composite_score_dec = (
            (EconomicModelConfig.WEIGHT_LIQUIDITY_RUNWAY * s_liq)
            + (EconomicModelConfig.WEIGHT_OVERDUE_RECEIVABLES * s_rec)
            + (EconomicModelConfig.WEIGHT_AGING_INVENTORY * s_inv)
            + (EconomicModelConfig.WEIGHT_NEAR_TERM_PAYABLES * s_pay)
            + (EconomicModelConfig.WEIGHT_DEMAND_TREND * s_dem)
            + (EconomicModelConfig.WEIGHT_MARGIN_COMPRESSION * s_gm)
        )
        pressure_score = int(min(Decimal("100"), max(Decimal("0"), composite_score_dec)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

        # 10. Business State Classification
        if pressure_score <= EconomicModelConfig.SCORE_STRONG_MAX:
            state_classification = "Strong"
            liquidity_status = "Healthy"
            headline = "Strong liquidity and working capital equilibrium"
            summary = "Operating cash flow is robust with low overdue receivables and minimal locked inventory."
        elif pressure_score <= EconomicModelConfig.SCORE_HEALTHY_MAX:
            state_classification = "Healthy"
            liquidity_status = "Healthy"
            headline = "Operating within sustainable liquidity parameters"
            summary = "Working capital velocity is steady, though routine collection monitoring is recommended."
        elif pressure_score <= EconomicModelConfig.SCORE_WATCH_MAX:
            state_classification = "Watch"
            liquidity_status = "Watch"
            headline = "Moderate liquidity equilibrium under watch"
            summary = "Near-term cash buffer is adequate, but working capital velocity exhibits slight compression."
        elif pressure_score <= EconomicModelConfig.SCORE_STRESSED_MAX:
            state_classification = "Stressed"
            liquidity_status = "Warning"
            headline = "Liquidity pressure is increasing"
            summary = f"Working capital restricted primarily because overdue receivables have reached {format_inr(overdue_receivables)} ({round_decimal(overdue_pct, 1)}% of book) and aged inventory locks {format_inr(aging_inventory_val)}."
        else:
            state_classification = "Critical"
            liquidity_status = "Critical"
            headline = "Severe liquidity pressure detected"
            summary = f"Immediate cash runway depletion risk. Near-term supplier dues of {format_inr(near_term_payables)} exceed sustainable operating reserves."

        # 11. Deterministic Pressure Drivers Ranking
        candidate_drivers = [
            {
                "id": "driver-rec-overdue",
                "title": f"{format_inr(overdue_receivables)} receivables overdue past 30 days",
                "impact_amount": overdue_receivables,
                "impact_formatted": format_inr(overdue_receivables),
                "category": "Receivables",
                "description": f"Overdue invoices account for {round_decimal(overdue_pct, 1)}% of total ledger, lengthening collection cycle and restricting operational cash.",
                "severity": "Critical" if overdue_pct > 30 else ("Warning" if overdue_pct > 15 else "Watch"),
                "contribution_score": round_decimal(EconomicModelConfig.WEIGHT_OVERDUE_RECEIVABLES * s_rec, 1),
            },
            {
                "id": "driver-inv-aged",
                "title": f"{format_inr(aging_inventory_val)} inventory aged over 45 days",
                "impact_amount": aging_inventory_val,
                "impact_formatted": format_inr(aging_inventory_val),
                "category": "Inventory",
                "description": f"Aged inventory represents {round_decimal(aging_pct, 1)}% of total stock valuation, locking working capital in slow-moving SKUs.",
                "severity": "Warning" if aging_pct > 20 else "Watch",
                "contribution_score": round_decimal(EconomicModelConfig.WEIGHT_AGING_INVENTORY * s_inv, 1),
            },
            {
                "id": "driver-pay-nearterm",
                "title": f"{format_inr(near_term_payables)} supplier obligations due within 12 days",
                "impact_amount": near_term_payables,
                "impact_formatted": format_inr(near_term_payables),
                "category": "Payables",
                "description": f"Imminent vendor dues require {round_decimal(payables_coverage_pct, 1)}% of current liquid cash balance ({format_inr(cash_balance)}).",
                "severity": "Warning" if payables_coverage_pct > 65 else "Watch",
                "contribution_score": round_decimal(EconomicModelConfig.WEIGHT_NEAR_TERM_PAYABLES * s_pay, 1),
            },
            {
                "id": "driver-demand-soft",
                "title": f"B2B order volume shift ({demand_trend_pct}% MoM)",
                "impact_amount": None,
                "impact_formatted": f"{demand_trend_pct}%",
                "category": "Demand",
                "description": "Short-term order pacing has softened, reducing forward cash inflows from immediate sales.",
                "severity": "Watch" if demand_trend_pct < 0 else "Info",
                "contribution_score": round_decimal(EconomicModelConfig.WEIGHT_DEMAND_TREND * s_dem, 1),
            },
            {
                "id": "driver-liq-runway",
                "title": f"Cash runway estimated at {cash_runway_days} days",
                "impact_amount": cash_balance,
                "impact_formatted": f"{cash_runway_days}d",
                "category": "Liquidity",
                "description": f"Operating runway is below the 45-day safety buffer due to net daily cash burn of {format_inr(expected_daily_net_burn)}/day.",
                "severity": "Critical" if cash_runway_days < 20 else ("Warning" if cash_runway_days < 30 else "Watch"),
                "contribution_score": round_decimal(EconomicModelConfig.WEIGHT_LIQUIDITY_RUNWAY * s_liq, 1),
            },
        ]

        candidate_drivers.sort(key=lambda x: x["contribution_score"], reverse=True)
        top_drivers: List[PressureDriverModel] = []
        for idx, d in enumerate(candidate_drivers, start=1):
            top_drivers.append(
                PressureDriverModel(
                    id=d["id"],
                    title=d["title"],
                    impact_amount=d["impact_amount"],
                    impact_formatted=d["impact_formatted"],
                    category=d["category"],
                    description=d["description"],
                    severity=d["severity"],
                    contribution_score=d["contribution_score"],
                    rank=idx,
                )
            )

        # 12. Working Capital & Ratios
        working_capital = (cash_balance + total_receivables + total_inventory_val) - total_payables
        quick_ratio = (
            round_decimal((cash_balance + total_receivables) / total_payables, 2)
            if total_payables > 0
            else Decimal("2.10")
        )
        current_ratio = (
            round_decimal((cash_balance + total_receivables + total_inventory_val) / total_payables, 2)
            if total_payables > 0
            else Decimal("4.50")
        )

        dso_days = latest_snapshot.dso_days if latest_snapshot else 42
        dpo_days = latest_snapshot.dpo_days if latest_snapshot else 35
        dio_days = latest_snapshot.dio_days if latest_snapshot else 58
        cash_conversion_cycle = dio_days + dso_days - dpo_days

        # 13. Build 10 Dimension State Models
        dim_cash = DimensionStateModel(
            dimension="cash",
            name="Cash Balance",
            value=cash_balance,
            formatted_value=format_inr(cash_balance),
            status="Watch" if cash_runway_days < 30 else "Healthy",
            label="Available now",
            trend="Down",
            trend_pct=Decimal("-5.4"),
            benchmark="₹6.50L Target",
        )
        dim_receivables = DimensionStateModel(
            dimension="receivables",
            name="Receivables Book",
            value=total_receivables,
            formatted_value=format_inr(total_receivables),
            status="Warning" if overdue_pct > 25 else "Watch",
            label=f"{format_inr(overdue_receivables)} overdue",
            trend="Up",
            trend_pct=Decimal("8.2"),
            benchmark="DSO 42d",
        )
        dim_payables = DimensionStateModel(
            dimension="payables",
            name="Accounts Payable",
            value=total_payables,
            formatted_value=format_inr(total_payables),
            status="Watch" if payables_coverage_pct > 65 else "Healthy",
            label=f"{format_inr(near_term_payables)} due in 12d",
            trend="Up",
            trend_pct=Decimal("4.1"),
            benchmark="DPO 35d",
        )
        dim_inventory = DimensionStateModel(
            dimension="inventory_value",
            name="Inventory Valuation",
            value=total_inventory_val,
            formatted_value=format_inr(total_inventory_val),
            status="Healthy",
            label=f"{len(inv_items)} SKUs active",
            trend="Stable",
            trend_pct=Decimal("1.2"),
            benchmark="DIO 58d",
        )
        dim_aging_inventory = DimensionStateModel(
            dimension="aging_inventory",
            name="Aging Inventory",
            value=aging_inventory_val,
            formatted_value=format_inr(aging_inventory_val),
            status="Warning" if aging_pct > 20 else "Watch",
            label=f"{round_decimal(aging_pct, 1)}% of total stock",
            trend="Up",
            trend_pct=Decimal("6.5"),
            benchmark="<15% Target",
        )
        dim_gross_margin = DimensionStateModel(
            dimension="gross_margin",
            name="Gross Margin",
            value=gross_margin_pct,
            formatted_value=f"{gross_margin_pct}%",
            status="Healthy" if gross_margin_pct >= EconomicModelConfig.TARGET_GROSS_MARGIN_PCT else "Watch",
            label="Weighted blended margin",
            trend="Stable",
            trend_pct=Decimal("0.4"),
            benchmark="25.0% Min",
        )
        dim_demand_trend = DimensionStateModel(
            dimension="demand_trend",
            name="Demand Trend",
            value=demand_trend_pct,
            formatted_value=f"{demand_trend_pct}%",
            status="Watch" if demand_trend_pct < 0 else "Healthy",
            label="MoM order velocity",
            trend="Down" if demand_trend_pct < 0 else "Up",
            trend_pct=demand_trend_pct,
            benchmark="Sector Avg +2.0%",
        )
        dim_customer_val = DimensionStateModel(
            dimension="customer_value",
            name="Customer Portfolio",
            value=total_customer_revenue,
            formatted_value=format_inr(total_customer_revenue),
            status="Healthy",
            label=f"{len(customers)} Active Accounts",
            trend="Up",
            trend_pct=Decimal("3.8"),
            benchmark="92% Retention",
        )
        dim_fulfillment = DimensionStateModel(
            dimension="fulfillment_capacity",
            name="Fulfillment Capacity",
            value=Decimal("84.0"),
            formatted_value="84.0%",
            status="Healthy",
            label="Warehouse throughput",
            trend="Stable",
            trend_pct=Decimal("0.0"),
            benchmark="85% Max Opt",
        )
        dim_runway = DimensionStateModel(
            dimension="cash_runway",
            name="Cash Runway",
            value=Decimal(cash_runway_days),
            formatted_value=cash_runway_display,
            status="Warning" if cash_runway_days < 30 else "Healthy",
            label="Operating runway",
            trend="Down",
            trend_pct=Decimal("-8.0"),
            benchmark="45d Safe Buffer",
        )

        return EconomicStateModel(
            merchant_id=merchant.id,
            merchant_name=merchant.name,
            trade_name=merchant.trade_name,
            gst_number=merchant.gst_number,
            industry=merchant.industry,
            as_of=now,
            cash=dim_cash,
            receivables=dim_receivables,
            payables=dim_payables,
            inventory_value=dim_inventory,
            aging_inventory=dim_aging_inventory,
            gross_margin=dim_gross_margin,
            demand_trend=dim_demand_trend,
            customer_value=dim_customer_val,
            fulfillment_capacity=dim_fulfillment,
            cash_runway=dim_runway,
            cash_position=cash_balance,
            total_receivables=total_receivables,
            overdue_receivables=overdue_receivables,
            total_payables=total_payables,
            near_term_payables=near_term_payables,
            inventory_valuation=total_inventory_val,
            aging_inventory_value=aging_inventory_val,
            available_inventory_units=available_inventory_units,
            gross_margin_pct=gross_margin_pct,
            recent_revenue=recent_gross_revenue,
            recent_demand_trend_pct=demand_trend_pct,
            payment_velocity=payment_velocity,
            customer_portfolio_value=total_customer_revenue,
            fulfillment_capacity_pct=Decimal("84.0"),
            cash_runway_days=cash_runway_days,
            cash_runway_display=cash_runway_display,
            pressure_score=pressure_score,
            liquidity_stress_score=pressure_score,
            state=state_classification,
            liquidity_status=liquidity_status,
            liquidity_outlook_headline=headline,
            liquidity_outlook_summary=summary,
            top_drivers=top_drivers,
            drivers=top_drivers,
            working_capital=working_capital,
            working_capital_formatted=format_inr(working_capital),
            quick_ratio=quick_ratio,
            current_ratio=current_ratio,
            dso_days=dso_days,
            dpo_days=dpo_days,
            dio_days=dio_days,
            cash_conversion_cycle=cash_conversion_cycle,
        )

    @classmethod
    def get_state_score(cls, db: Session, merchant_id: str) -> StateScoreModel:
        state = cls.calculate_current_state(db=db, merchant_id=merchant_id)
        component_weights = {
            "liquidity_runway": EconomicModelConfig.WEIGHT_LIQUIDITY_RUNWAY,
            "overdue_receivables": EconomicModelConfig.WEIGHT_OVERDUE_RECEIVABLES,
            "aging_inventory": EconomicModelConfig.WEIGHT_AGING_INVENTORY,
            "near_term_payables": EconomicModelConfig.WEIGHT_NEAR_TERM_PAYABLES,
            "demand_trend": EconomicModelConfig.WEIGHT_DEMAND_TREND,
            "margin_compression": EconomicModelConfig.WEIGHT_MARGIN_COMPRESSION,
        }
        component_scores = {
            driver.category.lower(): driver.contribution_score
            for driver in state.top_drivers
        }
        return StateScoreModel(
            pressure_score=state.pressure_score,
            state=state.state,
            state_description=state.liquidity_outlook_summary,
            component_scores=component_scores,
            component_weights=component_weights,
        )

    @classmethod
    def get_state_drivers(cls, db: Session, merchant_id: str) -> StateDriversResponse:
        state = cls.calculate_current_state(db=db, merchant_id=merchant_id)
        return StateDriversResponse(
            merchant_id=state.merchant_id,
            as_of=state.as_of,
            pressure_score=state.pressure_score,
            state=state.state,
            drivers=state.top_drivers,
            total_drivers_count=len(state.top_drivers),
        )

    @classmethod
    def get_state_history(cls, db: Session, merchant_id: str) -> StateHistoryResponse:
        snapshots = (
            db.query(EconomicSnapshot)
            .filter(EconomicSnapshot.merchant_id == merchant_id)
            .order_by(EconomicSnapshot.snapshot_date.asc())
            .all()
        )

        history_points: List[StateHistoryPoint] = []
        for s in snapshots:
            score = s.liquidity_stress_score
            if score <= EconomicModelConfig.SCORE_STRONG_MAX:
                st = "Strong"
            elif score <= EconomicModelConfig.SCORE_HEALTHY_MAX:
                st = "Healthy"
            elif score <= EconomicModelConfig.SCORE_WATCH_MAX:
                st = "Watch"
            elif score <= EconomicModelConfig.SCORE_STRESSED_MAX:
                st = "Stressed"
            else:
                st = "Critical"

            history_points.append(
                StateHistoryPoint(
                    date=s.snapshot_date.strftime("%Y-%m-%d"),
                    timestamp=s.snapshot_date,
                    cash=Decimal(str(s.cash_balance)),
                    receivables=Decimal(str(s.total_receivables)),
                    overdue_receivables=Decimal(str(s.total_receivables)) * Decimal("0.31"),
                    payables=Decimal(str(s.total_payables)),
                    inventory=Decimal(str(s.inventory_value)),
                    aging_inventory=Decimal(str(s.aging_inventory_value)),
                    gross_margin_pct=Decimal(str(s.gross_margin_pct)),
                    runway_days=s.cash_runway_days,
                    pressure_score=score,
                    state=st,
                    demand_trend_pct=Decimal("-4.2"),
                    working_capital=Decimal(str(s.working_capital)),
                    event_marker=s.event_marker,
                )
            )

        start_date = history_points[0].date if history_points else ""
        end_date = history_points[-1].date if history_points else ""

        return StateHistoryResponse(
            merchant_id=merchant_id,
            total_points=len(history_points),
            start_date=start_date,
            end_date=end_date,
            history=history_points,
        )

    @classmethod
    def get_state_delta(
        cls, db: Session, merchant_id: str, days_ago: int = 30
    ) -> StateDeltaResponse:
        current_state = cls.calculate_current_state(db=db, merchant_id=merchant_id)

        # Fetch baseline snapshot ~days_ago
        target_date = current_state.as_of - datetime.timedelta(days=days_ago)
        baseline_snapshot = (
            db.query(EconomicSnapshot)
            .filter(
                EconomicSnapshot.merchant_id == merchant_id,
                EconomicSnapshot.snapshot_date <= target_date + datetime.timedelta(days=2),
            )
            .order_by(EconomicSnapshot.snapshot_date.asc())
            .first()
        )

        if not baseline_snapshot:
            baseline_snapshot = (
                db.query(EconomicSnapshot)
                .filter(EconomicSnapshot.merchant_id == merchant_id)
                .order_by(EconomicSnapshot.snapshot_date.asc())
                .first()
            )

        b_cash = Decimal(str(baseline_snapshot.cash_balance)) if baseline_snapshot else current_state.cash_position
        b_rec = Decimal(str(baseline_snapshot.total_receivables)) if baseline_snapshot else current_state.total_receivables
        b_pay = Decimal(str(baseline_snapshot.total_payables)) if baseline_snapshot else current_state.total_payables
        b_inv = Decimal(str(baseline_snapshot.inventory_value)) if baseline_snapshot else current_state.inventory_valuation
        b_aging = Decimal(str(baseline_snapshot.aging_inventory_value)) if baseline_snapshot else current_state.aging_inventory_value
        b_margin = Decimal(str(baseline_snapshot.gross_margin_pct)) if baseline_snapshot else current_state.gross_margin_pct
        b_runway = Decimal(str(baseline_snapshot.cash_runway_days)) if baseline_snapshot else Decimal(str(current_state.cash_runway_days))
        b_score = baseline_snapshot.liquidity_stress_score if baseline_snapshot else current_state.pressure_score
        b_date = baseline_snapshot.snapshot_date if baseline_snapshot else (current_state.as_of - datetime.timedelta(days=days_ago))

        def make_delta(metric: str, label: str, b_val: Decimal, a_val: Decimal, unit: str = "INR", is_pct: bool = False, higher_is_better: bool = True) -> MetricDelta:
            abs_change = a_val - b_val
            pct_change = (
                round_decimal((abs_change / b_val) * Decimal("100"), 1)
                if b_val != 0
                else Decimal("0.0")
            )
            if abs_change == 0:
                direction = "Neutral"
            elif (abs_change > 0 and higher_is_better) or (abs_change < 0 and not higher_is_better):
                direction = "Positive"
            else:
                direction = "Negative"

            if unit == "INR":
                fmt_b = format_inr(b_val)
                fmt_a = format_inr(a_val)
                fmt_c = f"{'+' if abs_change > 0 else ''}{format_inr(abs_change)}"
            elif unit == "Days":
                fmt_b = f"{int(b_val)}d"
                fmt_a = f"{int(a_val)}d"
                fmt_c = f"{'+' if abs_change > 0 else ''}{int(abs_change)}d"
            elif is_pct or unit == "%":
                fmt_b = f"{b_val}%"
                fmt_a = f"{a_val}%"
                fmt_c = f"{'+' if abs_change > 0 else ''}{abs_change}%"
            else:
                fmt_b = str(b_val)
                fmt_a = str(a_val)
                fmt_c = f"{'+' if abs_change > 0 else ''}{abs_change}"

            return MetricDelta(
                metric=metric,
                label=label,
                before=b_val,
                after=a_val,
                absolute_change=abs_change,
                percentage_change=pct_change,
                direction=direction,
                unit=unit,
                formatted_before=fmt_b,
                formatted_after=fmt_a,
                formatted_change=fmt_c,
            )

        deltas = [
            make_delta("cash", "Available Cash Balance", b_cash, current_state.cash_position, "INR", higher_is_better=True),
            make_delta("receivables", "Receivables Book", b_rec, current_state.total_receivables, "INR", higher_is_better=False),
            make_delta("payables", "Accounts Payable", b_pay, current_state.total_payables, "INR", higher_is_better=False),
            make_delta("inventory_value", "Inventory Valuation", b_inv, current_state.inventory_valuation, "INR", higher_is_better=True),
            make_delta("aging_inventory", "Aging Inventory (>45d)", b_aging, current_state.aging_inventory_value, "INR", higher_is_better=False),
            make_delta("gross_margin", "Gross Margin", b_margin, current_state.gross_margin_pct, "%", is_pct=True, higher_is_better=True),
            make_delta("cash_runway", "Cash Runway", b_runway, Decimal(str(current_state.cash_runway_days)), "Days", higher_is_better=True),
            make_delta("pressure_score", "Pressure Score", Decimal(b_score), Decimal(current_state.pressure_score), "Points", higher_is_better=False),
        ]

        b_state = "Healthy" if b_score < 45 else ("Watch" if b_score < 60 else "Stressed")

        summary = (
            f"Over the {days_ago}-day observation window, liquid cash declined by {format_inr(b_cash - current_state.cash_position)} "
            f"while overdue receivables and aged stock expanded, raising the composite pressure score from {b_score}/100 ({b_state}) "
            f"to {current_state.pressure_score}/100 ({current_state.state})."
        )

        return StateDeltaResponse(
            merchant_id=merchant_id,
            baseline_date=b_date,
            current_date=current_state.as_of,
            baseline_state=b_state,
            current_state=current_state.state,
            baseline_pressure_score=b_score,
            current_pressure_score=current_state.pressure_score,
            deltas=deltas,
            summary=summary,
        )

    @classmethod
    def calculate_economic_value(
        cls,
        contribution_margin_value: Decimal,
        liquidity_improvement_value: Decimal,
        inventory_relief_value: Decimal,
        receivable_improvement_value: Decimal,
        economic_risk_cost: Decimal,
    ) -> EconomicValueModel:
        LAMBDA_LIQUIDITY = Decimal("0.15")
        LAMBDA_INVENTORY = Decimal("0.10")
        LAMBDA_RECEIVABLE = Decimal("0.08")

        weighted_liq = round_decimal(liquidity_improvement_value * LAMBDA_LIQUIDITY, 2)
        weighted_inv = round_decimal(inventory_relief_value * LAMBDA_INVENTORY, 2)
        weighted_rec = round_decimal(receivable_improvement_value * LAMBDA_RECEIVABLE, 2)

        total_evc = round_decimal(
            contribution_margin_value + weighted_liq + weighted_inv + weighted_rec - economic_risk_cost,
            2
        )

        assumptions = {
            "lambda_liquidity_weight": float(LAMBDA_LIQUIDITY),
            "lambda_inventory_relief_weight": float(LAMBDA_INVENTORY),
            "lambda_receivable_acceleration_weight": float(LAMBDA_RECEIVABLE),
            "formula": "EVC = CM + 0.15*LiquidityDelta + 0.10*InventoryRelief + 0.08*ReceivableDelta - RiskCost",
        }

        return EconomicValueModel(
            contribution_margin_value=round_decimal(contribution_margin_value, 2),
            liquidity_improvement_value=round_decimal(liquidity_improvement_value, 2),
            inventory_relief_value=round_decimal(inventory_relief_value, 2),
            receivable_improvement_value=round_decimal(receivable_improvement_value, 2),
            economic_risk_cost=round_decimal(economic_risk_cost, 2),
            total_economic_value_created=total_evc,
            assumptions=assumptions,
        )

    @classmethod
    def evaluate_action(
        cls, db: Session, merchant_id: str, action: EconomicActionModel
    ) -> ActionEvaluationResponse:
        current_state = cls.calculate_current_state(db=db, merchant_id=merchant_id)

        proj_cash = current_state.cash_position
        proj_rec = current_state.total_receivables
        proj_inv = current_state.inventory_valuation
        proj_aging = current_state.aging_inventory_value
        cm_value = Decimal("0.00")
        liq_value = Decimal("0.00")
        inv_relief = Decimal("0.00")
        rec_relief = Decimal("0.00")
        risk_cost = Decimal("0.00")

        if action.action_type == "accelerate_payment":
            discount_pct = Decimal(str(action.parameters.get("discount_pct", 2.0)))
            invoice_val = Decimal(str(action.parameters.get("invoice_amount", 330000.00)))
            realized_cash = invoice_val * (Decimal("1.0") - (discount_pct / Decimal("100")))
            discount_cost = invoice_val - realized_cash

            proj_cash += realized_cash
            proj_rec -= invoice_val
            rec_relief += invoice_val
            liq_value += realized_cash
            risk_cost += discount_cost
            cm_value -= discount_cost

        elif action.action_type == "liquidate_inventory":
            discount_pct = Decimal(str(action.parameters.get("discount_pct", 10.0)))
            stock_cost = Decimal(str(action.parameters.get("inventory_cost", 288000.00)))
            markup = Decimal(str(action.parameters.get("standard_markup", 1.45)))
            retail_val = stock_cost * markup
            sale_rev = retail_val * (Decimal("1.0") - (discount_pct / Decimal("100")))

            cm_value += (sale_rev - stock_cost)
            proj_cash += sale_rev
            proj_inv -= stock_cost
            proj_aging -= stock_cost
            inv_relief += stock_cost
            liq_value += sale_rev

        elif action.action_type == "offer_discount":
            discount_pct = Decimal(str(action.parameters.get("discount_pct", 5.0)))
            gross_val = Decimal(str(action.parameters.get("gross_value", 183000.00)))
            cogs = Decimal(str(action.parameters.get("cogs", 126000.00)))
            net_rev = gross_val * (Decimal("1.0") - (discount_pct / Decimal("100")))

            cm_value += (net_rev - cogs)
            proj_cash += net_rev
            proj_inv -= cogs
            liq_value += net_rev

        else:
            cm_value += Decimal("25000.00")
            proj_cash += Decimal("50000.00")
            liq_value += Decimal("50000.00")

        evc = cls.calculate_economic_value(
            contribution_margin_value=cm_value,
            liquidity_improvement_value=liq_value,
            inventory_relief_value=inv_relief,
            receivable_improvement_value=rec_relief,
            economic_risk_cost=risk_cost,
        )

        score_reduction = int((liq_value + inv_relief + rec_relief) / Decimal("75000.00"))
        proj_score = max(0, min(100, current_state.pressure_score - score_reduction))
        score_delta = proj_score - current_state.pressure_score

        if proj_score <= EconomicModelConfig.SCORE_STRONG_MAX:
            proj_state = "Strong"
        elif proj_score <= EconomicModelConfig.SCORE_HEALTHY_MAX:
            proj_state = "Healthy"
        elif proj_score <= EconomicModelConfig.SCORE_WATCH_MAX:
            proj_state = "Watch"
        elif proj_score <= EconomicModelConfig.SCORE_STRESSED_MAX:
            proj_state = "Stressed"
        else:
            proj_state = "Critical"

        deltas = [
            MetricDelta(
                metric="cash",
                label="Available Cash",
                before=current_state.cash_position,
                after=proj_cash,
                absolute_change=proj_cash - current_state.cash_position,
                percentage_change=round_decimal(((proj_cash - current_state.cash_position) / current_state.cash_position) * Decimal("100"), 1) if current_state.cash_position > 0 else Decimal(0),
                direction="Positive" if proj_cash >= current_state.cash_position else "Negative",
                unit="INR",
                formatted_before=format_inr(current_state.cash_position),
                formatted_after=format_inr(proj_cash),
                formatted_change=f"+{format_inr(proj_cash - current_state.cash_position)}",
            ),
            MetricDelta(
                metric="pressure_score",
                label="Pressure Score",
                before=Decimal(current_state.pressure_score),
                after=Decimal(proj_score),
                absolute_change=Decimal(score_delta),
                percentage_change=round_decimal((Decimal(score_delta) / Decimal(current_state.pressure_score)) * Decimal("100"), 1) if current_state.pressure_score > 0 else Decimal(0),
                direction="Positive" if score_delta <= 0 else "Negative",
                unit="Points",
                formatted_before=f"{current_state.pressure_score}/100",
                formatted_after=f"{proj_score}/100",
                formatted_change=f"{score_delta} pts",
            ),
        ]

        is_favorable = evc.total_economic_value_created > 0 and score_delta <= 0

        summary = (
            f"Executing '{action.description}' generates {format_inr(evc.total_economic_value_created)} in total economic value, "
            f"improving available cash to {format_inr(proj_cash)} and relieving pressure from {current_state.pressure_score}/100 down to {proj_score}/100 ({proj_state})."
        )

        return ActionEvaluationResponse(
            action=action,
            is_favorable=is_favorable,
            current_pressure_score=current_state.pressure_score,
            projected_pressure_score=proj_score,
            pressure_score_delta=score_delta,
            current_state=current_state.state,
            projected_state=proj_state,
            economic_value_created=evc,
            deltas=deltas,
            recommendation_summary=summary,
        )
