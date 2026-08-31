import json
from decimal import Decimal
import pytest
from app.models.negotiation import NegotiationSession, NegotiationOffer
from app.models.payment import PaymentOrder, PaymentWebhookLog
from app.models.inventory import InventoryItem
from app.models.transaction import Transaction
from app.models.snapshot import EconomicSnapshot
from app.schemas.agent import BuyerRequest
from app.schemas.payment import (
    PaymentVerifyRequest,
)
from app.agent.negotiation_service import NegotiationService
from app.services.payment_service import PaymentService, RazorpayClientWrapper


def test_payment_order_creation_from_accepted_negotiation(db):
    # 1. Run demo scenario to get an ACCEPTED negotiation session
    session_res = NegotiationService.run_demo_scenario(db=db, merchant_id="mch_aarav_001")
    assert session_res.status == "ACCEPTED"

    # 2. Create PaymentOrder
    payment_res = PaymentService.create_payment_order(db=db, negotiation_id=session_res.id)
    assert payment_res.id.startswith("pay_ord_")
    assert payment_res.negotiation_id == session_res.id
    assert payment_res.status == "CREATED"
    assert payment_res.razorpay_order_id.startswith("order_")
    assert payment_res.amount > Decimal("0.00")
    assert payment_res.amount_paise == int(payment_res.amount * 100)
    assert "MLE-" in payment_res.receipt

    # 3. Check database record
    db_order = db.query(PaymentOrder).filter(PaymentOrder.id == payment_res.id).first()
    assert db_order is not None
    assert db_order.status == "CREATED"
    assert db_order.before_state_json is not None


def test_payment_order_blocked_for_non_accepted_negotiation(db):
    # 1. Start a session (status = OFFERED, not yet ACCEPTED)
    req = BuyerRequest(
        buyer_id="buyer_test_unaccepted",
        intent="inquiry",
        product_requirements=["Valves"],
        quantity=100,
        maximum_budget=Decimal("200000.00"),
        maximum_delivery_days=7,
        preferred_payment_days=0,
    )
    session_res = NegotiationService.start_negotiation(db=db, merchant_id="mch_aarav_001", buyer_request=req)
    assert session_res.status == "OFFERED"

    # 2. Attempt to create payment order -> Expect ValueError
    with pytest.raises(ValueError, match="Only ACCEPTED negotiations can proceed to payment"):
        PaymentService.create_payment_order(db=db, negotiation_id=session_res.id)


def test_payment_signature_verification_and_state_transition(db):
    # 1. Prepare accepted negotiation and payment order
    session_res = NegotiationService.run_demo_scenario(db=db, merchant_id="mch_aarav_001")
    payment_res = PaymentService.create_payment_order(db=db, negotiation_id=session_res.id)

    # Initial inventory check
    offer = db.query(NegotiationOffer).filter(NegotiationOffer.id == session_res.current_offer.id).first()
    inv_before = db.query(InventoryItem).filter(InventoryItem.product_id == offer.product_id).first()
    initial_qty = inv_before.available_quantity

    # 2. Execute verification with valid test signature
    verify_req = PaymentVerifyRequest(
        payment_order_id=payment_res.id,
        razorpay_order_id=payment_res.razorpay_order_id,
        razorpay_payment_id=f"pay_test_{payment_res.id[-8:]}",
        razorpay_signature="mock_valid_test_signature",
    )

    verify_res = PaymentService.verify_payment_and_execute(db=db, payload=verify_req)

    # Assertions
    assert verify_res.success is True
    assert verify_res.status == "PAID"
    assert verify_res.transaction_id.startswith("tx_")
    assert verify_res.amount == payment_res.amount
    assert len(verify_res.metrics_comparison) >= 4

    # 3. Verify database updates
    # PaymentOrder updated
    db_order = db.query(PaymentOrder).filter(PaymentOrder.id == payment_res.id).first()
    assert db_order.status == "PAID"
    assert db_order.paid_at is not None
    assert db_order.after_state_json is not None

    # Inventory decremented
    inv_after = db.query(InventoryItem).filter(InventoryItem.product_id == offer.product_id).first()
    assert inv_after.available_quantity == initial_qty - offer.quantity

    # Transaction created
    tx = db.query(Transaction).filter(Transaction.id == verify_res.transaction_id).first()
    assert tx is not None
    assert tx.gross_value == payment_res.amount
    assert tx.source == "agentic_negotiation"
    assert tx.payment_order_id == payment_res.id


def test_invalid_payment_signature_rejected(db):
    session_res = NegotiationService.run_demo_scenario(db=db, merchant_id="mch_aarav_001")
    payment_res = PaymentService.create_payment_order(db=db, negotiation_id=session_res.id)

    # Execute verification with forged signature
    verify_req = PaymentVerifyRequest(
        payment_order_id=payment_res.id,
        razorpay_order_id=payment_res.razorpay_order_id,
        razorpay_payment_id="pay_fraud_12345",
        razorpay_signature="forged_invalid_signature_hex_xyz",
    )

    with pytest.raises(ValueError, match="Cryptographic Razorpay payment signature verification failed"):
        PaymentService.verify_payment_and_execute(db=db, payload=verify_req)

    # Order marked as failed
    db_order = db.query(PaymentOrder).filter(PaymentOrder.id == payment_res.id).first()
    assert db_order.status == "FAILED"


def test_economic_twin_recalculation_and_snapshot_creation(db):
    snapshots_count_before = db.query(EconomicSnapshot).filter(EconomicSnapshot.merchant_id == "mch_aarav_001").count()

    session_res = NegotiationService.run_demo_scenario(db=db, merchant_id="mch_aarav_001")
    payment_res = PaymentService.create_payment_order(db=db, negotiation_id=session_res.id)

    verify_req = PaymentVerifyRequest(
        payment_order_id=payment_res.id,
        razorpay_order_id=payment_res.razorpay_order_id,
        razorpay_payment_id=f"pay_test_{payment_res.id[-6:]}",
        razorpay_signature="mock_valid_test_signature",
    )
    verify_res = PaymentService.verify_payment_and_execute(db=db, payload=verify_req)

    # Verify a new snapshot was recorded
    snapshots_count_after = db.query(EconomicSnapshot).filter(EconomicSnapshot.merchant_id == "mch_aarav_001").count()
    assert snapshots_count_after == snapshots_count_before + 1

    latest_snapshot = (
        db.query(EconomicSnapshot)
        .filter(EconomicSnapshot.merchant_id == "mch_aarav_001")
        .order_by(EconomicSnapshot.snapshot_date.desc())
        .first()
    )
    assert "Agentic" in latest_snapshot.event_marker
    assert verify_res.realized_evc > Decimal("0.00")


def test_webhook_idempotency_duplicate_protection(db):
    session_res = NegotiationService.run_demo_scenario(db=db, merchant_id="mch_aarav_001")
    payment_res = PaymentService.create_payment_order(db=db, negotiation_id=session_res.id)

    webhook_payload = {
        "id": "evt_test_webhook_idempotent_001",
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_whk_001",
                    "order_id": payment_res.razorpay_order_id,
                    "amount": payment_res.amount_paise,
                    "status": "captured",
                }
            }
        }
    }
    body_bytes = json.dumps(webhook_payload).encode("utf-8")

    # 1. First webhook delivery
    res1 = PaymentService.process_webhook(
        db=db,
        raw_body_bytes=body_bytes,
        signature="mock_valid_webhook_signature",
    )
    assert res1["status"] == "success"
    assert res1["processed"] is True

    # 2. Second webhook delivery (Replay duplicate)
    res2 = PaymentService.process_webhook(
        db=db,
        raw_body_bytes=body_bytes,
        signature="mock_valid_webhook_signature",
    )
    assert res2["status"] == "duplicate_ignored"
    assert res2["processed"] is True


def test_payment_api_endpoints_full_lifecycle(client):
    # 1. Run demo scenario through agent API
    demo_res = client.post("/api/agent/negotiations/demo", json={})
    assert demo_res.status_code == 200
    session_data = demo_res.json()
    negotiation_id = session_data["id"]
    assert session_data["status"] == "ACCEPTED"

    # 2. Create Payment Order
    create_res = client.post("/api/payments/orders", json={"negotiation_id": negotiation_id})
    assert create_res.status_code == 200
    order_data = create_res.json()
    payment_order_id = order_data["id"]
    razorpay_order_id = order_data["razorpay_order_id"]
    assert order_data["status"] == "CREATED"
    assert float(order_data["amount"]) > 0

    # 3. Retrieve payment by negotiation
    get_neg_res = client.get(f"/api/payments/negotiation/{negotiation_id}")
    assert get_neg_res.status_code == 200
    assert get_neg_res.json()["id"] == payment_order_id

    # 4. Verify Payment Execution
    verify_res = client.post(
        "/api/payments/verify",
        json={
            "payment_order_id": payment_order_id,
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": "pay_test_api_success_123",
            "razorpay_signature": "mock_valid_test_signature",
        },
    )
    assert verify_res.status_code == 200
    verify_data = verify_res.json()
    assert verify_data["success"] is True
    assert verify_data["status"] == "PAID"
    assert len(verify_data["metrics_comparison"]) >= 4

    # 5. Webhook endpoint
    whk_res = client.post(
        "/api/payments/razorpay/webhook",
        headers={"X-Razorpay-Signature": "mock_valid_webhook_signature"},
        json={
            "id": "evt_api_test_001",
            "event": "order.paid",
            "payload": {
                "payment": {
                    "entity": {
                        "id": "pay_whk_api_001",
                        "order_id": razorpay_order_id,
                        "status": "captured",
                    }
                }
            }
        },
    )
    assert whk_res.status_code == 200
    assert whk_res.json()["processed"] is True
