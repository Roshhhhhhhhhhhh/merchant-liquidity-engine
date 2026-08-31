import sys
import os

# Set UTF-8 output encoding for windows console
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import httpx

BASE_URL = "http://127.0.0.1:8000/api"
FRONTEND_URL = "http://127.0.0.1:5173"

def test_backend_endpoints():
    print("\n--- Testing Backend API Endpoints ---")
    with httpx.Client(timeout=10) as client:
        # 1. Health
        res = client.get(f"{BASE_URL}/health")
        print(f"GET /api/health -> {res.status_code}: {res.json()['status']}")
        assert res.status_code == 200

        # 2. Merchant
        res = client.get(f"{BASE_URL}/merchant")
        print(f"GET /api/merchant -> {res.status_code}: {res.json()['name']}")
        assert res.status_code == 200

        # 3. Merchant State (10 Dimensions + Outlook)
        res = client.get(f"{BASE_URL}/merchant/state")
        data = res.json()
        print(f"GET /api/merchant/state -> {res.status_code}")
        print(f"  Liquidity Stress Score: {data['liquidity_stress_score']}/100 ({data['liquidity_status']})")
        print(f"  Outlook Headline: {data['liquidity_outlook_headline']}")
        print(f"  Cash Runway: {data['cash_runway']['formatted_value']}")
        print(f"  Working Capital: {data['working_capital_formatted']}")
        print(f"  Primary Drivers Count: {len(data['drivers'])}")
        assert res.status_code == 200
        assert data['liquidity_stress_score'] == 68
        assert data['liquidity_status'] == 'Warning'

        # 4. Inventory
        res = client.get(f"{BASE_URL}/inventory")
        inv = res.json()
        print(f"GET /api/inventory -> {res.status_code}")
        print(f"  Total SKUs: {inv['summary']['total_skus']}")
        print(f"  Inventory Value: {inv['summary']['total_inventory_value_formatted']}")
        print(f"  Aging Value: {inv['summary']['total_aging_value_formatted']} ({inv['summary']['aging_pct']}%)")
        assert res.status_code == 200
        assert inv['summary']['total_skus'] == 14

        # 5. Receivables
        res = client.get(f"{BASE_URL}/receivables")
        rec = res.json()
        print(f"GET /api/receivables -> {res.status_code}")
        print(f"  Total Outstanding: {rec['summary']['total_outstanding_formatted']}")
        print(f"  Total Overdue: {rec['summary']['total_overdue_formatted']}")
        print(f"  Avg DSO: {rec['summary']['average_dso_days']} Days")
        print(f"  Aging Buckets: {len(rec['summary']['aging_buckets'])}")
        assert res.status_code == 200

        # 6. Customers
        res = client.get(f"{BASE_URL}/receivables/customers")
        cust = res.json()
        print(f"GET /api/receivables/customers -> {res.status_code}: {cust['summary']['total_customers']} Customers")
        assert res.status_code == 200

        # 7. Payables
        res = client.get(f"{BASE_URL}/payables")
        pay = res.json()
        print(f"GET /api/payables -> {res.status_code}")
        print(f"  Total Payables: {pay['summary']['total_payables_formatted']}")
        print(f"  Due Within 12 Days: {pay['summary']['due_within_12_days_formatted']}")
        assert res.status_code == 200

        # 8. Transactions
        res = client.get(f"{BASE_URL}/transactions")
        tx = res.json()
        print(f"GET /api/transactions -> {res.status_code}")
        print(f"  Total Transactions: {tx['summary']['total_transactions']}")
        print(f"  Total Volume: {tx['summary']['total_gross_volume_formatted']}")
        print(f"  Avg Realized Margin: {tx['summary']['avg_gross_margin_pct']}%")
        assert res.status_code == 200

        # 9. Snapshots
        res = client.get(f"{BASE_URL}/snapshots")
        snaps = res.json()
        print(f"GET /api/snapshots -> {res.status_code}: {snaps['total_points']} daily trend data points")
        assert res.status_code == 200

        # 10. Activity
        res = client.get(f"{BASE_URL}/activity")
        act = res.json()
        print(f"GET /api/activity -> {res.status_code}: {act['summary']['total_events']} audit events")
        assert res.status_code == 200

def test_frontend_server():
    print("\n--- Testing Frontend Dev Server ---")
    with httpx.Client(timeout=10) as client:
        res = client.get(FRONTEND_URL)
        print(f"GET {FRONTEND_URL} -> {res.status_code}")
        assert res.status_code == 200
        assert "Merchant Liquidity Engine" in res.text
        assert "root" in res.text

if __name__ == "__main__":
    test_backend_endpoints()
    test_frontend_server()
    print("\n>>> ALL RUNTIME HEALTH & INTEGRATION CHECKS PASSED WITH 100% SUCCESS! <<<\n")
