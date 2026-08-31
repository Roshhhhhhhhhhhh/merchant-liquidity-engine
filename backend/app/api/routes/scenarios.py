from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.api.deps import get_current_merchant_id
from app.schemas.scenario import (
    ScenarioSimulateRequest,
    ScenarioSimulateResponse,
    ScenarioListResponse,
    BuyerRequestModel,
    MerchantConstraintsModel,
    DealCandidateModel,
    CompareDealsRequest,
    CompareDealsResponse,
)
from app.services.scenario_service import ScenarioService
from app.services.deal_generator import DealCandidateGenerator
from app.services.economic_state_service import EconomicStateService

router = APIRouter()


@router.post("/simulate", response_model=ScenarioSimulateResponse, summary="Run counterfactual deal simulation & optimize")
def simulate_scenario(
    payload: ScenarioSimulateRequest,
    merchant_id: str = Depends(get_current_merchant_id),
    db: Session = Depends(get_db),
):
    try:
        effective_merchant_id = payload.merchant_id or merchant_id
        return ScenarioService.simulate_scenario(
            db=db,
            merchant_id=effective_merchant_id,
            request=payload.request,
            constraints=payload.constraints,
            scenario_name=payload.scenario_name,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scenario simulation failed: {str(e)}")


@router.get("", response_model=ScenarioListResponse, summary="Get historical counterfactual simulation runs")
def get_scenarios(
    merchant_id: str = Depends(get_current_merchant_id),
    db: Session = Depends(get_db),
):
    try:
        return ScenarioService.get_scenarios(db=db, merchant_id=merchant_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve scenarios: {str(e)}")


@router.get("/{scenario_id}", response_model=ScenarioSimulateResponse, summary="Get detailed scenario simulation by ID")
def get_scenario_by_id(
    scenario_id: str,
    merchant_id: str = Depends(get_current_merchant_id),
    db: Session = Depends(get_db),
):
    try:
        return ScenarioService.get_scenario_by_id(db=db, scenario_id=scenario_id, merchant_id=merchant_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve scenario: {str(e)}")


@router.post("/deals/generate", summary="Algorithmically generate candidate deal options for an inquiry")
def generate_deal_options(
    payload: BuyerRequestModel,
    merchant_id: str = Depends(get_current_merchant_id),
    db: Session = Depends(get_db),
):
    try:
        current_state = EconomicStateService.calculate_current_state(db=db, merchant_id=merchant_id)
        effective_constraints = MerchantConstraintsModel()
        return DealCandidateGenerator.generate_candidates(
            db=db,
            merchant_id=merchant_id,
            current_state=current_state,
            request=payload,
            constraints=effective_constraints,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate deal candidates: {str(e)}")
