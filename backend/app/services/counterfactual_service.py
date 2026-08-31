import json
from decimal import Decimal
import datetime
from typing import Dict, Any, Tuple, List, Optional
from sqlalchemy.orm import Session
from app.models import Product, InventoryItem, Merchant
from app.schemas.economic_state import EconomicStateModel, MetricDelta
from app.services.economic_state_service import EconomicStateService, EconomicModelConfig
from app.services.simulator_config import SimulatorConfig
from app.services.formatters import format_inr, round_decimal


class CounterfactualStateService:
    """
    Pure in-memory simulation engine for projecting merchant economic state transitions.
    Never mutates the underlying database ledgers.
    """

    @staticmethod
    def simulate_deal(
        db: Session,
        merchant_id: str,
        current_state: EconomicStateModel,
        product_id: str,
        quantity: int,
        unit_price: Decimal,
        payment_timing_days: int = 0,
        delivery_days: int = 5,
        target_aging_reduction_units: int = 0,
    ) -> Dict[str, Any]:
        """
        Simulates a specific commercial deal and returns all projected metrics,
        impact deltas, and the projected Economic Pressure Score.
        """
        if quantity <= 0:
            raise ValueError(f"Quantity must be strictly positive, got {quantity}")
        if unit_price < 0:
            raise ValueError(f"Unit price cannot be negative, got {unit_price}")

        # 1. Fetch Product and Inventory Item details
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            # Fallback to first product of merchant
            product = db.query(Product).filter(Product.merchant_id == merchant_id).first()
            if not product:
                product = db.query(Product).first()
                if not product:
                    raise ValueError(f"No products found for merchant {merchant_id}")

        inv_item = (
            db.query(InventoryItem)
            .filter(InventoryItem.product_id == product.id, InventoryItem.merchant_id == merchant_id)
            .first()
        )

        unit_cost = Decimal(str(product.unit_cost))
        catalog_price = Decimal(str(product.current_price))

        # 2. Financial Metrics
        gross_value = round_decimal(Decimal(quantity) * unit_price, 2)
        estimated_cogs = round_decimal(Decimal(quantity) * unit_cost, 2)
        contribution_margin = round_decimal(gross_value - estimated_cogs, 2)
        margin_pct = (
            round_decimal((contribution_margin / gross_value) * Decimal("100.0"), 2)
            if gross_value > 0
            else Decimal("0.0")
        )
        discount_pct = (
            round_decimal(((catalog_price - unit_price) / catalog_price) * Decimal("100.0"), 2)
            if catalog_price > unit_price and catalog_price > 0
            else Decimal("0.0")
        )

        # 3. Inventory & Aging Impact
        inventory_reduction = estimated_cogs
        is_item_aging = (
            inv_item.days_in_stock > EconomicModelConfig.AGING_INVENTORY_DAYS_THRESHOLD
            or inv_item.status in ("Aging", "Critical")
        ) if inv_item else False

        if target_aging_reduction_units > 0:
            aging_units = min(quantity, target_aging_reduction_units)
            aging_inventory_reduction = round_decimal(Decimal(aging_units) * unit_cost, 2)
        elif is_item_aging:
            aging_inventory_reduction = min(current_state.aging_inventory_value, inventory_reduction)
        else:
            aging_inventory_reduction = Decimal("0.00")

        # 4. Cash vs Receivables Impact
        if payment_timing_days == 0:
            cash_impact = gross_value
            receivable_impact = Decimal("0.00")
        else:
            cash_impact = Decimal("0.00")
            receivable_impact = gross_value

        # 5. Capacity Impact Calculation (Normalized % load)
        max_daily_capacity = 25
        total_capacity_available = max_daily_capacity * max(1, delivery_days)
        capacity_load_pct = round_decimal(
            (Decimal(quantity) / Decimal(total_capacity_available)) * Decimal("100.0"), 1
        )

        # 6. Days of Inventory Coverage
        available_units_before = inv_item.available_quantity if inv_item else 100
        available_units_after = max(0, available_units_before - quantity)
        daily_demand = Decimal("4.0")
        days_inventory_coverage = round_decimal(Decimal(available_units_after) / daily_demand, 1)
        
        if days_inventory_coverage >= SimulatorConfig.MIN_COVERAGE_DAYS_HEALTHY:
            stockout_risk = "Low"
        elif days_inventory_coverage >= SimulatorConfig.MIN_COVERAGE_DAYS_WATCH:
            stockout_risk = "Moderate"
        elif days_inventory_coverage >= SimulatorConfig.MIN_COVERAGE_DAYS_CONSTRAINED:
            stockout_risk = "Constrained"
        else:
            stockout_risk = "Critical"

        # 7. Projected State Variables
        projected_cash = current_state.cash_position + cash_impact
        projected_inventory = max(Decimal("0.00"), current_state.inventory_valuation - inventory_reduction)
        projected_aging_inventory = max(Decimal("0.00"), current_state.aging_inventory_value - aging_inventory_reduction)
        projected_receivables = current_state.total_receivables + receivable_impact
        projected_overdue_receivables = current_state.overdue_receivables
        projected_payables = current_state.total_payables
        projected_near_term_payables = current_state.near_term_payables
        projected_capacity = min(Decimal("100.0"), current_state.fulfillment_capacity_pct + (capacity_load_pct * Decimal("0.25")))

        # 8. Projected Runway Calculation
        baseline_fixed_daily_outflow = Decimal("12500.00")
        near_term_daily_payables = projected_near_term_payables / Decimal(str(EconomicModelConfig.NEAR_TERM_PAYABLES_DAYS)) if projected_near_term_payables > 0 else Decimal("0.00")
        expected_daily_outflow = baseline_fixed_daily_outflow + near_term_daily_payables
        expected_daily_inflow = (
            (current_state.receivables.value * current_state.payment_velocity) / Decimal("14")
            if current_state.receivables.value > 0
            else Decimal("0.00")
        )
        projected_net_burn = expected_daily_outflow - expected_daily_inflow

        if projected_net_burn > 0:
            raw_runway = int(projected_cash / projected_net_burn)
            projected_runway_days = max(1, raw_runway)
        else:
            projected_runway_days = 90

        # 9. Projected Pressure Score
        # Component 1: Liquidity Runway
        if projected_runway_days <= 10:
            s_liq = Decimal("100.0")
        elif projected_runway_days <= 20:
            s_liq = Decimal("85.0") + (Decimal(20 - projected_runway_days) * Decimal("1.5"))
        elif projected_runway_days <= 30:
            s_liq = Decimal("60.0") + (Decimal(30 - projected_runway_days) * Decimal("2.5"))
        elif projected_runway_days <= 45:
            s_liq = Decimal("30.0") + (Decimal(45 - projected_runway_days) * Decimal("2.0"))
        elif projected_runway_days < 60:
            s_liq = Decimal(60 - projected_runway_days) * Decimal("2.0")
        else:
            s_liq = Decimal("0.0")

        # Component 2: Overdue & Credit Delay Receivables
        base_overdue_pct = (
            (projected_overdue_receivables / current_state.total_receivables) * Decimal("100")
            if current_state.total_receivables > 0
            else Decimal("0.0")
        )
        credit_delay_penalty = (
            (Decimal(str(payment_timing_days)) / Decimal("30.0")) * Decimal("15.0")
            if payment_timing_days > 0
            else Decimal("0.0")
        )
        s_rec = min(Decimal("100.0"), (base_overdue_pct * Decimal("2.4")) + credit_delay_penalty)

        # Component 3: Aging Inventory
        aging_pct = (
            (projected_aging_inventory / projected_inventory) * Decimal("100")
            if projected_inventory > 0
            else Decimal("0.0")
        )
        s_inv = min(Decimal("100.0"), aging_pct * Decimal("2.5"))

        # Component 4: Near-Term Payables Coverage
        near_term_cov_ratio = (
            projected_cash / projected_near_term_payables
            if projected_near_term_payables > 0
            else Decimal("10.0")
        )
        if near_term_cov_ratio < Decimal("0.8"):
            s_pay = Decimal("100.0")
        elif near_term_cov_ratio < Decimal("1.2"):
            s_pay = Decimal("75.0")
        elif near_term_cov_ratio < Decimal("2.0"):
            s_pay = Decimal("40.0")
        else:
            s_pay = Decimal("0.0")

        # Component 5: Demand Softening
        s_dem = max(Decimal("0.0"), Decimal("20.0") - current_state.recent_demand_trend_pct * Decimal("2.0"))

        # Component 6: Margin Compression
        s_mar = (
            Decimal("0.0") if margin_pct >= Decimal("25.0")
            else Decimal("35.0") if margin_pct >= Decimal("18.0")
            else Decimal("75.0")
        )

        # Composite Pressure Score
        projected_pressure_raw = (
            s_liq * EconomicModelConfig.WEIGHT_LIQUIDITY_RUNWAY
            + s_rec * EconomicModelConfig.WEIGHT_OVERDUE_RECEIVABLES
            + s_inv * EconomicModelConfig.WEIGHT_AGING_INVENTORY
            + s_pay * EconomicModelConfig.WEIGHT_NEAR_TERM_PAYABLES
            + s_dem * EconomicModelConfig.WEIGHT_DEMAND_TREND
            + s_mar * EconomicModelConfig.WEIGHT_MARGIN_COMPRESSION
        )
        projected_pressure_score = max(0, min(100, int(round_decimal(projected_pressure_raw, 0))))

        # 10. Classify Projected Business State
        if projected_pressure_score <= EconomicModelConfig.SCORE_STRONG_MAX:
            projected_state = "Strong"
        elif projected_pressure_score <= EconomicModelConfig.SCORE_HEALTHY_MAX:
            projected_state = "Healthy"
        elif projected_pressure_score <= EconomicModelConfig.SCORE_WATCH_MAX:
            projected_state = "Watch"
        elif projected_pressure_score <= EconomicModelConfig.SCORE_STRESSED_MAX:
            projected_state = "Stressed"
        else:
            projected_state = "Critical"

        # 11. Metric Deltas
        deltas = [
            MetricDelta(
                metric="cash",
                label="Cash Available",
                before=float(current_state.cash_position),
                after=float(projected_cash),
                absolute_change=float(cash_impact),
                percentage_change=float(round_decimal((cash_impact / current_state.cash_position) * Decimal("100"), 1)) if current_state.cash_position > 0 else 0.0,
                direction="Positive" if cash_impact > 0 else "Neutral",
                unit="INR",
                formatted_before=current_state.cash.formatted_value,
                formatted_after=format_inr(projected_cash),
                formatted_change=f"+{format_inr(cash_impact)}" if cash_impact > 0 else "₹0",
            ),
            MetricDelta(
                metric="inventory",
                label="Inventory Value",
                before=float(current_state.inventory_valuation),
                after=float(projected_inventory),
                absolute_change=float(-inventory_reduction),
                percentage_change=float(round_decimal((-inventory_reduction / current_state.inventory_valuation) * Decimal("100"), 1)) if current_state.inventory_valuation > 0 else 0.0,
                direction="Neutral",
                unit="INR",
                formatted_before=current_state.inventory_value.formatted_value,
                formatted_after=format_inr(projected_inventory),
                formatted_change=f"-{format_inr(inventory_reduction)}",
            ),
            MetricDelta(
                metric="aging_inventory",
                label="Aging Inventory",
                before=float(current_state.aging_inventory_value),
                after=float(projected_aging_inventory),
                absolute_change=float(-aging_inventory_reduction),
                percentage_change=float(round_decimal((-aging_inventory_reduction / current_state.aging_inventory_value) * Decimal("100"), 1)) if current_state.aging_inventory_value > 0 else 0.0,
                direction="Positive" if aging_inventory_reduction > 0 else "Neutral",
                unit="INR",
                formatted_before=current_state.aging_inventory.formatted_value,
                formatted_after=format_inr(projected_aging_inventory),
                formatted_change=f"-{format_inr(aging_inventory_reduction)}" if aging_inventory_reduction > 0 else "₹0",
            ),
            MetricDelta(
                metric="receivables",
                label="Receivables Book",
                before=float(current_state.total_receivables),
                after=float(projected_receivables),
                absolute_change=float(receivable_impact),
                percentage_change=float(round_decimal((receivable_impact / current_state.total_receivables) * Decimal("100"), 1)) if current_state.total_receivables > 0 else 0.0,
                direction="Negative" if receivable_impact > 0 else "Neutral",
                unit="INR",
                formatted_before=current_state.receivables.formatted_value,
                formatted_after=format_inr(projected_receivables),
                formatted_change=f"+{format_inr(receivable_impact)}" if receivable_impact > 0 else "₹0",
            ),
            MetricDelta(
                metric="pressure_score",
                label="Pressure Score",
                before=float(current_state.pressure_score),
                after=float(projected_pressure_score),
                absolute_change=float(projected_pressure_score - current_state.pressure_score),
                percentage_change=float(projected_pressure_score - current_state.pressure_score),
                direction="Positive" if projected_pressure_score < current_state.pressure_score else "Negative" if projected_pressure_score > current_state.pressure_score else "Neutral",
                unit="Score",
                formatted_before=f"{current_state.pressure_score}/100",
                formatted_after=f"{projected_pressure_score}/100",
                formatted_change=f"{projected_pressure_score - current_state.pressure_score} pts",
            ),
        ]

        return {
            "product_id": product.id,
            "product_name": product.name,
            "quantity": quantity,
            "unit_price": unit_price,
            "unit_cost": unit_cost,
            "catalog_price": catalog_price,
            "gross_value": gross_value,
            "estimated_cogs": estimated_cogs,
            "contribution_margin": contribution_margin,
            "margin_pct": margin_pct,
            "discount_pct": discount_pct,
            "payment_timing_days": payment_timing_days,
            "delivery_days": delivery_days,
            "cash_impact": cash_impact,
            "inventory_impact": inventory_reduction,
            "aging_inventory_impact": aging_inventory_reduction,
            "receivable_impact": receivable_impact,
            "capacity_impact_pct": capacity_load_pct,
            "days_inventory_coverage": days_inventory_coverage,
            "stockout_risk": stockout_risk,
            "projected_cash": projected_cash,
            "projected_inventory": projected_inventory,
            "projected_aging_inventory": projected_aging_inventory,
            "projected_receivables": projected_receivables,
            "projected_capacity": projected_capacity,
            "projected_runway_days": projected_runway_days,
            "current_pressure_score": current_state.pressure_score,
            "projected_pressure_score": projected_pressure_score,
            "pressure_score_delta": projected_pressure_score - current_state.pressure_score,
            "current_state": current_state.state,
            "projected_state": projected_state,
            "deltas": deltas,
        }
