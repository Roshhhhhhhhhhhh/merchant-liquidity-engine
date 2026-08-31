import datetime
from decimal import Decimal
import pytest
from app.services.economic_state_service import EconomicStateService
from app.services.counterfactual_service import CounterfactualStateService
from app.services.deal_generator import DealCandidateGenerator
from app.services.deal_optimizer import DealOptimizationService
from app.services.scenario_service import ScenarioService
from app.schemas.scenario import BuyerRequestModel, MerchantConstraintsModel
from app.models import Product, InventoryItem, Receivable, Payable, Scenario, ScenarioCandidate


def test_deal_validation_constraints(db):
    current_state = EconomicStateService.calculate_current_state(db=db, merchant_id="mch_aarav_001")
    prod = db.query(Product).first()

    # Zero/negative quantity should raise ValueError
    with pytest.raises(ValueError):
        CounterfactualStateService.simulate_deal(
            db=db,
            merchant_id="mch_aarav_001",
            current_state=current_state,
            product_id=prod.id,
            quantity=0,
            unit_price=Decimal("1000.00"),
        )

    with pytest.raises(ValueError):
        CounterfactualStateService.simulate_deal(
            db=db,
            merchant_id="mch_aarav_001",
            current_state=current_state,
            product_id=prod.id,
            quantity=-10,
            unit_price=Decimal("1000.00"),
        )


def test_inventory_and_aging_projection(db):
    current_state = EconomicStateService.calculate_current_state(db=db, merchant_id="mch_aarav_001")
    prod = db.query(Product).first()
    unit_cost = Decimal(str(prod.unit_cost))
    qty = 50

    res = CounterfactualStateService.simulate_deal(
        db=db,
        merchant_id="mch_aarav_001",
        current_state=current_state,
        product_id=prod.id,
        quantity=qty,
        unit_price=Decimal("1200.00"),
        target_aging_reduction_units=30,
    )

    assert res["inventory_impact"] == Decimal(qty) * unit_cost
    assert res["projected_inventory"] == current_state.inventory_valuation - (Decimal(qty) * unit_cost)
    assert res["aging_inventory_impact"] == Decimal(30) * unit_cost
    assert res["projected_aging_inventory"] == current_state.aging_inventory_value - (Decimal(30) * unit_cost)


def test_cash_vs_receivable_timing_difference(db):
    current_state = EconomicStateService.calculate_current_state(db=db, merchant_id="mch_aarav_001")
    prod = db.query(Product).first()
    qty = 100
    price = Decimal("1000.00")
    total_val = Decimal("100000.00")

    # Deal 1: Immediate payment (0 days)
    res_immediate = CounterfactualStateService.simulate_deal(
        db=db,
        merchant_id="mch_aarav_001",
        current_state=current_state,
        product_id=prod.id,
        quantity=qty,
        unit_price=price,
        payment_timing_days=0,
    )

    # Deal 2: 30-day deferred credit
    res_deferred = CounterfactualStateService.simulate_deal(
        db=db,
        merchant_id="mch_aarav_001",
        current_state=current_state,
        product_id=prod.id,
        quantity=qty,
        unit_price=price,
        payment_timing_days=30,
    )

    # Immediate should add to cash, not receivables
    assert res_immediate["cash_impact"] == total_val
    assert res_immediate["receivable_impact"] == Decimal("0.00")
    assert res_immediate["projected_cash"] == current_state.cash_position + total_val
    assert res_immediate["projected_receivables"] == current_state.total_receivables

    # Deferred should add to receivables, not cash
    assert res_deferred["cash_impact"] == Decimal("0.00")
    assert res_deferred["receivable_impact"] == total_val
    assert res_deferred["projected_cash"] == current_state.cash_position
    assert res_deferred["projected_receivables"] == current_state.total_receivables + total_val

    # Immediate deal should have lower or equal projected pressure score
    assert res_immediate["projected_pressure_score"] <= res_deferred["projected_pressure_score"]


def test_capacity_impact_and_stockout_risk(db):
    current_state = EconomicStateService.calculate_current_state(db=db, merchant_id="mch_aarav_001")
    prod = db.query(Product).first()

    # Large lot size in short delivery window
    res_high_load = CounterfactualStateService.simulate_deal(
        db=db,
        merchant_id="mch_aarav_001",
        current_state=current_state,
        product_id=prod.id,
        quantity=300,
        unit_price=Decimal("1000.00"),
        delivery_days=2,
    )

    assert res_high_load["capacity_impact_pct"] > 0
    assert res_high_load["days_inventory_coverage"] >= 0
    assert res_high_load["stockout_risk"] in ("Low", "Moderate", "Constrained", "Critical")


def test_economic_value_created_transparency(db):
    current_state = EconomicStateService.calculate_current_state(db=db, merchant_id="mch_aarav_001")
    prod = db.query(Product).first()
    price = Decimal(str(prod.current_price))

    sim = CounterfactualStateService.simulate_deal(
        db=db,
        merchant_id="mch_aarav_001",
        current_state=current_state,
        product_id=prod.id,
        quantity=100,
        unit_price=price,
        payment_timing_days=0,
        target_aging_reduction_units=40,
    )

    evc, breakdown = DealOptimizationService.calculate_economic_value(sim)

    assert breakdown.total_economic_value_created == evc
    assert breakdown.contribution_margin_value > 0
    assert breakdown.liquidity_improvement_value > 0
    assert breakdown.inventory_relief_value > 0
    assert "w_contribution" in breakdown.weights_used


def test_tradeoff_immediate_cash_and_aging_beats_deferred_revenue(db):
    """
    CRITICAL TRADE-OFF TEST:
    A deal with lower nominal revenue but immediate cash and aging inventory liquidation
    MUST produce higher Economic Value Created (EVC) than a higher-revenue deal with 30-day delayed credit!
    """
    current_state = EconomicStateService.calculate_current_state(db=db, merchant_id="mch_aarav_001")
    prod = db.query(Product).first()

    # Deal High Rev / 30d credit: 100 units @ 1100 = ₹110,000, 30-day payment, 0 aging relief
    deal_high_rev = CounterfactualStateService.simulate_deal(
        db=db,
        merchant_id="mch_aarav_001",
        current_state=current_state,
        product_id=prod.id,
        quantity=100,
        unit_price=Decimal("1100.00"),
        payment_timing_days=30,
        target_aging_reduction_units=0,
    )
    evc_high_rev, _ = DealOptimizationService.calculate_economic_value(deal_high_rev)

    # Deal Liquidity & Aging Clearance: 100 units @ 1020 = ₹102,000, 0-day immediate payment, 80 units aging relief
    deal_liquidity = CounterfactualStateService.simulate_deal(
        db=db,
        merchant_id="mch_aarav_001",
        current_state=current_state,
        product_id=prod.id,
        quantity=100,
        unit_price=Decimal("1020.00"),
        payment_timing_days=0,
        target_aging_reduction_units=80,
    )
    evc_liquidity, _ = DealOptimizationService.calculate_economic_value(deal_liquidity)

    # Nominal gross revenue of deal_high_rev (110k) > deal_liquidity (102k)
    assert deal_high_rev["gross_value"] > deal_liquidity["gross_value"]

    # BUT Economic Value Created of deal_liquidity MUST be higher!
    assert evc_liquidity > evc_high_rev
    assert deal_liquidity["projected_pressure_score"] <= deal_high_rev["projected_pressure_score"]


def test_candidate_generation_deterministic(db):
    current_state = EconomicStateService.calculate_current_state(db=db, merchant_id="mch_aarav_001")
    request = BuyerRequestModel(
        requested_quantity=300,
        target_budget=Decimal("360000.00"),
        max_delivery_days=6,
        preferred_payment_timing_days=0,
    )
    constraints = MerchantConstraintsModel()

    candidates1 = DealCandidateGenerator.generate_candidates(
        db=db,
        merchant_id="mch_aarav_001",
        current_state=current_state,
        request=request,
        constraints=constraints,
    )
    candidates2 = DealCandidateGenerator.generate_candidates(
        db=db,
        merchant_id="mch_aarav_001",
        current_state=current_state,
        request=request,
        constraints=constraints,
    )

    assert len(candidates1) == 4
    # Deterministic identity verification
    for c1, c2 in zip(candidates1, candidates2):
        assert c1["id"] == c2["id"]
        assert c1["unit_price"] == c2["unit_price"]
        assert c1["quantity"] == c2["quantity"]


def test_scenario_service_end_to_end_and_db_immutability(db):
    # Record baseline state before simulation
    rec_count_before = db.query(Receivable).count()
    inv_count_before = db.query(InventoryItem).count()
    pay_count_before = db.query(Payable).count()

    request = BuyerRequestModel(
        requested_quantity=200,
        target_budget=Decimal("250000.00"),
        max_delivery_days=5,
        preferred_payment_timing_days=0,
    )

    response = ScenarioService.simulate_scenario(
        db=db,
        merchant_id="mch_aarav_001",
        request=request,
        scenario_name="Automated Test Scenario Run",
    )

    assert response.scenario_id.startswith("scen_")
    assert len(response.candidates) == 4
    assert response.recommended_candidate.is_recommended is True
    assert response.recommended_candidate.rank == 1
    assert len(response.ranking_explanation) > 20

    # Verify candidates are strictly ordered by economic_value descending
    ev_values = [c.economic_value for c in response.candidates]
    for i in range(len(ev_values) - 1):
        assert ev_values[i] >= ev_values[i + 1]

    # Verify scenario was persisted
    saved = db.query(Scenario).filter(Scenario.id == response.scenario_id).first()
    assert saved is not None
    assert len(saved.candidates) == 4

    # CRITICAL: Verify underlying merchant operational ledger was NOT mutated
    assert db.query(Receivable).count() == rec_count_before
    assert db.query(InventoryItem).count() == inv_count_before
    assert db.query(Payable).count() == pay_count_before


def test_api_scenario_endpoints(client):
    # 1. POST /api/scenarios/simulate
    sim_payload = {
        "scenario_name": "API Test Inquiry 300 Units",
        "request": {
            "requested_quantity": 300,
            "target_budget": 360000.00,
            "max_delivery_days": 6,
            "preferred_payment_timing_days": 0,
        }
    }
    res1 = client.post("/api/scenarios/simulate", json=sim_payload)
    assert res1.status_code == 200
    data1 = res1.json()
    assert "scenario_id" in data1
    assert len(data1["candidates"]) == 4
    assert data1["recommended_candidate"]["is_recommended"] is True

    scenario_id = data1["scenario_id"]

    # 2. GET /api/scenarios
    res2 = client.get("/api/scenarios")
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["total_scenarios"] >= 1
    assert any(s["id"] == scenario_id for s in data2["scenarios"])

    # 3. GET /api/scenarios/{id}
    res3 = client.get(f"/api/scenarios/{scenario_id}")
    assert res3.status_code == 200
    data3 = res3.json()
    assert data3["scenario_id"] == scenario_id
    assert len(data3["candidates"]) == 4

    # 4. POST /api/scenarios/deals/generate
    gen_payload = {
        "requested_quantity": 250,
        "target_budget": 300000.00,
        "max_delivery_days": 5,
        "preferred_payment_timing_days": 0,
    }
    res4 = client.post("/api/scenarios/deals/generate", json=gen_payload)
    assert res4.status_code == 200
    data4 = res4.json()
    assert len(data4) == 4
