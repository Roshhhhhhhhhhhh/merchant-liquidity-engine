def test_get_payables(client):
    response = client.get("/api/payables")
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "items" in data
    assert float(data["summary"]["total_payables"]) > 0
    assert float(data["summary"]["due_within_12_days"]) > 0


def test_get_transactions(client):
    response = client.get("/api/transactions")
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "items" in data
    assert data["summary"]["total_transactions"] >= 15
    assert float(data["summary"]["total_gross_volume"]) > 0


def test_get_snapshots(client):
    response = client.get("/api/snapshots")
    assert response.status_code == 200
    data = response.json()
    assert data["total_points"] >= 10
    assert len(data["data"]) == data["total_points"]
    assert len(data["recent_snapshots"]) > 0


def test_get_activity(client):
    response = client.get("/api/activity")
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "events" in data
    assert data["summary"]["total_events"] >= 5
