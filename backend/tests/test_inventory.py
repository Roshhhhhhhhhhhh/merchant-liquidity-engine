def test_get_inventory(client):
    response = client.get("/api/inventory")
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "items" in data
    assert data["summary"]["total_skus"] >= 10
    assert float(data["summary"]["total_inventory_value"]) > 0
    assert len(data["summary"]["category_breakdown"]) > 0
    assert len(data["items"]) == data["summary"]["total_skus"]


def test_get_inventory_filter_by_status(client):
    response = client.get("/api/inventory?status=Aging")
    assert response.status_code == 200
    data = response.json()
    for item in data["items"]:
        assert item["status"] == "Aging"


def test_get_products(client):
    response = client.get("/api/inventory/products")
    assert response.status_code == 200
    products = response.json()
    assert len(products) >= 10
    skus = [p["sku"] for p in products]
    assert "VAL-GS-004" in skus
