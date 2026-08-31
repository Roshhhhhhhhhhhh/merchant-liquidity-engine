def test_get_receivables(client):
    response = client.get("/api/receivables")
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "items" in data
    assert float(data["summary"]["total_outstanding"]) > 0
    assert float(data["summary"]["total_overdue"]) > 0
    assert len(data["summary"]["aging_buckets"]) == 4
    assert len(data["items"]) > 0


def test_get_customers(client):
    response = client.get("/api/receivables/customers")
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "customers" in data
    assert data["summary"]["total_customers"] >= 5
    assert len(data["customers"]) == data["summary"]["total_customers"]
