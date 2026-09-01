# Razorpay Test Mode & Settlement Integration

## 1. Overview

The **Merchant Liquidity Engine (MLE)** closes the loop between autonomous AI multi-agent negotiation and real-world commercial transaction execution via **Razorpay Test Mode**. 

When an AI Buyer Agent and Merchant Agent reach an `ACCEPTED` commercial agreement, the transaction is executed against the Razorpay sandbox payment gateway. Upon cryptographic payment signature verification, the backend atomically mutates warehouse inventory, settles cash/receivables, and recalculates the Merchant Economic Twin to reflect the realized balance sheet impact.

```
┌───────────────────────────┐
│   ACCEPTED NEGOTIATION    │
└─────────────┬─────────────┘
              │
              ▼
┌───────────────────────────┐
│  RAZORPAY TEST ORDER      │ (POST /api/payments/orders - Server Derived Amount)
└─────────────┬─────────────┘
              │
              ▼
┌───────────────────────────┐
│     RAZORPAY CHECKOUT     │ (checkout.js Modal / Sandbox Test Mode)
└─────────────┬─────────────┘
              │
              ▼
┌───────────────────────────┐
│   SIGNATURE VERIFICATION  │ (POST /api/payments/verify - HMAC-SHA256)
└─────────────┬─────────────┘
              │
              ▼
┌───────────────────────────┐
│   ATOMIC DB TRANSACTION   │
│   ├── Mark Order PAID     │
│   ├── Create Transaction  │
│   ├── Decrement Stock     │
│   ├── Update Cash/AR      │
│   └── New Snapshot / Event│
└─────────────┬─────────────┘
              │
              ▼
┌───────────────────────────┐
│   BEFORE → AFTER TWIN     │ (Projected vs Realized Balance Sheet Comparison)
└───────────────────────────┘
```

---

## 2. Environment Configuration & Security Boundary

### Backend Configuration (`.env`)
```bash
# Razorpay Test Mode Credentials
# Obtain from: https://dashboard.razorpay.com/app/keys (Select 'Test Mode')
RAZORPAY_KEY_ID="rzp_test_your_key_id_here"
RAZORPAY_KEY_SECRET="your_test_secret_key_here"
RAZORPAY_WEBHOOK_SECRET="your_webhook_secret_here"
RAZORPAY_TEST_MODE=True
```

### Security Guardrails
1. **Zero Secret Exposure to Client**: `RAZORPAY_KEY_SECRET` and `RAZORPAY_WEBHOOK_SECRET` are strictly kept on the backend. Only the public `RAZORPAY_KEY_ID` is provided to the client for initializing the checkout modal.
2. **Server-Authoritative Amounts**: The frontend never supplies or controls the payment amount. The backend strictly computes `amount_paise = int(offer.gross_value * 100)` directly from the immutable accepted offer.
3. **Cryptographic HMAC-SHA256 Verification**: Payments are never settled on the client-side callback alone. The server calculates `hmac.new(key=RAZORPAY_KEY_SECRET, msg=f"{order_id}|{payment_id}", digestmod=sha256)` and compares digests.
4. **State Machine Invariants**: Unverified payments, simulation runs, or rejected negotiations can never mutate inventory, cash, or economic twin state.

---

## 3. Payment Order Creation

**Endpoint**: `POST /api/payments/orders`  
**Payload**: `{"negotiation_id": "neg_..."}`

### Execution Logic:
1. Validates that the negotiation session exists and is in `ACCEPTED` status.
2. Validates that the negotiation has not already been paid.
3. Verifies that warehouse inventory has sufficient `available_quantity` for the ordered product.
4. Captures the pre-deal baseline snapshot (`before_state_json`).
5. Calls Razorpay API (`client.order.create`) with `amount_paise`, currency (`INR`), receipt (`MLE-...`), and notes.
6. Persists internal `PaymentOrder` record with status `CREATED`.
7. Returns safe checkout parameters to the frontend.

---

## 4. Razorpay Checkout Flow

The frontend dynamically loads Razorpay's `checkout.js` script and initializes the standard Razorpay checkout modal:

```typescript
const options = {
  key: order.razorpay_key_id,
  amount: order.amount_paise,
  currency: order.currency,
  name: order.merchant_name,
  description: `Payment for ${order.quantity}x ${order.product_name} (${order.receipt})`,
  order_id: order.razorpay_order_id,
  handler: async (response) => {
    // Submit cryptographic response to backend verification
    await verifyPayment({
      payment_order_id: order.id,
      razorpay_order_id: response.razorpay_order_id,
      razorpay_payment_id: response.razorpay_payment_id,
      razorpay_signature: response.razorpay_signature,
    });
  }
};
```

---

## 5. Payment Verification & Real-Time Atomic Settlement

**Endpoint**: `POST /api/payments/verify`  
**Payload**:
```json
{
  "payment_order_id": "pay_ord_...",
  "razorpay_order_id": "order_...",
  "razorpay_payment_id": "pay_...",
  "razorpay_signature": "..."
}
```

### Atomic Database Mutations:
1. **HMAC Signature Check**: Cryptographically validates the signature using the server's `RAZORPAY_KEY_SECRET`.
2. **Idempotency**: If the order is already marked `PAID`, returns the existing settled state without re-executing mutations.
3. **Warehouse Stock Decrement**: Decrements `InventoryItem.available_quantity` by `offer.quantity` and adjusts status tags (`Critical`, `Watch`, `Healthy`).
4. **Transaction Logging**: Creates formal `Transaction` linked with `payment_order_id`, `razorpay_payment_id`, and `source="agentic_negotiation"`.
5. **Ledger Update**:
   - **Immediate Payment (0 days)**: Cash position increases by `gross_amount`.
   - **Deferred Payment (>0 days)**: New `Receivable` is created with due date.
   - **Aging Inventory Relief**: Aging stock is relieved if item aged >30 days.
6. **Economic Twin Snapshot**: Generates new `EconomicSnapshot` with updated Working Capital, Quick Ratio, Current Ratio, Cash Runway, and Pressure Score.
7. **Activity Event**: Logs positive liquidity event in the activity stream.

---

## 6. Webhooks & Idempotency Protection

**Endpoints**:
- `POST /api/webhooks/razorpay`
- `POST /api/payments/razorpay/webhook`

### Header:
`X-Razorpay-Signature: <HMAC-SHA256-hex>`

### Idempotent Event Handling:
1. **Signature Verification**: Verifies raw request body against `RAZORPAY_WEBHOOK_SECRET`.
2. **Deduplication**: Checks `PaymentWebhookLog` table by `event_id`. If already processed, immediately responds with `status: "duplicate_ignored"`.
3. **Event Execution**:
   - `order.paid` / `payment.captured`: Triggers payment verification and atomic state realization if not already completed.
   - `payment.failed`: Logs audit event without touching merchant balance sheet.
4. **Audit Logging**: Persists immutable event record in `payment_webhook_logs`.

---

## 7. Projected vs Realized Outcome

Before execution, Phase 3 and Phase 4 compute **Projected Economic Value Created (EVC)**:
$$\text{Projected EVC} = 0.35 \times \text{Margin} + 0.25 \times \text{Cash Velocity} + 0.15 \times \text{Aging Relief}$$

After verified payment execution, the backend computes **Realized EVC** from the actual balance sheet delta and returns a detailed comparison:

| Metric | Pre-Deal (Before) | Realized (After) | Delta | Direction |
|---|---|---|---|---|
| Liquid Cash Position | ₹4,85,000 | ₹8,45,000 | +₹3,60,000 | Favorable |
| Inventory Valuation | ₹12,40,000 | ₹9,85,000 | -₹2,55,000 | Neutral |
| Aging Inventory Relieved | ₹5,80,000 | ₹3,25,000 | -₹2,55,000 | Favorable |
| Cash Runway | 42 days | 71 days | +29 days | Favorable |
| Liquidity Pressure Score | 58 / 100 | 44 / 100 | -14 pts | Favorable |

---

## 8. Failure Modes Handled

- **Missing / Unconfigured Credentials**: Falls back safely to deterministic sandbox test order creation.
- **SDK Load Failure**: Falls back to internal test mode simulation modal so development & demo never halt.
- **Forged Payment Signature**: Request rejected with `400 Bad Request` and `PaymentOrder` marked `FAILED`.
- **Duplicate Verification / Webhook Replay**: Handled idempotently; returns existing completed state without duplicate stock decrements.
- **Unaccepted / In-Progress Negotiation**: Blocked from payment order creation with descriptive HTTP 400 error.
- **Stock Depletion**: Blocked at order creation time if requested quantity exceeds warehouse stock.
