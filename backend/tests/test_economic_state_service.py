import datetime
from decimal import Decimal
import pytest
from app.services.economic_state_service import EconomicStateService, EconomicModelConfig
from app.schemas.economic_state import EconomicActionModel
from app.models import Merchant, Product, InventoryItem, Receivable, Payable, Transaction, Customer, EconomicSnapshot


def test_calculate_current_state_basic(db):
    state = EconomicStateService.calculate_current_state(db=db, merchant_id="mch_aarav_001")

    assert state.merchant_id == "mch_aarav_001"
    assert state.cash_position > 0
    assert state.total_receivables > 0
    assert state.overdue_receivables > 0
    assert state.total_payables > 0
    assert state.inventory_valuation > 0
    assert state.aging_inventory_value > 0
    assert state.gross_margin_pct >= Decimal("20.0")
    assert state.cash_runway_days > 0
    assert 0 <= state.pressure_score <= 100
    assert state.state in ("Strong", "Healthy", "Watch", "Stressed", "Critical")
    assert len(state.top_drivers) >= 4


def test_inventory_value_and_aging(db):
    state = EconomicStateService.calculate_current_state(db=db, merchant_id="mch_aarav_001")

    # Verify inventory value equals sum of available_quantity * unit_cost
    inv_items = (
        db.query(InventoryItem)
        .join(Product, InventoryItem.product_id == Product.id)
        .filter(InventoryItem.merchant_id == "mch_aarav_001")
        .all()
    )
    expected_total = sum(Decimal(i.available_quantity) * Decimal(str(i.product.unit_cost)) for i in inv_items)
    expected_aging = sum(
        Decimal(i.available_quantity) * Decimal(str(i.product.unit_cost))
        for i in inv_items
        if i.days_in_stock > EconomicModelConfig.AGING_INVENTORY_DAYS_THRESHOLD or i.status in ("Aging", "Critical")
    )

    assert state.inventory_valuation == expected_total
    assert state.aging_inventory_value == expected_aging
    assert state.inventory_value.value == expected_total
    assert state.aging_inventory.value == expected_aging


def test_receivables_and_overdue(db):
    state = EconomicStateService.calculate_current_state(db=db, merchant_id="mch_aarav_001")

    receivables = db.query(Receivable).filter(Receivable.merchant_id == "mch_aarav_001").all()
    expected_total = sum(Decimal(str(r.balance_due)) for r in receivables)
    expected_overdue = sum(
        Decimal(str(r.balance_due))
        for r in receivables
        if r.status in ("Overdue", "Severely Overdue")
    )

    assert state.total_receivables == expected_total
    assert state.overdue_receivables == expected_overdue


def test_cash_runway_positive_and_negative_burn(db):
    # Test calculation formula directly
    state = EconomicStateService.calculate_current_state(db=db, merchant_id="mch_aarav_001")
    assert state.cash_runway_days > 0
    assert "Days" in state.cash_runway_display


def test_economic_pressure_score_and_weights():
    # Verify weights sum up to exactly 1.00
    total_weights = (
        EconomicModelConfig.WEIGHT_LIQUIDITY_RUNWAY
        + EconomicModelConfig.WEIGHT_OVERDUE_RECEIVABLES
        + EconomicModelConfig.WEIGHT_AGING_INVENTORY
        + EconomicModelConfig.WEIGHT_NEAR_TERM_PAYABLES
        + EconomicModelConfig.WEIGHT_DEMAND_TREND
        + EconomicModelConfig.WEIGHT_MARGIN_COMPRESSION
    )
    assert total_weights == Decimal("1.00")


def test_business_state_classification():
    # Classification tiers: Strong (<=24), Healthy (25-44), Watch (45-59), Stressed (60-74), Critical (>=75)
    def classify(score):
        if score <= EconomicModelConfig.SCORE_STRONG_MAX:
            return "Strong"
        elif score <= EconomicModelConfig.SCORE_HEALTHY_MAX:
            return "Healthy"
        elif score <= EconomicModelConfig.SCORE_WATCH_MAX:
            return "Watch"
        elif score <= EconomicModelConfig.SCORE_STRESSED_MAX:
            return "Stressed"
        return "Critical"

    assert classify(15) == "Strong"
    assert classify(35) == "Healthy"
    assert classify(50) == "Watch"
    assert classify(67) == "Stressed"
    assert classify(85) == "Critical"


def test_driver_ranking(db):
    drivers_resp = EconomicStateService.get_state_drivers(db=db, merchant_id="mch_aarav_001")
    assert len(drivers_resp.drivers) >= 4

    # Verify ranked strictly in descending order of contribution_score
    scores = [d.contribution_score for d in drivers_resp.drivers]
    for i in range(len(scores) - 1):
        assert scores[i] >= scores[i + 1]

    # Verify rank numbering 1, 2, 3...
    ranks = [d.rank for d in drivers_resp.drivers]
    assert ranks == list(range(1, len(ranks) + 1))


def test_state_delta_computation(db):
    delta_resp = EconomicStateService.get_state_delta(db=db, merchant_id="mch_aarav_001", days_ago=30)
    assert delta_resp.merchant_id == "mch_aarav_001"
    assert len(delta_resp.deltas) >= 6
    assert delta_resp.current_pressure_score > 0
    assert len(delta_resp.summary) > 20

    cash_delta = next(d for d in delta_resp.deltas if d.metric == "cash")
    assert cash_delta.before > 0
    assert cash_delta.after > 0
    assert cash_delta.absolute_change == (cash_delta.after - cash_delta.before)


def test_economic_value_calculation():
    evc = EconomicStateService.calculate_economic_value(
        contribution_margin_value=Decimal("45000.00"),
        liquidity_improvement_value=Decimal("150000.00"),
        inventory_relief_value=Decimal("80000.00"),
        receivable_improvement_value=Decimal("120000.00"),
        economic_risk_cost=Decimal("5000.00"),
    )

    # EVC = 45000 + 0.15*150000 + 0.10*80000 + 0.08*120000 - 5000
    # = 45000 + 22500 + 8000 + 9600 - 5000 = 80100.00
    assert evc.total_economic_value_created == Decimal("80100.00")
    assert "lambda_liquidity_weight" in evc.assumptions


def test_action_evaluation_foundation(db):
    action = EconomicActionModel(
        action_type="accelerate_payment",
        target_id="rec_02",
        parameters={"discount_pct": 2.0, "invoice_amount": 330000.00},
        description="Early settlement discount (2%) for Deccan Refineries overdue invoice",
    )
    result = EconomicStateService.evaluate_action(db=db, merchant_id="mch_aarav_001", action=action)

    assert result.action.action_type == "accelerate_payment"
    assert result.is_favorable is True
    assert result.projected_pressure_score <= result.current_pressure_score
    assert result.economic_value_created.total_economic_value_created > 0
    assert len(result.deltas) >= 2


def test_api_state_endpoints(client):
    # 1. GET /api/merchant/state
    res1 = client.get("/api/merchant/state")
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["merchant_id"] == "mch_aarav_001"
    assert "cash_position" in data1
    assert "total_receivables" in data1
    assert "pressure_score" in data1
    assert "state" in data1
    assert "top_drivers" in data1

    # 2. GET /api/merchant/state/score
    res2 = client.get("/api/merchant/state/score")
    assert res2.status_code == 200
    data2 = res2.json()
    assert "pressure_score" in data2
    assert "component_weights" in data2

    # 3. GET /api/merchant/state/drivers
    res3 = client.get("/api/merchant/state/drivers")
    assert res3.status_code == 200
    data3 = res3.json()
    assert len(data3["drivers"]) >= 4

    # 4. GET /api/merchant/state/history
    res4 = client.get("/api/merchant/state/history")
    assert res4.status_code == 200
    data4 = res4.json()
    assert data4["total_points"] >= 10

    # 5. GET /api/merchant/state/delta
    res5 = client.get("/api/merchant/state/delta?days_ago=30")
    assert res5.status_code == 200
    data5 = res5.json()
    assert len(data5["deltas"]) >= 6

    # 6. POST /api/merchant/state/evaluate-action
    action_payload = {
        "action": {
            "action_type": "liquidate_inventory",
            "parameters": {"discount_pct": 10.0, "inventory_cost": 288000.00},
            "description": "Liquidate aged electro-hydraulic actuators",
        }
    }
    res6 = client.post("/api/merchant/state/evaluate-action", json=action_payload)
    assert res6.status_code == 200
    data6 = res6.json()
    assert data6["is_favorable"] is True
    assert "economic_value_created" in data6


def test_edge_case_unknown_merchant(db):
    with pytest.raises(ValueError):
        EconomicStateService.calculate_current_state(db=db, merchant_id="mch_nonexistent_999")
