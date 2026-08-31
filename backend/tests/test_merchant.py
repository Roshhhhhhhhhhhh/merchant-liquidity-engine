def test_get_merchant(client):
    response = client.get("/api/merchant")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "mch_aarav_001"
    assert "Aarav Industrial Supplies" in data["trade_name"]
    assert data["gst_number"] == "27AAACA1234F1Z8"
    assert data["base_currency"] == "INR"


def test_get_merchant_state(client):
    response = client.get("/api/merchant/state")
    assert response.status_code == 200
    data = response.json()
    assert data["merchant_id"] == "mch_aarav_001"
    assert "liquidity_stress_score" in data
    assert data["liquidity_status"] in ["Healthy", "Watch", "Warning", "Critical"]
    assert len(data["drivers"]) >= 3
    assert "cash" in data
    assert "receivables" in data
    assert "payables" in data
    assert "inventory_value" in data
    assert "aging_inventory" in data
    assert "gross_margin" in data
    assert "demand_trend" in data
    assert "customer_value" in data
    assert "fulfillment_capacity" in data
    assert "cash_runway" in data
    assert "working_capital" in data
