import requests
import json

BASE_URL = "http://localhost:8000/api"

def run_test():
    print("1. Testing Health Endpoint...")
    res = requests.get(f"{BASE_URL}/health")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    print(f"   -> Health OK: {res.json()}")

    print("\n2. Running Demo Autonomous Negotiation Scenario...")
    res = requests.post(f"{BASE_URL}/agent/negotiations/demo", json={})
    assert res.status_code == 200, f"Demo failed: {res.text}"
    session = res.json()
    negotiation_id = session["id"]
    offer = session["current_offer"]
    print(f"   -> Negotiation ID: {negotiation_id}")
    print(f"   -> Status: {session['status']}")
    print(f"   -> Accepted Offer Gross Value: INR {offer['gross_value']} ({offer['quantity']} units of {offer['product_name']})")
    print(f"   -> Projected EVC: INR {offer['economic_value']}")

    print("\n3. Creating Razorpay Test Mode Payment Order...")
    res = requests.post(f"{BASE_URL}/payments/orders", json={"negotiation_id": negotiation_id})
    assert res.status_code == 200, f"Create payment order failed: {res.text}"
    pay_order = res.json()
    payment_order_id = pay_order["id"]
    razorpay_order_id = pay_order["razorpay_order_id"]
    print(f"   -> Payment Order ID: {payment_order_id}")
    print(f"   -> Razorpay Order ID: {razorpay_order_id}")
    print(f"   -> Amount (Paise): {pay_order['amount_paise']} paise ({pay_order['amount_formatted']})")
    print(f"   -> Status: {pay_order['status']}")

    print("\n4. Executing Payment Verification with HMAC Signature...")
    verify_payload = {
        "payment_order_id": payment_order_id,
        "razorpay_order_id": razorpay_order_id,
        "razorpay_payment_id": f"pay_live_test_{payment_order_id[-8:]}",
        "razorpay_signature": "mock_valid_test_signature",
    }
    res = requests.post(f"{BASE_URL}/payments/verify", json=verify_payload)
    assert res.status_code == 200, f"Payment verify failed: {res.text}"
    verify_data = res.json()
    print(f"   -> Status: {verify_data['status']}")
    print(f"   -> Transaction ID: {verify_data['transaction_id']}")
    print(f"   -> Transaction Reference: {verify_data['reference_id']}")
    print(f"   -> Projected EVC: {verify_data['projected_evc_formatted']} | Realized EVC: {verify_data['realized_evc_formatted']}")
    print(f"   -> EVC Variance: {verify_data['evc_variance_formatted']}")
    print("\n5. Balance Sheet Transition Metrics (Before -> After):")
    for m in verify_data["metrics_comparison"]:
        print(f"   - {m['metric']:<26}: {m['before_formatted']} -> {m['after_formatted']} (Delta: {m['delta_formatted']}) [{m['direction']}]")

    print("\n6. Verifying Transaction Appears in Ledger Endpoint...")
    res = requests.get(f"{BASE_URL}/transactions")
    assert res.status_code == 200, f"Transactions fetch failed: {res.text}"
    tx_list = res.json()
    matched_tx = next((t for t in tx_list["items"] if t["id"] == verify_data["transaction_id"]), None)
    assert matched_tx is not None, "Newly created transaction not found in ledger list!"
    print(f"   -> Found Transaction in Ledger: {matched_tx['reference_id']}")
    print(f"   -> Source: {matched_tx['source']}")
    print(f"   -> Payment Method: {matched_tx['payment_method']}")
    print(f"   -> Razorpay Payment ID: {matched_tx['razorpay_payment_id']}")

    print("\n7. Testing Razorpay Webhook Idempotency...")
    webhook_payload = {
        "id": "evt_live_test_webhook_idempotency_123",
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": f"pay_live_test_{payment_order_id[-8:]}",
                    "order_id": razorpay_order_id,
                    "amount": pay_order["amount_paise"],
                    "status": "captured",
                }
            }
        }
    }
    headers = {"X-Razorpay-Signature": "mock_valid_webhook_signature"}
    res1 = requests.post(f"{BASE_URL}/payments/razorpay/webhook", json=webhook_payload, headers=headers)
    assert res1.status_code == 200
    print(f"   -> Webhook 1 Result: {res1.json()['status']} (Processed: {res1.json()['processed']})")

    res2 = requests.post(f"{BASE_URL}/payments/razorpay/webhook", json=webhook_payload, headers=headers)
    assert res2.status_code == 200
    print(f"   -> Webhook 2 (Replay) Result: {res2.json()['status']} (Processed: {res2.json()['processed']})")
    assert res2.json()["status"] == "duplicate_ignored", "Webhook idempotency failed!"

    print("\n=======================================================")
    print("ALL PHASE 5 END-TO-END VERIFICATION CHECKS PASSED 100%!")
    print("=======================================================")

if __name__ == "__main__":
    run_test()
