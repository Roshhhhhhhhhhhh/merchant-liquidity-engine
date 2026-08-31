from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.api.deps import get_current_merchant_id
from app.models.merchant import Merchant
from app.schemas.merchant import MerchantResponse
from app.schemas.economic_state import (
    EconomicStateModel,
    StateScoreModel,
    StateDriversResponse,
    StateHistoryResponse,
    StateDeltaResponse,
    ActionEvaluationRequest,
    ActionEvaluationResponse,
)
from app.services.economic_state_service import EconomicStateService

router = APIRouter()


@router.get("", response_model=MerchantResponse, summary="Get merchant profile")
def get_merchant(
    merchant_id: str = Depends(get_current_merchant_id),
    db: Session = Depends(get_db),
):
    merchant = db.query(Merchant).filter(Merchant.id == merchant_id).first()
    if not merchant:
        raise HTTPException(status_code=404, detail=f"Merchant '{merchant_id}' not found")
    return merchant


@router.get("/state", response_model=EconomicStateModel, summary="Get comprehensive merchant economic state & twin")
def get_merchant_state(
    merchant_id: str = Depends(get_current_merchant_id),
    db: Session = Depends(get_db),
):
    try:
        return EconomicStateService.calculate_current_state(db=db, merchant_id=merchant_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate economic state: {str(e)}")


@router.get("/state/score", response_model=StateScoreModel, summary="Get economic pressure score & component weights")
def get_merchant_state_score(
    merchant_id: str = Depends(get_current_merchant_id),
    db: Session = Depends(get_db),
):
    try:
        return EconomicStateService.get_state_score(db=db, merchant_id=merchant_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate state score: {str(e)}")


@router.get("/state/drivers", response_model=StateDriversResponse, summary="Get ranked deterministic pressure drivers")
def get_merchant_state_drivers(
    merchant_id: str = Depends(get_current_merchant_id),
    db: Session = Depends(get_db),
):
    try:
        return EconomicStateService.get_state_drivers(db=db, merchant_id=merchant_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate pressure drivers: {str(e)}")


@router.get("/state/history", response_model=StateHistoryResponse, summary="Get chronological state trajectory & timeline")
def get_merchant_state_history(
    merchant_id: str = Depends(get_current_merchant_id),
    db: Session = Depends(get_db),
):
    try:
        return EconomicStateService.get_state_history(db=db, merchant_id=merchant_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve state history: {str(e)}")


@router.get("/state/delta", response_model=StateDeltaResponse, summary="Get state transition comparison (Before vs After)")
def get_merchant_state_delta(
    days_ago: int = Query(30, ge=1, le=180, description="Observation baseline window in days"),
    merchant_id: str = Depends(get_current_merchant_id),
    db: Session = Depends(get_db),
):
    try:
        return EconomicStateService.get_state_delta(db=db, merchant_id=merchant_id, days_ago=days_ago)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate state delta: {str(e)}")


@router.post("/state/evaluate-action", response_model=ActionEvaluationResponse, summary="Deterministic economic action evaluation")
def evaluate_economic_action(
    payload: ActionEvaluationRequest,
    merchant_id: str = Depends(get_current_merchant_id),
    db: Session = Depends(get_db),
):
    try:
        effective_merchant_id = payload.merchant_id or merchant_id
        return EconomicStateService.evaluate_action(db=db, merchant_id=effective_merchant_id, action=payload.action)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to evaluate economic action: {str(e)}")
