import json
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.negotiation import (
    NegotiationSession,
    NegotiationMessage,
    NegotiationOffer,
    AgentTrace,
)
from app.schemas.agent import (
    BuyerRequest,
    NegotiationOfferModel,
    NegotiationMessageModel,
    AgentTraceModel,
    NegotiationSessionResponse,
    NegotiationListItem,
    NegotiationListResponse,
    BuyerCounterRequest,
)
from app.agent.buyer_agent import AIBuyerAgent
from app.agent.merchant_agent import MerchantAgent
from app.agent.provider import get_llm_provider
from app.services.formatters import format_inr


class NegotiationService:
    """
    State machine coordinator and persistence manager for B2B agentic negotiations.
    """

    @staticmethod
    def _map_session_response(session: NegotiationSession, buyer_req: BuyerRequest) -> NegotiationSessionResponse:
        current_offer_model = None
        offers_models = []
        for o in session.offers:
            m = NegotiationOfferModel(
                id=o.id,
                session_id=o.session_id,
                candidate_id=o.candidate_id,
                round_number=o.round_number,
                product_id=o.product_id,
                product_name=o.product_name,
                quantity=o.quantity,
                unit_price=Decimal(str(o.unit_price)),
                gross_value=Decimal(str(o.gross_value)),
                gross_value_formatted=format_inr(Decimal(str(o.gross_value))),
                payment_timing_days=o.payment_timing_days,
                delivery_days=o.delivery_days,
                economic_value=Decimal(str(o.economic_value)),
                economic_value_formatted=format_inr(Decimal(str(o.economic_value))),
                current_pressure_score=o.current_pressure_score,
                projected_pressure_score=o.projected_pressure_score,
                pressure_score_delta=o.pressure_score_delta,
                status=o.status,
                strategy_tag=o.strategy_tag,
                rationale=o.rationale,
                created_at=o.created_at,
            )
            offers_models.append(m)
            if session.current_offer_id == o.id or (not current_offer_model and o.status in ("OFFERED", "ACCEPTED")):
                current_offer_model = m

        messages_models = [
            NegotiationMessageModel(
                id=msg.id,
                session_id=msg.session_id,
                sender=msg.sender,
                message_type=msg.message_type,
                round_number=msg.round_number,
                raw_message=msg.raw_message,
                structured_data=json.loads(msg.structured_data) if msg.structured_data else None,
                created_at=msg.created_at,
            )
            for msg in session.messages
        ]

        traces_models = [
            AgentTraceModel(
                id=t.id,
                session_id=t.session_id,
                round_number=t.round_number,
                timestamp=t.timestamp,
                agent=t.agent,
                action=t.action,
                tool_called=t.tool_called,
                tool_input=json.loads(t.tool_input) if t.tool_input else None,
                tool_output_summary=t.tool_output_summary,
                decision=t.decision,
                result=t.result,
            )
            for t in session.traces
        ]

        final_agreement = json.loads(session.final_agreement_data) if session.final_agreement_data else None

        return NegotiationSessionResponse(
            id=session.id,
            merchant_id=session.merchant_id,
            buyer_id=session.buyer_id,
            status=session.status,
            round_number=session.round_number,
            max_rounds=session.max_rounds,
            buyer_request=buyer_req,
            current_offer=current_offer_model or (offers_models[-1] if offers_models else None),
            messages=messages_models,
            offers=offers_models,
            traces=traces_models,
            agent_mode="fallback",
            final_agreement=final_agreement,
            created_at=session.created_at,
            updated_at=session.updated_at,
        )

    @staticmethod
    def start_negotiation(
        db: Session,
        merchant_id: str,
        buyer_request: BuyerRequest,
    ) -> NegotiationSessionResponse:
        session_id = f"neg_{uuid.uuid4().hex[:10]}"
        now = datetime.utcnow()

        session = NegotiationSession(
            id=session_id,
            merchant_id=merchant_id,
            buyer_id=buyer_request.buyer_id,
            status="ANALYZING",
            buyer_request_data=buyer_request.model_dump_json(),
            round_number=1,
            max_rounds=5,
            created_at=now,
            updated_at=now,
        )
        db.add(session)

        # 1. Record Buyer Initial Request Message
        req_msg_text = (
            buyer_request.raw_inquiry_text
            or f"Looking to purchase {buyer_request.quantity} units of {buyer_request.product_name or 'industrial supply lot'} with budget ceiling of {format_inr(buyer_request.maximum_budget)} and {buyer_request.maximum_delivery_days}-day delivery."
        )
        buyer_msg = NegotiationMessage(
            id=f"msg_{uuid.uuid4().hex[:8]}",
            session_id=session_id,
            sender="buyer",
            message_type="request",
            round_number=1,
            raw_message=req_msg_text,
            structured_data=buyer_request.model_dump_json(),
            created_at=now,
        )
        db.add(buyer_msg)

        # 2. Instantiate Merchant Agent and Run Deterministic Tool Pipeline
        merchant_agent = MerchantAgent(merchant_id=merchant_id)
        offer_data, merchant_msg_text, traces_data = merchant_agent.process_buyer_request(
            db=db,
            buyer_req=buyer_request,
            round_number=1,
        )

        # 3. Create Offer Record
        offer_id = f"ofr_{uuid.uuid4().hex[:8]}"
        offer = NegotiationOffer(
            id=offer_id,
            session_id=session_id,
            candidate_id=offer_data.get("candidate_id"),
            round_number=1,
            product_id=offer_data["product_id"],
            product_name=offer_data["product_name"],
            quantity=offer_data["quantity"],
            unit_price=offer_data["unit_price"],
            gross_value=offer_data["gross_value"],
            payment_timing_days=offer_data["payment_timing_days"],
            delivery_days=offer_data["delivery_days"],
            economic_value=offer_data["economic_value"],
            current_pressure_score=offer_data["current_pressure_score"],
            projected_pressure_score=offer_data["projected_pressure_score"],
            pressure_score_delta=offer_data["pressure_score_delta"],
            status="OFFERED",
            strategy_tag=offer_data.get("strategy_tag"),
            rationale=offer_data.get("rationale"),
            created_at=now,
        )
        db.add(offer)

        # 4. Record Merchant Offer Message
        merchant_msg = NegotiationMessage(
            id=f"msg_{uuid.uuid4().hex[:8]}",
            session_id=session_id,
            sender="merchant",
            message_type="offer",
            round_number=1,
            raw_message=merchant_msg_text,
            structured_data=json.dumps(offer_data, default=str),
            created_at=now,
        )
        db.add(merchant_msg)

        # 5. Record Traces
        for td in traces_data:
            t = AgentTrace(
                id=f"trc_{uuid.uuid4().hex[:8]}",
                session_id=session_id,
                round_number=1,
                timestamp=now,
                agent=td["agent"],
                action=td["action"],
                tool_called=td.get("tool_called"),
                tool_input=json.dumps(td.get("tool_input", {})),
                tool_output_summary=td.get("tool_output_summary"),
                decision=td.get("decision"),
                result=td.get("result"),
            )
            db.add(t)

        # 6. Update Session
        session.status = "OFFERED"
        session.current_offer_id = offer_id
        db.commit()

        return NegotiationService._map_session_response(session, buyer_request)

    @staticmethod
    def send_buyer_counter(
        db: Session,
        session_id: str,
        payload: BuyerCounterRequest,
    ) -> NegotiationSessionResponse:
        session = db.query(NegotiationSession).filter(NegotiationSession.id == session_id).first()
        if not session:
            raise ValueError(f"Negotiation session '{session_id}' not found")
        if session.status in ("ACCEPTED", "REJECTED", "EXPIRED"):
            raise ValueError(f"Negotiation session is already finalized as {session.status}")

        now = datetime.utcnow()
        buyer_req = BuyerRequest(**json.loads(session.buyer_request_data))
        current_offer = (
            db.query(NegotiationOffer).filter(NegotiationOffer.id == session.current_offer_id).first()
            or session.offers[-1]
        )

        current_offer_dict = {
            "id": current_offer.id,
            "product_id": current_offer.product_id,
            "product_name": current_offer.product_name,
            "quantity": current_offer.quantity,
            "unit_price": current_offer.unit_price,
            "gross_value": current_offer.gross_value,
            "payment_timing_days": current_offer.payment_timing_days,
            "delivery_days": current_offer.delivery_days,
            "economic_value": current_offer.economic_value,
        }

        # Determine counter parameters
        target_budget = payload.target_budget or (buyer_req.maximum_budget if buyer_req.maximum_budget < current_offer.gross_value else current_offer.gross_value * Decimal("0.96"))
        counter_params = {
            "target_budget": target_budget,
            "requested_quantity": payload.requested_quantity or current_offer.quantity,
            "preferred_payment_days": payload.preferred_payment_days if payload.preferred_payment_days is not None else current_offer.payment_timing_days,
            "max_delivery_days": payload.max_delivery_days or current_offer.delivery_days,
        }

        new_round = session.round_number + 1
        session.round_number = new_round
        session.status = "BUYER_COUNTERED"

        # 1. Record Buyer Counter Message
        counter_text = payload.counter_message or f"Can you meet our target budget of {format_inr(target_budget)} for {counter_params['requested_quantity']} units?"
        buyer_msg = NegotiationMessage(
            id=f"msg_{uuid.uuid4().hex[:8]}",
            session_id=session_id,
            sender="buyer",
            message_type="counter",
            round_number=new_round,
            raw_message=counter_text,
            structured_data=json.dumps(counter_params, default=str),
            created_at=now,
        )
        db.add(buyer_msg)

        # 2. Merchant Agent Re-evaluation
        merchant_agent = MerchantAgent(merchant_id=session.merchant_id)
        updated_offer_data, merchant_msg_text, status_res, traces_data = merchant_agent.evaluate_buyer_counter(
            db=db,
            counter_params=counter_params,
            current_offer=current_offer_dict,
            round_number=new_round,
        )

        # 3. Create New Offer Record
        if updated_offer_data:
            new_offer_id = f"ofr_{uuid.uuid4().hex[:8]}"
            new_offer = NegotiationOffer(
                id=new_offer_id,
                session_id=session_id,
                candidate_id=updated_offer_data.get("candidate_id"),
                round_number=new_round,
                product_id=updated_offer_data["product_id"],
                product_name=updated_offer_data["product_name"],
                quantity=updated_offer_data["quantity"],
                unit_price=updated_offer_data["unit_price"],
                gross_value=updated_offer_data["gross_value"],
                payment_timing_days=updated_offer_data["payment_timing_days"],
                delivery_days=updated_offer_data["delivery_days"],
                economic_value=updated_offer_data["economic_value"],
                current_pressure_score=updated_offer_data["current_pressure_score"],
                projected_pressure_score=updated_offer_data["projected_pressure_score"],
                pressure_score_delta=updated_offer_data["pressure_score_delta"],
                status="OFFERED",
                strategy_tag=updated_offer_data.get("strategy_tag"),
                rationale=updated_offer_data.get("rationale"),
                created_at=now,
            )
            db.add(new_offer)
            session.current_offer_id = new_offer_id

        # 4. Record Merchant Counter/Response Message
        merchant_msg = NegotiationMessage(
            id=f"msg_{uuid.uuid4().hex[:8]}",
            session_id=session_id,
            sender="merchant",
            message_type="offer" if status_res == "COUNTER_OFFERED" else "rejection",
            round_number=new_round,
            raw_message=merchant_msg_text,
            structured_data=json.dumps(updated_offer_data, default=str) if updated_offer_data else None,
            created_at=now,
        )
        db.add(merchant_msg)

        # 5. Record Traces
        for td in traces_data:
            t = AgentTrace(
                id=f"trc_{uuid.uuid4().hex[:8]}",
                session_id=session_id,
                round_number=new_round,
                timestamp=now,
                agent=td["agent"],
                action=td["action"],
                tool_called=td.get("tool_called"),
                tool_input=json.dumps(td.get("tool_input", {})),
                tool_output_summary=td.get("tool_output_summary"),
                decision=td.get("decision"),
                result=td.get("result"),
            )
            db.add(t)

        # 6. Automatic Buyer Evaluation of the Counteroffer
        if updated_offer_data:
            buyer_agent = AIBuyerAgent(request=buyer_req)
            buyer_decision, buyer_decision_text, _ = buyer_agent.evaluate_offer(
                offer_data=updated_offer_data,
                round_number=new_round,
                max_rounds=session.max_rounds,
            )

            if buyer_decision == "ACCEPT":
                session.status = "ACCEPTED"
                session.final_agreement_data = json.dumps(updated_offer_data, default=str)
                # Record Buyer Acceptance Message
                accept_msg = NegotiationMessage(
                    id=f"msg_{uuid.uuid4().hex[:8]}",
                    session_id=session_id,
                    sender="buyer",
                    message_type="acceptance",
                    round_number=new_round,
                    raw_message=buyer_decision_text,
                    structured_data=json.dumps({"agreement": updated_offer_data}, default=str),
                    created_at=datetime.utcnow(),
                )
                db.add(accept_msg)
            elif new_round >= session.max_rounds:
                session.status = "EXPIRED"
            else:
                session.status = "COUNTER_OFFERED"

        db.commit()
        return NegotiationService._map_session_response(session, buyer_req)

    @staticmethod
    def accept_offer(db: Session, session_id: str) -> NegotiationSessionResponse:
        session = db.query(NegotiationSession).filter(NegotiationSession.id == session_id).first()
        if not session:
            raise ValueError(f"Negotiation session '{session_id}' not found")

        current_offer = db.query(NegotiationOffer).filter(NegotiationOffer.id == session.current_offer_id).first()
        if not current_offer:
            raise ValueError("No active offer found to accept")

        now = datetime.utcnow()
        session.status = "ACCEPTED"
        current_offer.status = "ACCEPTED"
        agreement_payload = {
            "offer_id": current_offer.id,
            "quantity": current_offer.quantity,
            "unit_price": float(current_offer.unit_price),
            "gross_value": float(current_offer.gross_value),
            "payment_timing_days": current_offer.payment_timing_days,
            "delivery_days": current_offer.delivery_days,
            "economic_value": float(current_offer.economic_value),
            "accepted_at": now.isoformat(),
        }
        session.final_agreement_data = json.dumps(agreement_payload)

        # Record message
        msg = NegotiationMessage(
            id=f"msg_{uuid.uuid4().hex[:8]}",
            session_id=session_id,
            sender="buyer",
            message_type="acceptance",
            round_number=session.round_number,
            raw_message=f"Offer of {format_inr(Decimal(str(current_offer.gross_value)))} accepted. Commercial agreement finalized.",
            structured_data=json.dumps(agreement_payload),
            created_at=now,
        )
        db.add(msg)
        db.commit()

        buyer_req = BuyerRequest(**json.loads(session.buyer_request_data))
        return NegotiationService._map_session_response(session, buyer_req)

    @staticmethod
    def reject_offer(db: Session, session_id: str, reason: str = "Commercial terms unacceptable") -> NegotiationSessionResponse:
        session = db.query(NegotiationSession).filter(NegotiationSession.id == session_id).first()
        if not session:
            raise ValueError(f"Negotiation session '{session_id}' not found")

        now = datetime.utcnow()
        session.status = "REJECTED"
        if session.current_offer_id:
            current_offer = db.query(NegotiationOffer).filter(NegotiationOffer.id == session.current_offer_id).first()
            if current_offer:
                current_offer.status = "REJECTED"

        msg = NegotiationMessage(
            id=f"msg_{uuid.uuid4().hex[:8]}",
            session_id=session_id,
            sender="buyer",
            message_type="rejection",
            round_number=session.round_number,
            raw_message=f"Negotiation closed: {reason}",
            structured_data=json.dumps({"reason": reason}),
            created_at=now,
        )
        db.add(msg)
        db.commit()

        buyer_req = BuyerRequest(**json.loads(session.buyer_request_data))
        return NegotiationService._map_session_response(session, buyer_req)

    @staticmethod
    def run_demo_scenario(db: Session, merchant_id: str) -> NegotiationSessionResponse:
        """
        Executes an end-to-end, multi-turn B2B agentic negotiation demo:
        Round 1: Buyer requests 300 units with budget ₹3.60L.
        Merchant Agent analyzes and offers 350 units at ₹930 each (immediate cash).
        Round 2: Buyer counters with target budget ₹3.45L.
        Merchant Agent re-evaluates and offers ₹3.45L for 350 units (meeting margin constraints).
        Round 3: Buyer accepts agreement!
        """
        # Step 1: Initialize session
        demo_request = BuyerRequest(
            buyer_id="buyer_industrial_solutions_ltd",
            intent="bulk_purchase",
            product_requirements=["Forged Carbon Steel Weld Neck Flange"],
            product_id="prod_08",
            quantity=45,
            maximum_budget=Decimal("115000.00"),
            maximum_delivery_days=6,
            preferred_payment_days=0,
            raw_inquiry_text="Need 45 units of Forged Weld Neck Flanges within 6 days. Target budget ₹1.15 Lakh with immediate payment.",
        )

        res1 = NegotiationService.start_negotiation(
            db=db,
            merchant_id=merchant_id,
            buyer_request=demo_request,
        )

        # Step 2: Buyer counters with ₹1.08L for 50 units
        counter_req = BuyerCounterRequest(
            counter_message="We reviewed your initial offer. Can you meet ₹1.08 Lakh for 50 units with immediate settlement?",
            target_budget=Decimal("108000.00"),
            requested_quantity=50,
            preferred_payment_days=0,
            max_delivery_days=5,
        )

        res2 = NegotiationService.send_buyer_counter(
            db=db,
            session_id=res1.id,
            payload=counter_req,
        )

        # Step 3: Buyer accepts the merchant's matched counteroffer
        res3 = NegotiationService.accept_offer(
            db=db,
            session_id=res1.id,
        )

        return res3

    @staticmethod
    def get_negotiations(db: Session, merchant_id: str) -> NegotiationListResponse:
        sessions = (
            db.query(NegotiationSession)
            .filter(NegotiationSession.merchant_id == merchant_id)
            .order_by(NegotiationSession.updated_at.desc())
            .all()
        )

        items = []
        for s in sessions:
            req_data = json.loads(s.buyer_request_data) if s.buyer_request_data else {}
            current_ofr = next((o for o in s.offers if o.id == s.current_offer_id), s.offers[-1] if s.offers else None)
            
            budget = Decimal(str(req_data.get("maximum_budget", 0)))
            ofr_amt = Decimal(str(current_ofr.gross_value)) if current_ofr else None
            evc = Decimal(str(current_ofr.economic_value)) if current_ofr else None

            items.append(
                NegotiationListItem(
                    id=s.id,
                    merchant_id=s.merchant_id,
                    buyer_id=s.buyer_id,
                    status=s.status,
                    round_number=s.round_number,
                    requested_quantity=req_data.get("quantity", 0),
                    maximum_budget=budget,
                    maximum_budget_formatted=format_inr(budget),
                    current_offer_amount=ofr_amt,
                    current_offer_amount_formatted=format_inr(ofr_amt) if ofr_amt else None,
                    economic_value=evc,
                    economic_value_formatted=format_inr(evc) if evc else None,
                    created_at=s.created_at,
                )
            )

        return NegotiationListResponse(total_sessions=len(items), sessions=items)

    @staticmethod
    def get_negotiation_by_id(db: Session, session_id: str, merchant_id: str) -> NegotiationSessionResponse:
        session = (
            db.query(NegotiationSession)
            .filter(NegotiationSession.id == session_id, NegotiationSession.merchant_id == merchant_id)
            .first()
        )
        if not session:
            raise ValueError(f"Negotiation session '{session_id}' not found")

        buyer_req = BuyerRequest(**json.loads(session.buyer_request_data))
        return NegotiationService._map_session_response(session, buyer_req)
