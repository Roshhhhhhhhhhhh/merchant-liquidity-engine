from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.api.deps import get_current_merchant_id
from app.schemas.agent import (
    BuyerRequest,
    ParseBuyerRequestInput,
    StartNegotiationRequest,
    NegotiationSessionResponse,
    NegotiationListResponse,
    BuyerCounterRequest,
    DemoNegotiationRequest,
)
from app.agent.provider import get_llm_provider
from app.agent.negotiation_service import NegotiationService

router = APIRouter()


@router.post("/buyer/request", response_model=BuyerRequest, summary="Parse natural language purchase inquiry into structured BuyerRequest")
def parse_buyer_request(payload: ParseBuyerRequestInput):
    try:
        provider = get_llm_provider()
        req, _ = provider.extract_buyer_request(payload.message, payload.buyer_id or "buyer_enterprise_procure")
        return req
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse buyer request: {str(e)}")


@router.post("/negotiations", response_model=NegotiationSessionResponse, summary="Start B2B agent negotiation session with initial offer")
def start_negotiation(
    payload: StartNegotiationRequest,
    merchant_id: str = Depends(get_current_merchant_id),
    db: Session = Depends(get_db),
):
    try:
        effective_merchant_id = payload.merchant_id or merchant_id
        return NegotiationService.start_negotiation(
            db=db,
            merchant_id=effective_merchant_id,
            buyer_request=payload.buyer_request,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start negotiation: {str(e)}")


@router.get("/negotiations", response_model=NegotiationListResponse, summary="Get list of all negotiation sessions")
def get_negotiations(
    merchant_id: str = Depends(get_current_merchant_id),
    db: Session = Depends(get_db),
):
    try:
        return NegotiationService.get_negotiations(db=db, merchant_id=merchant_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve negotiations: {str(e)}")


@router.get("/negotiations/{session_id}", response_model=NegotiationSessionResponse, summary="Get full timeline, offers, and traces for negotiation session")
def get_negotiation_by_id(
    session_id: str,
    merchant_id: str = Depends(get_current_merchant_id),
    db: Session = Depends(get_db),
):
    try:
        return NegotiationService.get_negotiation_by_id(db=db, session_id=session_id, merchant_id=merchant_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve negotiation session: {str(e)}")


@router.post("/negotiations/{session_id}/message", response_model=NegotiationSessionResponse, summary="Send buyer counteroffer or advance negotiation round")
def send_counter_message(
    session_id: str,
    payload: BuyerCounterRequest,
    db: Session = Depends(get_db),
):
    try:
        return NegotiationService.send_buyer_counter(
            db=db,
            session_id=session_id,
            payload=payload,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process counter message: {str(e)}")


@router.post("/negotiations/{session_id}/accept", response_model=NegotiationSessionResponse, summary="Accept current offer and finalize agreement")
def accept_negotiation(
    session_id: str,
    db: Session = Depends(get_db),
):
    try:
        return NegotiationService.accept_offer(db=db, session_id=session_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to accept offer: {str(e)}")


@router.post("/negotiations/{session_id}/reject", response_model=NegotiationSessionResponse, summary="Reject offer and terminate negotiation")
def reject_negotiation(
    session_id: str,
    db: Session = Depends(get_db),
):
    try:
        return NegotiationService.reject_offer(db=db, session_id=session_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reject offer: {str(e)}")


@router.post("/negotiations/demo", response_model=NegotiationSessionResponse, summary="Run automated end-to-end B2B negotiation demo scenario")
def run_negotiation_demo(
    payload: Optional[DemoNegotiationRequest] = None,
    merchant_id: str = Depends(get_current_merchant_id),
    db: Session = Depends(get_db),
):
    try:
        effective_merchant_id = (payload.merchant_id if payload and payload.merchant_id else None) or merchant_id
        return NegotiationService.run_demo_scenario(db=db, merchant_id=effective_merchant_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to run demo scenario: {str(e)}")
