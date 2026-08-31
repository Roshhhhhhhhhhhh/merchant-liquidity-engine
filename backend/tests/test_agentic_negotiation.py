from decimal import Decimal
import pytest
from app.schemas.agent import BuyerRequest, BuyerCounterRequest
from app.agent.provider import DeterministicFallbackProvider, GeminiProvider, get_llm_provider
from app.agent.tools import AgentTools
from app.agent.buyer_agent import AIBuyerAgent
from app.agent.merchant_agent import MerchantAgent
from app.agent.negotiation_service import NegotiationService
from app.models.negotiation import NegotiationSession, NegotiationOffer, NegotiationMessage, AgentTrace


def test_natural_language_buyer_request_extraction():
    provider = DeterministicFallbackProvider()
    raw_msg = "We need 300 units of industrial valves within 6 days. Our procurement budget is ₹3.60 Lakh and we can settle immediately via UPI."
    
    req, mode = provider.extract_buyer_request(raw_msg)
    
    assert mode == "fallback"
    assert req.quantity == 300
    assert req.maximum_budget == Decimal("360000.00")
    assert req.maximum_delivery_days == 6
    assert req.preferred_payment_days == 0
    assert "Industrial Control Valves" in req.product_requirements


def test_deterministic_agent_tools(db):
    state = AgentTools.get_merchant_state(db=db, merchant_id="mch_aarav_001")
    assert state.merchant_id == "mch_aarav_001"
    assert state.pressure_score >= 0

    catalog = AgentTools.get_product_catalog(db=db, merchant_id="mch_aarav_001")
    assert len(catalog) >= 1
    assert catalog[0]["list_price"] > 0

    inventory = AgentTools.get_inventory(db=db, merchant_id="mch_aarav_001")
    assert len(inventory) >= 1

    buyer_req = BuyerRequest(
        quantity=250,
        maximum_budget=Decimal("300000.00"),
        maximum_delivery_days=5,
        preferred_payment_days=0,
    )
    candidates = AgentTools.generate_deal_candidates(
        db=db,
        merchant_id="mch_aarav_001",
        buyer_req=buyer_req,
    )
    assert len(candidates) == 4


def test_deterministic_financial_immutability(db):
    """
    CRITICAL SAFETY TEST:
    Verify that MerchantAgent output financial figures match exact calculations
    and cannot be arbitrarily invented or modified.
    """
    merchant_agent = MerchantAgent(merchant_id="mch_aarav_001")
    buyer_req = BuyerRequest(
        quantity=300,
        maximum_budget=Decimal("360000.00"),
        maximum_delivery_days=6,
        preferred_payment_days=0,
    )
    
    offer, message, traces = merchant_agent.process_buyer_request(
        db=db,
        buyer_req=buyer_req,
        round_number=1,
    )

    # Unit price * quantity MUST equal gross value exactly
    expected_gross = Decimal(offer["quantity"]) * offer["unit_price"]
    assert offer["gross_value"] == expected_gross
    assert offer["economic_value"] > 0
    assert len(traces) >= 3


def test_ai_buyer_agent_decision_logic():
    buyer_req = BuyerRequest(
        quantity=300,
        maximum_budget=Decimal("360000.00"),
        maximum_delivery_days=6,
        preferred_payment_days=0,
    )
    buyer_agent = AIBuyerAgent(request=buyer_req)

    # 1. Offer within budget -> ACCEPT
    offer_within = {
        "gross_value": Decimal("350000.00"),
        "quantity": 300,
        "delivery_days": 5,
        "payment_timing_days": 0,
    }
    decision1, _, _ = buyer_agent.evaluate_offer(offer_within, round_number=1)
    assert decision1 == "ACCEPT"

    # 2. Offer slightly above budget (within 5% tolerance) on early round -> COUNTER
    offer_counterable = {
        "gross_value": Decimal("370000.00"),
        "quantity": 300,
        "delivery_days": 5,
        "payment_timing_days": 0,
    }
    decision2, _, counter2 = buyer_agent.evaluate_offer(offer_counterable, round_number=1)
    assert decision2 == "COUNTER"
    assert counter2["target_budget"] == Decimal("360000.00")

    # 3. Offer excessively above budget -> REJECT
    offer_too_high = {
        "gross_value": Decimal("480000.00"),
        "quantity": 300,
        "delivery_days": 5,
        "payment_timing_days": 0,
    }
    decision3, _, _ = buyer_agent.evaluate_offer(offer_too_high, round_number=1)
    assert decision3 == "REJECT"


def test_negotiation_service_start_and_advance(db):
    buyer_req = BuyerRequest(
        quantity=300,
        maximum_budget=Decimal("360000.00"),
        maximum_delivery_days=6,
        preferred_payment_days=0,
        raw_inquiry_text="Need 300 units within 6 days. Target budget ₹3.60L.",
    )

    # 1. Start session
    session_res = NegotiationService.start_negotiation(
        db=db,
        merchant_id="mch_aarav_001",
        buyer_request=buyer_req,
    )
    assert session_res.id.startswith("neg_")
    assert session_res.status == "OFFERED"
    assert session_res.round_number == 1
    assert len(session_res.messages) == 2  # Request + Offer
    assert len(session_res.offers) == 1
    assert len(session_res.traces) >= 3

    # 2. Send buyer counter
    counter = BuyerCounterRequest(
        counter_message="Can you adjust price to ₹3.45L?",
        target_budget=Decimal("345000.00"),
        requested_quantity=300,
    )
    advanced_res = NegotiationService.send_buyer_counter(
        db=db,
        session_id=session_res.id,
        payload=counter,
    )
    assert advanced_res.round_number == 2
    assert len(advanced_res.offers) == 2
    assert advanced_res.status in ("COUNTER_OFFERED", "ACCEPTED")


def test_end_to_end_demo_scenario(db):
    res = NegotiationService.run_demo_scenario(db=db, merchant_id="mch_aarav_001")
    assert res.id.startswith("neg_")
    assert res.status == "ACCEPTED"
    assert res.round_number >= 2
    assert res.final_agreement is not None
    assert len(res.messages) >= 4
    assert len(res.traces) >= 4


def test_agent_api_endpoints(client):
    # 1. Parse natural language request
    parse_res = client.post(
        "/api/agent/buyer/request",
        json={"message": "We need 250 units within 5 days with budget ₹3.2 Lakhs and immediate settlement."},
    )
    assert parse_res.status_code == 200
    req_data = parse_res.json()
    assert req_data["quantity"] == 250
    assert float(req_data["maximum_budget"]) == 320000.00

    # 2. Start negotiation session
    start_res = client.post(
        "/api/agent/negotiations",
        json={"buyer_request": req_data},
    )
    assert start_res.status_code == 200
    session_data = start_res.json()
    session_id = session_data["id"]
    assert session_data["status"] == "OFFERED"
    assert session_data["round_number"] == 1

    # 3. Get session by ID
    get_res = client.get(f"/api/agent/negotiations/{session_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == session_id

    # 4. List all sessions
    list_res = client.get("/api/agent/negotiations")
    assert list_res.status_code == 200
    assert list_res.json()["total_sessions"] >= 1

    # 5. Run automated demo scenario
    demo_res = client.post("/api/agent/negotiations/demo", json={})
    assert demo_res.status_code == 200
    demo_data = demo_res.json()
    assert demo_data["status"] == "ACCEPTED"
    assert demo_data["final_agreement"] is not None
