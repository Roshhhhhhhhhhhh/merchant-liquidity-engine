import json
from decimal import Decimal
import pytest
from app.models.inventory import InventoryItem
from app.models.payment import PaymentOrder
from app.schemas.payment import PaymentVerifyRequest
from app.agent.negotiation_service import NegotiationService
from app.services.payment_service import PaymentService


# --------------- helpers ---------------

def _patch_inv(db, product_id, merchant_id, days, status="Active"):
    inv = db.query(InventoryItem).filter(
        InventoryItem.product_id == product_id,
        InventoryItem.merchant_id == merchant_id,
    ).first()
    if inv is None:
        pytest.skip(f"No InventoryItem for {product_id}")
    orig_days, orig_status = inv.days_in_stock, inv.status
    inv.days_in_stock = days
    inv.status = status
    db.flush()
    return inv, orig_days, orig_status


def _deal_d(db, product_id, merchant_id):
    from app.services.deal_generator import DealCandidateGenerator
    from app.schemas.scenario import BuyerRequestModel, MerchantConstraintsModel
    from app.services.economic_state_service import EconomicStateService
    state = EconomicStateService.calculate_current_state(db=db, merchant_id=merchant_id)
    req = BuyerRequestModel(product_id=product_id, requested_quantity=50,
                            target_budget=Decimal("115000.00"), max_delivery_days=6)
    cons = MerchantConstraintsModel(min_margin_pct=Decimal("8.0"), max_discount_pct=Decimal("12.0"))
    cands = DealCandidateGenerator.generate_candidates(db=db, merchant_id=merchant_id,
                                                       current_state=state, request=req, constraints=cons)
    return next(c for c in cands if "cand_d" in c["id"])


# --------------- Issue 1 ---------------

def test_immediate_payment_cash_delta(db):
    """Immediate payment must increase cash by the payment amount (tests db.flush fix)."""
    session_res = NegotiationService.run_demo_scenario(db=db, merchant_id="mch_aarav_001")
    assert session_res.status == "ACCEPTED"
    payment_res = PaymentService.create_payment_order(db=db, negotiation_id=session_res.id)
    amount = payment_res.amount
    before_state = json.loads(db.query(PaymentOrder).filter(PaymentOrder.id == payment_res.id).first().before_state_json)
    before_cash = Decimal(str(before_state["cash_position"]))
    verify_req = PaymentVerifyRequest(
        payment_order_id=payment_res.id,
        razorpay_order_id=payment_res.razorpay_order_id,
        razorpay_payment_id=f"pay_test_delta_{payment_res.id[-6:]}",
        razorpay_signature="mock_valid_test_signature",
    )
    verify_res = PaymentService.verify_payment_and_execute(db=db, payload=verify_req)
    assert verify_res.success is True
    after_state = json.loads(db.query(PaymentOrder).filter(PaymentOrder.id == payment_res.id).first().after_state_json)
    after_cash = Decimal(str(after_state["cash_position"]))
    delta = after_cash - before_cash
    assert delta > Decimal("0.00"), f"Cash delta is {delta} — must be positive for immediate payment of {amount}"
    assert abs(delta - amount) < Decimal("1.00"), f"Cash delta {delta} should equal payment amount {amount}"


# --------------- Issue 2 ---------------

def test_fresh_sku_22d_not_aging_clearance(db):
    """22d SKU: strategy_tag must NOT be Aging Clearance (threshold is 45d)."""
    demo = NegotiationService.run_demo_scenario(db=db, merchant_id="mch_aarav_001")
    pid = demo.current_offer.product_id
    inv, od, os_ = _patch_inv(db, pid, "mch_aarav_001", 22, "Active")
    try:
        d = _deal_d(db, pid, "mch_aarav_001")
        assert d["strategy_tag"] != "Aging Clearance", f"22d SKU got strategy_tag={d['strategy_tag']}"
        assert d["target_aging_reduction_units"] == 0
    finally:
        inv.days_in_stock, inv.status = od, os_; db.flush()


def test_old_sku_60d_is_aging_clearance(db):
    """60d SKU: strategy_tag MUST be Aging Clearance with relief units > 0."""
    demo = NegotiationService.run_demo_scenario(db=db, merchant_id="mch_aarav_001")
    pid = demo.current_offer.product_id
    inv, od, os_ = _patch_inv(db, pid, "mch_aarav_001", 60, "Aging")
    try:
        d = _deal_d(db, pid, "mch_aarav_001")
        assert d["strategy_tag"] == "Aging Clearance", f"60d SKU got strategy_tag={d['strategy_tag']}"
        assert d["target_aging_reduction_units"] > 0
    finally:
        inv.days_in_stock, inv.status = od, os_; db.flush()


def test_boundary_45d_not_aging_clearance(db):
    """45d exactly: condition is strictly greater-than 45, so 45 must NOT trigger Aging Clearance."""
    demo = NegotiationService.run_demo_scenario(db=db, merchant_id="mch_aarav_001")
    pid = demo.current_offer.product_id
    inv, od, os_ = _patch_inv(db, pid, "mch_aarav_001", 45, "Active")
    try:
        d = _deal_d(db, pid, "mch_aarav_001")
        assert d["strategy_tag"] != "Aging Clearance", f"Exactly 45d SKU got strategy_tag={d['strategy_tag']}"
        assert d["target_aging_reduction_units"] == 0
    finally:
        inv.days_in_stock, inv.status = od, os_; db.flush()


def test_critical_status_triggers_aging_clearance(db):
    """status=Critical must yield Aging Clearance even if days_in_stock is below numeric threshold."""
    demo = NegotiationService.run_demo_scenario(db=db, merchant_id="mch_aarav_001")
    pid = demo.current_offer.product_id
    inv, od, os_ = _patch_inv(db, pid, "mch_aarav_001", 20, "Critical")
    try:
        d = _deal_d(db, pid, "mch_aarav_001")
        assert d["strategy_tag"] == "Aging Clearance", f"Critical status got strategy_tag={d['strategy_tag']}"
        assert d["target_aging_reduction_units"] > 0
    finally:
        inv.days_in_stock, inv.status = od, os_; db.flush()
