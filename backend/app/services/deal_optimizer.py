from decimal import Decimal
from typing import List, Dict, Any, Tuple
from app.schemas.scenario import DealCandidateModel, EconomicValueBreakdownModel
from app.services.simulator_config import SimulatorConfig
from app.services.formatters import format_inr, round_decimal


class DealOptimizationService:
    """
    Computes Economic Value Created (EVC), normalizes component impacts,
    ranks candidate commercial deals, and generates deterministic decision rationales.
    """

    @staticmethod
    def calculate_economic_value(sim_result: Dict[str, Any]) -> Tuple[Decimal, EconomicValueBreakdownModel]:
        cm = sim_result["contribution_margin"]
        cash_impact = sim_result["cash_impact"]
        aging_impact = sim_result["aging_inventory_impact"]
        receivable_impact = sim_result["receivable_impact"]
        timing_days = sim_result["payment_timing_days"]
        capacity_load = sim_result["capacity_impact_pct"]
        coverage_days = sim_result["days_inventory_coverage"]

        # 1. Liquidity Value (cash multiplied by timing utility)
        timing_mult = SimulatorConfig.TIMING_MULTIPLIERS.get(timing_days, Decimal("0.30"))
        # If immediate cash, full utility; if deferred, discounted utility
        if timing_days == 0:
            liquidity_val = round_decimal(cash_impact * timing_mult, 2)
        else:
            # Accelerated terms (7d) provide partial liquidity benefit
            liquidity_val = round_decimal(receivable_impact * timing_mult * Decimal("0.5"), 2)

        # 2. Inventory Relief (Aging inventory unlocked has high capital velocity premium)
        inventory_relief_val = round_decimal(
            aging_impact * (Decimal("1.0") + SimulatorConfig.AGING_CLEARANCE_PREMIUM_RATE), 2
        )

        # 3. Receivable Acceleration Benefit
        if timing_days == 0:
            receivable_benefit_val = round_decimal(cm * Decimal("0.25"), 2)
        elif timing_days <= 7:
            receivable_benefit_val = round_decimal(cm * Decimal("0.10"), 2)
        else:
            receivable_benefit_val = Decimal("0.00")

        # 4. Risk Cost (Credit terms create delay and collection friction)
        if timing_days >= 30:
            risk_cost = round_decimal(receivable_impact * Decimal("0.05"), 2)
        elif timing_days >= 15:
            risk_cost = round_decimal(receivable_impact * Decimal("0.02"), 2)
        else:
            risk_cost = Decimal("0.00")

        # 5. Capacity Overload Cost
        if capacity_load > SimulatorConfig.OPTIMAL_CAPACITY_MAX_PCT:
            excess_load = capacity_load - SimulatorConfig.OPTIMAL_CAPACITY_MAX_PCT
            capacity_cost = round_decimal(excess_load * SimulatorConfig.CAPACITY_OVERLOAD_PENALTY_RATE, 2)
        else:
            capacity_cost = Decimal("0.00")

        # 6. Stockout Opportunity Cost
        if coverage_days < SimulatorConfig.MIN_COVERAGE_DAYS_CONSTRAINED:
            stockout_cost = round_decimal(cm * Decimal("0.25"), 2)
        elif coverage_days < SimulatorConfig.MIN_COVERAGE_DAYS_WATCH:
            stockout_cost = round_decimal(cm * Decimal("0.10"), 2)
        else:
            stockout_cost = Decimal("0.00")

        # 7. Composite EVC Prototype Formula
        evc = (
            (SimulatorConfig.WEIGHT_CONTRIBUTION * cm)
            + (SimulatorConfig.WEIGHT_LIQUIDITY * liquidity_val)
            + (SimulatorConfig.WEIGHT_INVENTORY_RELIEF * inventory_relief_val)
            + (SimulatorConfig.WEIGHT_RECEIVABLE_BENEFIT * receivable_benefit_val)
            - (SimulatorConfig.WEIGHT_RISK_COST * risk_cost)
            - (SimulatorConfig.WEIGHT_CAPACITY_COST * capacity_cost)
            - (SimulatorConfig.WEIGHT_STOCKOUT_COST * stockout_cost)
        )
        total_evc = round_decimal(evc, 2)

        breakdown = EconomicValueBreakdownModel(
            contribution_margin_value=cm,
            liquidity_improvement_value=liquidity_val,
            inventory_relief_value=inventory_relief_val,
            receivable_improvement_value=receivable_benefit_val,
            economic_risk_cost=risk_cost,
            capacity_cost=capacity_cost,
            stockout_opportunity_cost=stockout_cost,
            total_economic_value_created=total_evc,
            weights_used={
                "w_contribution": float(SimulatorConfig.WEIGHT_CONTRIBUTION),
                "w_liquidity": float(SimulatorConfig.WEIGHT_LIQUIDITY),
                "w_inventory_relief": float(SimulatorConfig.WEIGHT_INVENTORY_RELIEF),
                "w_receivable_benefit": float(SimulatorConfig.WEIGHT_RECEIVABLE_BENEFIT),
                "w_risk_cost": float(SimulatorConfig.WEIGHT_RISK_COST),
                "w_capacity_cost": float(SimulatorConfig.WEIGHT_CAPACITY_COST),
                "w_stockout_cost": float(SimulatorConfig.WEIGHT_STOCKOUT_COST),
            },
        )

        return total_evc, breakdown

    @staticmethod
    def generate_candidate_explanation(cand_data: Dict[str, Any], rank: int) -> str:
        label = cand_data["label"]
        gross_fmt = format_inr(cand_data["gross_value"])
        cash_impact = cand_data["cash_impact"]
        aging_impact = cand_data["aging_inventory_impact"]
        timing = cand_data["payment_timing_days"]
        delta_p = cand_data["pressure_score_delta"]
        evc_fmt = format_inr(cand_data["economic_value"])

        reasons = []
        if cash_impact > 0:
            reasons.append(f"generates {format_inr(cash_impact)} in immediate liquid cash inflows")
        elif timing > 0:
            reasons.append(f"requires {timing}-day trade credit terms")

        if aging_impact > 0:
            reasons.append(f"liquidates {format_inr(aging_impact)} of slow-moving aging stock")

        if delta_p < 0:
            reasons.append(f"reduces merchant economic pressure by {abs(delta_p)} points")
        elif delta_p > 0:
            reasons.append(f"increases economic pressure by {delta_p} points")

        reasons_text = ", ".join(reasons) if reasons else "maintains balanced working capital"

        if rank == 1:
            return f"Rank #1 Preferred: Generates highest net economic value ({evc_fmt}) because it {reasons_text}."
        else:
            return f"Rank #{rank} Alternative: Gross volume of {gross_fmt} ({evc_fmt} net economic value), but {reasons_text}."

    @staticmethod
    def optimize_and_rank_candidates(
        evaluated_candidates: List[Dict[str, Any]]
    ) -> Tuple[List[DealCandidateModel], DealCandidateModel, str]:
        # Sort candidates strictly in descending order of Economic Value Created
        sorted_raw = sorted(evaluated_candidates, key=lambda c: c["economic_value"], reverse=True)

        final_candidates: List[DealCandidateModel] = []
        for idx, item in enumerate(sorted_raw):
            rank = idx + 1
            is_rec = (rank == 1)
            explanation = DealOptimizationService.generate_candidate_explanation(item, rank)

            model = DealCandidateModel(
                id=item["id"],
                label=item["label"],
                strategy_tag=item.get("strategy_tag", "Standard"),
                is_recommended=is_rec,
                rank=rank,
                action_type=item["action_type"],
                quantity=item["quantity"],
                unit_price=item["unit_price"],
                gross_value=item["gross_value"],
                estimated_cogs=item["estimated_cogs"],
                contribution_margin=item["contribution_margin"],
                margin_pct=item["margin_pct"],
                discount_pct=item.get("discount_pct", Decimal("0.0")),
                payment_timing_days=item["payment_timing_days"],
                delivery_days=item["delivery_days"],
                cash_impact=item["cash_impact"],
                inventory_impact=item["inventory_impact"],
                aging_inventory_impact=item["aging_inventory_impact"],
                receivable_impact=item["receivable_impact"],
                capacity_impact_pct=item["capacity_impact_pct"],
                days_inventory_coverage=item["days_inventory_coverage"],
                stockout_risk=item["stockout_risk"],
                economic_value=item["economic_value"],
                economic_value_breakdown=item["economic_value_breakdown"],
                current_pressure_score=item["current_pressure_score"],
                projected_pressure_score=item["projected_pressure_score"],
                pressure_score_delta=item["pressure_score_delta"],
                current_state=item["current_state"],
                projected_state=item["projected_state"],
                gross_value_formatted=format_inr(item["gross_value"]),
                contribution_margin_formatted=format_inr(item["contribution_margin"]),
                cash_impact_formatted=format_inr(item["cash_impact"]),
                inventory_impact_formatted=format_inr(item["inventory_impact"]),
                aging_inventory_impact_formatted=format_inr(item["aging_inventory_impact"]),
                receivable_impact_formatted=format_inr(item["receivable_impact"]),
                economic_value_formatted=format_inr(item["economic_value"]),
                explanation=explanation,
                deltas=item.get("deltas", []),
            )
            final_candidates.append(model)

        recommended = final_candidates[0]
        second = final_candidates[1] if len(final_candidates) > 1 else None

        # Build overall ranking summary
        evc_diff = (
            format_inr(recommended.economic_value - second.economic_value)
            if second
            else "₹0"
        )
        ranking_explanation = (
            f"{recommended.label} emerges as the optimal commercial choice creating {recommended.economic_value_formatted} in net economic value "
            f"(+{evc_diff} higher than closest alternative). "
            f"It delivers {recommended.cash_impact_formatted} in liquid funds while reducing projected pressure score from {recommended.current_pressure_score} to {recommended.projected_pressure_score}."
        )

        return final_candidates, recommended, ranking_explanation
