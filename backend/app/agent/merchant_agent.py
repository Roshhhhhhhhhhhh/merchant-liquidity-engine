from decimal import Decimal
from typing import Dict, Any, List, Tuple, Optional
from sqlalchemy.orm import Session
from app.models import Product
from app.schemas.agent import BuyerRequest, AgentTraceModel
from app.schemas.scenario import MerchantConstraintsModel
from app.agent.tools import AgentTools
from app.agent.provider import LLMProvider, get_llm_provider
from app.services.formatters import format_inr, round_decimal


class MerchantAgent:
    """
    Orchestrates deterministic tools to negotiate commercial transactions
    that maximize the merchant's Economic Value Created (EVC).
    """

    def __init__(self, merchant_id: str, provider: Optional[LLMProvider] = None):
        self.merchant_id = merchant_id
        self.provider = provider or get_llm_provider()

    def process_buyer_request(
        self,
        db: Session,
        buyer_req: BuyerRequest,
        constraints: Optional[MerchantConstraintsModel] = None,
        round_number: int = 1,
    ) -> Tuple[Dict[str, Any], str, List[Dict[str, Any]]]:
        """
        Executes end-to-end tool-calling pipeline to generate the optimal merchant offer.
        Returns: (winning_offer_dict, natural_language_message, list_of_agent_traces)
        """
        traces = []

        # 1. Tool Call: get_merchant_state
        current_state = AgentTools.get_merchant_state(db=db, merchant_id=self.merchant_id)
        traces.append({
            "agent": "Merchant Agent",
            "action": "Retrieve Live Economic State",
            "tool_called": "get_merchant_state",
            "tool_input": {"merchant_id": self.merchant_id},
            "tool_output_summary": f"Cash: {current_state.cash.formatted_value}, Receivables: {current_state.receivables.formatted_value}, Pressure: {current_state.pressure_score}/100 ({current_state.state})",
            "decision": "Fetched baseline balance sheet dimensions to evaluate working capital impact.",
            "result": "SUCCESS",
        })

        # 2. Tool Call: get_merchant_constraints
        effective_constraints = constraints or AgentTools.get_merchant_constraints(self.merchant_id)

        # 3. Tool Call: generate_deal_candidates
        raw_candidates = AgentTools.generate_deal_candidates(
            db=db,
            merchant_id=self.merchant_id,
            buyer_req=buyer_req,
            constraints=effective_constraints,
        )
        traces.append({
            "agent": "Economic Engine",
            "action": "Generate Deal Candidates",
            "tool_called": "generate_deal_candidates",
            "tool_input": {"quantity": buyer_req.quantity, "target_budget": float(buyer_req.maximum_budget)},
            "tool_output_summary": f"Generated {len(raw_candidates)} strategic commercial structures (Standard 30d, Cash Accel 0d, Volume 7d, Aging Clearance 0d).",
            "decision": "Produced diverse commercial options spanning pricing, payment timing, and inventory relief.",
            "result": "SUCCESS",
        })

        # 4. Tool Call: simulate_deal for each candidate
        evaluated_candidates = []
        for cand in raw_candidates:
            sim = AgentTools.simulate_deal(
                db=db,
                merchant_id=self.merchant_id,
                product_id=cand["product_id"],
                quantity=cand["quantity"],
                unit_price=cand["unit_price"],
                payment_timing_days=cand["payment_timing_days"],
                delivery_days=cand["delivery_days"],
                target_aging_reduction_units=cand.get("target_aging_reduction_units", 0),
            )
            # Compute EVC via optimizer
            from app.services.deal_optimizer import DealOptimizationService
            evc, breakdown = DealOptimizationService.calculate_economic_value(sim)
            evaluated_candidates.append({
                **cand,
                **sim,
                "economic_value": evc,
                "economic_value_breakdown": breakdown,
            })

        # 5. Tool Call: compare_and_optimize_deals
        ranked_candidates, recommended, ranking_explanation = AgentTools.compare_and_optimize_deals(
            evaluated_candidates
        )
        traces.append({
            "agent": "Economic Optimizer",
            "action": "Rank Candidates by Economic Value Created ($EVC$)",
            "tool_called": "compare_and_optimize_deals",
            "tool_input": {"candidates_count": len(ranked_candidates)},
            "tool_output_summary": f"Top Candidate: {recommended.label} (EVC: {recommended.economic_value_formatted}, Pressure: {recommended.current_pressure_score} -> {recommended.projected_pressure_score})",
            "decision": f"Selected {recommended.label} as optimal commercial offer: {ranking_explanation}",
            "result": "SUCCESS",
        })

        # 6. Generate Natural Language Offer Message
        offer_payload = {
            "candidate_id": recommended.id,
            "product_id": recommended.product_id if hasattr(recommended, "product_id") else raw_candidates[0]["product_id"],
            "product_name": raw_candidates[0].get("product_name", "Industrial Control Valves"),
            "quantity": recommended.quantity,
            "unit_price": recommended.unit_price,
            "gross_value": recommended.gross_value,
            "gross_value_formatted": recommended.gross_value_formatted,
            "payment_timing_days": recommended.payment_timing_days,
            "delivery_days": recommended.delivery_days,
            "economic_value": recommended.economic_value,
            "economic_value_formatted": recommended.economic_value_formatted,
            "current_pressure_score": recommended.current_pressure_score,
            "projected_pressure_score": recommended.projected_pressure_score,
            "pressure_score_delta": recommended.pressure_score_delta,
            "strategy_tag": recommended.strategy_tag,
            "rationale": ranking_explanation,
        }

        merchant_message = self.provider.generate_merchant_offer_message(
            offer=offer_payload,
            merchant_state_summary=f"Pressure: {current_state.pressure_score}/100",
        )

        return offer_payload, merchant_message, traces

    def evaluate_buyer_counter(
        self,
        db: Session,
        counter_params: Dict[str, Any],
        current_offer: Dict[str, Any],
        constraints: Optional[MerchantConstraintsModel] = None,
        round_number: int = 2,
    ) -> Tuple[Optional[Dict[str, Any]], str, str, List[Dict[str, Any]]]:
        """
        Re-evaluates a buyer counteroffer against merchant policy and working capital.
        Returns: (updated_offer_dict, merchant_message, decision_status, traces)
        decision_status: 'COUNTER_OFFERED' | 'ACCEPTED' | 'REJECTED'
        """
        traces = []
        target_budget = Decimal(str(counter_params.get("target_budget", current_offer["gross_value"])))
        qty = int(counter_params.get("requested_quantity", current_offer["quantity"]))
        payment_days = int(counter_params.get("preferred_payment_days", current_offer["payment_timing_days"]))
        delivery_days = int(counter_params.get("max_delivery_days", current_offer["delivery_days"]))

        # Check unit price required to meet target budget
        proposed_unit_price = round_decimal(target_budget / Decimal(qty), 2)

        # 1. Fetch Product cost & verify margin floor
        target_prod_id = current_offer.get("product_id")
        product = db.query(Product).filter(Product.id == target_prod_id).first() if target_prod_id else None
        if not product:
            product = db.query(Product).filter(Product.merchant_id == self.merchant_id).first() or db.query(Product).first()

        unit_cost = Decimal(str(product.unit_cost)) if product else Decimal("850.00")
        product_name = product.name if product else "Industrial Supply Lot"
        effective_constraints = constraints or AgentTools.get_merchant_constraints(self.merchant_id)
        min_allowed_price = round_decimal(unit_cost * (Decimal("1.0") + (effective_constraints.min_margin_pct / Decimal("100.0"))), 2)

        # Log trace
        traces.append({
            "agent": "Merchant Agent",
            "action": "Parse Buyer Counteroffer",
            "tool_called": "evaluate_buyer_counter",
            "tool_input": {"target_budget": float(target_budget), "proposed_price": float(proposed_unit_price)},
            "tool_output_summary": f"Target: ₹{target_budget:,.2f} ({proposed_unit_price}/unit). Minimum margin floor price: ₹{min_allowed_price:,.2f}/unit.",
            "decision": "Verifying whether requested counter violates margin floor or cash velocity requirements.",
            "result": "SUCCESS",
        })

        if proposed_unit_price >= min_allowed_price:
            # Feasible! We can adjust price or compromise with immediate settlement
            sim = AgentTools.simulate_deal(
                db=db,
                merchant_id=self.merchant_id,
                product_id=current_offer.get("product_id", product.id),
                quantity=qty,
                unit_price=proposed_unit_price,
                payment_timing_days=payment_days,
                delivery_days=delivery_days,
            )
            from app.services.deal_optimizer import DealOptimizationService
            evc, breakdown = DealOptimizationService.calculate_economic_value(sim)

            updated_offer = {
                "candidate_id": "cand_counter_adjusted",
                "product_id": current_offer.get("product_id", product.id),
                "product_name": current_offer.get("product_name", product_name),
                "quantity": qty,
                "unit_price": proposed_unit_price,
                "gross_value": round_decimal(Decimal(qty) * proposed_unit_price, 2),
                "gross_value_formatted": format_inr(round_decimal(Decimal(qty) * proposed_unit_price, 2)),
                "payment_timing_days": payment_days,
                "delivery_days": delivery_days,
                "economic_value": evc,
                "economic_value_formatted": format_inr(evc),
                "current_pressure_score": sim["current_pressure_score"],
                "projected_pressure_score": sim["projected_pressure_score"],
                "pressure_score_delta": sim["pressure_score_delta"],
                "strategy_tag": "Compromise Counteroffer",
                "rationale": f"Adjusted price to ₹{proposed_unit_price}/unit to meet buyer budget while maintaining healthy {sim['margin_pct']}% contribution margin.",
            }

            traces.append({
                "agent": "Economic Engine",
                "action": "Simulate Counteroffer Impact",
                "tool_called": "simulate_deal",
                "tool_input": {"unit_price": float(proposed_unit_price), "quantity": qty},
                "tool_output_summary": f"Simulated Deal: EVC {updated_offer['economic_value_formatted']}, Pressure Score: {sim['projected_pressure_score']}/100 ({sim['pressure_score_delta']} pts)",
                "decision": "Counteroffer accepted and structured with validated margin.",
                "result": "SUCCESS",
            })

            message = self.provider.generate_merchant_counter_message(
                offer=updated_offer,
                rationale=f"We can meet your target budget of {updated_offer['gross_value_formatted']} for {qty} units with {payment_days}d settlement.",
            )
            return updated_offer, message, "COUNTER_OFFERED", traces
        else:
            # Below margin floor: Offer minimum feasible compromise price
            feasible_price = min_allowed_price
            feasible_gross = round_decimal(Decimal(qty) * feasible_price, 2)
            sim = AgentTools.simulate_deal(
                db=db,
                merchant_id=self.merchant_id,
                product_id=current_offer.get("product_id", product.id),
                quantity=qty,
                unit_price=feasible_price,
                payment_timing_days=0,  # Require immediate cash to offset lower price
                delivery_days=delivery_days,
            )
            from app.services.deal_optimizer import DealOptimizationService
            evc, breakdown = DealOptimizationService.calculate_economic_value(sim)

            updated_offer = {
                "candidate_id": "cand_counter_floor",
                "product_id": current_offer.get("product_id", product.id),
                "product_name": current_offer.get("product_name", product_name),
                "quantity": qty,
                "unit_price": feasible_price,
                "gross_value": feasible_gross,
                "gross_value_formatted": format_inr(feasible_gross),
                "payment_timing_days": 0,
                "delivery_days": delivery_days,
                "economic_value": evc,
                "economic_value_formatted": format_inr(evc),
                "current_pressure_score": sim["current_pressure_score"],
                "projected_pressure_score": sim["projected_pressure_score"],
                "pressure_score_delta": sim["pressure_score_delta"],
                "strategy_tag": "Margin Floor Compromise",
                "rationale": f"Proposed buyer target is below cost floor. Offered best feasible compromise at ₹{feasible_price}/unit with immediate UPI settlement.",
            }

            traces.append({
                "agent": "Merchant Agent",
                "action": "Enforce Margin Boundary Constraint",
                "tool_called": "get_merchant_constraints",
                "tool_input": {"min_margin_pct": float(effective_constraints.min_margin_pct)},
                "tool_output_summary": f"Buyer budget ₹{target_budget:,.2f} would breach margin floor. Adjusted to minimum viable price ₹{feasible_gross:,.2f}.",
                "decision": "Enforced strict economic policy boundary to preserve merchant solvency.",
                "result": "COUNTERED",
            })

            message = self.provider.generate_merchant_counter_message(
                offer=updated_offer,
                rationale=f"Your requested budget of ₹{target_budget:,.2f} is below our unit manufacturing cost floor. Our best viable counter is {updated_offer['gross_value_formatted']} (₹{feasible_price}/unit) with immediate settlement.",
            )
            return updated_offer, message, "COUNTER_OFFERED", traces
