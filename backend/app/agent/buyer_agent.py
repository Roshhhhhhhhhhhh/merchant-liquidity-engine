from decimal import Decimal
from typing import Dict, Any, Tuple
from app.schemas.agent import BuyerRequest, BuyerConstraintModel
from app.agent.provider import LLMProvider, get_llm_provider
from app.services.formatters import format_inr


class AIBuyerAgent:
    """
    Simulates the purchasing counterparty with deterministic budget utility
    and constraint verification.
    """

    def __init__(self, request: BuyerRequest, provider: LLMProvider = None):
        self.request = request
        self.provider = provider or get_llm_provider()
        self.constraints = BuyerConstraintModel(
            budget_ceiling=request.maximum_budget,
            min_quantity=int(request.quantity * 0.90),  # At least 90% of requested qty
            max_delivery_days=request.maximum_delivery_days,
            preferred_payment_days=request.preferred_payment_days,
            negotiation_tolerance_pct=Decimal("5.0"),
        )

    def evaluate_offer(
        self,
        offer_data: Dict[str, Any],
        round_number: int,
        max_rounds: int = 5,
    ) -> Tuple[str, str, Dict[str, Any]]:
        """
        Evaluates a merchant proposal against buyer constraints.
        Returns (decision, message, counter_params).
        decision: 'ACCEPT' | 'COUNTER' | 'REJECT'
        """
        gross_value = Decimal(str(offer_data["gross_value"]))
        qty = offer_data["quantity"]
        delivery_days = offer_data["delivery_days"]
        payment_days = offer_data["payment_timing_days"]

        budget = self.constraints.budget_ceiling
        tolerance_ceiling = budget * (Decimal("1.0") + (self.constraints.negotiation_tolerance_pct / Decimal("100.0")))

        # Check conditions
        within_budget = gross_value <= budget
        within_tolerance = gross_value <= tolerance_ceiling
        sufficient_qty = qty >= self.constraints.min_quantity
        acceptable_delivery = delivery_days <= self.constraints.max_delivery_days

        # Decision Logic
        if within_budget and sufficient_qty and acceptable_delivery:
            decision = "ACCEPT"
            rationale = f"Gross value of {format_inr(gross_value)} is within our {format_inr(budget)} budget and delivery of {delivery_days}d meets our deadline."
            counter_params = {}
        elif within_tolerance and round_number < max_rounds:
            decision = "COUNTER"
            target_counter_budget = budget
            rationale = f"Offer of {format_inr(gross_value)} is slightly above our ₹{budget:,.0f} budget. We counter with our target budget of {format_inr(target_counter_budget)}."
            counter_params = {
                "target_budget": target_counter_budget,
                "requested_quantity": qty,
                "preferred_payment_days": payment_days,
                "max_delivery_days": delivery_days,
            }
        elif round_number >= max_rounds and within_tolerance:
            # Final round: Accept within tolerance
            decision = "ACCEPT"
            rationale = f"Final round accepted at {format_inr(gross_value)} as it falls within our acceptable upper variance limit."
            counter_params = {}
        else:
            decision = "REJECT"
            rationale = f"Offer of {format_inr(gross_value)} exceeds our strict maximum budgetary limit ({format_inr(budget)})."
            counter_params = {}

        message = self.provider.generate_buyer_response_message(decision, offer_data, rationale)
        return decision, message, counter_params
