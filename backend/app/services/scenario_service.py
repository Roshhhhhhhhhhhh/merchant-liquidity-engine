import json
import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.scenario import Scenario, ScenarioCandidate
from app.models.merchant import Merchant
from app.schemas.scenario import (
    BuyerRequestModel,
    MerchantConstraintsModel,
    DealCandidateModel,
    ScenarioSimulateResponse,
    ScenarioListItem,
    ScenarioListResponse,
    CompareDealsResponse,
)
from app.schemas.economic_state import MetricDelta
from app.services.economic_state_service import EconomicStateService
from app.services.counterfactual_service import CounterfactualStateService
from app.services.deal_generator import DealCandidateGenerator
from app.services.deal_optimizer import DealOptimizationService
from app.services.formatters import format_inr


class ScenarioService:
    """
    Orchestration service for running, persisting, and retrieving counterfactual scenarios.
    """

    @staticmethod
    def simulate_scenario(
        db: Session,
        merchant_id: str,
        request: BuyerRequestModel,
        constraints: Optional[MerchantConstraintsModel] = None,
        scenario_name: Optional[str] = None,
    ) -> ScenarioSimulateResponse:
        merchant = db.query(Merchant).filter(Merchant.id == merchant_id).first()
        if not merchant:
            raise ValueError(f"Merchant '{merchant_id}' not found")

        effective_constraints = constraints or MerchantConstraintsModel()
        name = scenario_name or f"Inquiry: {request.requested_quantity} units ({request.product_name or 'Standard Order'})"

        # 1. Fetch Current Economic Twin State
        current_state = EconomicStateService.calculate_current_state(db=db, merchant_id=merchant_id)

        # 2. Generate 4 Algorithmic Deal Candidates
        raw_candidates = DealCandidateGenerator.generate_candidates(
            db=db,
            merchant_id=merchant_id,
            current_state=current_state,
            request=request,
            constraints=effective_constraints,
        )

        # 3. Simulate Each Candidate via Pure Counterfactual Engine
        evaluated_candidates = []
        for cand in raw_candidates:
            sim_result = CounterfactualStateService.simulate_deal(
                db=db,
                merchant_id=merchant_id,
                current_state=current_state,
                product_id=cand["product_id"],
                quantity=cand["quantity"],
                unit_price=cand["unit_price"],
                payment_timing_days=cand["payment_timing_days"],
                delivery_days=cand["delivery_days"],
                target_aging_reduction_units=cand.get("target_aging_reduction_units", 0),
            )
            # Compute EVC
            evc, breakdown = DealOptimizationService.calculate_economic_value(sim_result)
            
            cand_payload = {
                **cand,
                **sim_result,
                "economic_value": evc,
                "economic_value_breakdown": breakdown,
            }
            evaluated_candidates.append(cand_payload)

        # 4. Rank and Generate Deterministic Explanation
        final_candidates, recommended, ranking_explanation = DealOptimizationService.optimize_and_rank_candidates(
            evaluated_candidates
        )

        # 5. Persist Scenario & Candidate Records in DB
        scenario_id = f"scen_{uuid.uuid4().hex[:12]}"
        scenario = Scenario(
            id=scenario_id,
            merchant_id=merchant_id,
            name=name,
            status="Simulated",
            request_data=request.model_dump_json(),
            recommended_candidate_id=recommended.id,
            explanation=ranking_explanation,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(scenario)

        for cand in final_candidates:
            cand_db = ScenarioCandidate(
                id=f"{scenario_id}_{cand.id}",
                scenario_id=scenario_id,
                label=cand.label,
                is_recommended=cand.is_recommended,
                rank=cand.rank,
                action_type=cand.action_type,
                action_data=json.dumps({"strategy_tag": cand.strategy_tag, "discount_pct": float(cand.discount_pct)}),
                quantity=cand.quantity,
                unit_price=cand.unit_price,
                gross_value=cand.gross_value,
                estimated_cogs=cand.estimated_cogs,
                contribution_margin=cand.contribution_margin,
                margin_pct=cand.margin_pct,
                payment_timing_days=cand.payment_timing_days,
                delivery_days=cand.delivery_days,
                cash_impact=cand.cash_impact,
                inventory_impact=cand.inventory_impact,
                aging_inventory_impact=cand.aging_inventory_impact,
                receivable_impact=cand.receivable_impact,
                capacity_impact_pct=cand.capacity_impact_pct,
                days_inventory_coverage=cand.days_inventory_coverage,
                stockout_risk=cand.stockout_risk,
                economic_value=cand.economic_value,
                economic_value_breakdown=cand.economic_value_breakdown.model_dump_json(),
                current_pressure_score=cand.current_pressure_score,
                projected_pressure_score=cand.projected_pressure_score,
                pressure_score_delta=cand.pressure_score_delta,
                projected_state=cand.projected_state,
                projected_state_data=json.dumps({"deltas": [d.model_dump(mode="json") for d in cand.deltas]}),
                explanation=cand.explanation,
                created_at=datetime.utcnow(),
            )
            db.add(cand_db)

        db.commit()

        return ScenarioSimulateResponse(
            scenario_id=scenario_id,
            merchant_id=merchant_id,
            scenario_name=name,
            request=request,
            current_state=current_state,
            candidates=final_candidates,
            recommended_candidate=recommended,
            ranking_explanation=ranking_explanation,
            created_at=scenario.created_at,
        )

    @staticmethod
    def get_scenarios(db: Session, merchant_id: str) -> ScenarioListResponse:
        scenarios = (
            db.query(Scenario)
            .filter(Scenario.merchant_id == merchant_id)
            .order_by(Scenario.created_at.desc())
            .all()
        )

        items = []
        for s in scenarios:
            req_data = json.loads(s.request_data) if s.request_data else {}
            # Find recommended candidate
            rec_cand = next((c for c in s.candidates if c.is_recommended), None) or (s.candidates[0] if s.candidates else None)
            
            target_budget = Decimal(str(req_data.get("target_budget", 0)))
            evc = Decimal(str(rec_cand.economic_value)) if rec_cand else Decimal("0.00")
            
            items.append(
                ScenarioListItem(
                    id=s.id,
                    merchant_id=s.merchant_id,
                    name=s.name,
                    status=s.status,
                    requested_quantity=req_data.get("requested_quantity", 0),
                    target_budget=target_budget,
                    target_budget_formatted=format_inr(target_budget),
                    recommended_deal_label=rec_cand.label if rec_cand else None,
                    recommended_deal_strategy=rec_cand.action_type if rec_cand else None,
                    economic_value=evc,
                    economic_value_formatted=format_inr(evc),
                    projected_pressure_score=rec_cand.projected_pressure_score if rec_cand else 0,
                    projected_state=rec_cand.projected_state if rec_cand else "Healthy",
                    created_at=s.created_at,
                )
            )

        return ScenarioListResponse(total_scenarios=len(items), scenarios=items)

    @staticmethod
    def get_scenario_by_id(db: Session, scenario_id: str, merchant_id: str) -> ScenarioSimulateResponse:
        scenario = (
            db.query(Scenario)
            .filter(Scenario.id == scenario_id, Scenario.merchant_id == merchant_id)
            .first()
        )
        if not scenario:
            raise ValueError(f"Scenario '{scenario_id}' not found")

        req_dict = json.loads(scenario.request_data)
        request = BuyerRequestModel(**req_dict)
        current_state = EconomicStateService.calculate_current_state(db=db, merchant_id=merchant_id)

        candidates: List[DealCandidateModel] = []
        for c in scenario.candidates:
            breakdown_dict = json.loads(c.economic_value_breakdown) if c.economic_value_breakdown else {}
            proj_dict = json.loads(c.projected_state_data) if c.projected_state_data else {}
            deltas = [MetricDelta(**d) for d in proj_dict.get("deltas", [])]

            candidates.append(
                DealCandidateModel(
                    id=c.id.split("_")[-1] if "_" in c.id else c.id,
                    label=c.label,
                    strategy_tag=c.action_type,
                    is_recommended=c.is_recommended,
                    rank=c.rank,
                    action_type=c.action_type,
                    quantity=c.quantity,
                    unit_price=Decimal(str(c.unit_price)),
                    gross_value=Decimal(str(c.gross_value)),
                    estimated_cogs=Decimal(str(c.estimated_cogs)),
                    contribution_margin=Decimal(str(c.contribution_margin)),
                    margin_pct=Decimal(str(c.margin_pct)),
                    discount_pct=Decimal("0.0"),
                    payment_timing_days=c.payment_timing_days,
                    delivery_days=c.delivery_days,
                    cash_impact=Decimal(str(c.cash_impact)),
                    inventory_impact=Decimal(str(c.inventory_impact)),
                    aging_inventory_impact=Decimal(str(c.aging_inventory_impact)),
                    receivable_impact=Decimal(str(c.receivable_impact)),
                    capacity_impact_pct=Decimal(str(c.capacity_impact_pct)),
                    days_inventory_coverage=Decimal(str(c.days_inventory_coverage)),
                    stockout_risk=c.stockout_risk,
                    economic_value=Decimal(str(c.economic_value)),
                    economic_value_breakdown=breakdown_dict,
                    current_pressure_score=c.current_pressure_score,
                    projected_pressure_score=c.projected_pressure_score,
                    pressure_score_delta=c.pressure_score_delta,
                    current_state=current_state.state,
                    projected_state=c.projected_state,
                    gross_value_formatted=format_inr(Decimal(str(c.gross_value))),
                    contribution_margin_formatted=format_inr(Decimal(str(c.contribution_margin))),
                    cash_impact_formatted=format_inr(Decimal(str(c.cash_impact))),
                    inventory_impact_formatted=format_inr(Decimal(str(c.inventory_impact))),
                    aging_inventory_impact_formatted=format_inr(Decimal(str(c.aging_inventory_impact))),
                    receivable_impact_formatted=format_inr(Decimal(str(c.receivable_impact))),
                    economic_value_formatted=format_inr(Decimal(str(c.economic_value))),
                    explanation=c.explanation,
                    deltas=deltas,
                )
            )

        recommended = next((c for c in candidates if c.is_recommended), candidates[0])

        return ScenarioSimulateResponse(
            scenario_id=scenario.id,
            merchant_id=scenario.merchant_id,
            scenario_name=scenario.name,
            request=request,
            current_state=current_state,
            candidates=candidates,
            recommended_candidate=recommended,
            ranking_explanation=scenario.explanation or "",
            created_at=scenario.created_at,
        )
