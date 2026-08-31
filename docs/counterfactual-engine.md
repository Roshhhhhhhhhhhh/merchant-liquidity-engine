# Counterfactual Economic Simulator — Architecture & Specification

## 1. Core Principle
The **Merchant Liquidity Engine** treats every proposed commercial transaction not as an isolated revenue event, but as a **future economic state transition** of the merchant.

$$\text{Current Merchant State } S_0 + \text{Proposed Commercial Deal } D_k \xrightarrow{\text{In-Memory Engine}} \text{Counterfactual Future State } S'_k$$

The simulator guarantees:
- **Zero Ledger Mutation**: Simulation calculations are strictly in-memory and read-only with respect to the merchant's financial books (`receivables`, `payables`, `inventory_items`, `transactions`).
- **Deterministic Reproducibility**: Given identical state $S_0$ and deal parameters, the simulator produces identical candidate rankings and projected metrics.
- **True Economic Optimization**: Evaluates total balance sheet utility, ensuring higher nominal revenue with delayed payment does not automatically beat lower-price cash settlement with aging inventory liquidation.

---

## 2. Mathematical Modeling

### 2.1 Balance Sheet State Transition Functions
Given $S_0 = (C_0, R_0, I_0, I_{\text{aging}, 0}, P_0, K_0)$ and Deal $D = (Q, P_{\text{unit}}, C_{\text{unit}}, T_{\text{pay}}, T_{\text{del}})$:

1. **Cash Flow ($C$)**:
   $$C' = \begin{cases} C_0 + (Q \times P_{\text{unit}}) & \text{if } T_{\text{pay}} = 0 \\ C_0 & \text{if } T_{\text{pay}} > 0 \end{cases}$$

2. **Receivables Book ($R$)**:
   $$R' = \begin{cases} R_0 & \text{if } T_{\text{pay}} = 0 \\ R_0 + (Q \times P_{\text{unit}}) & \text{if } T_{\text{pay}} > 0 \end{cases}$$

3. **Inventory Valuation ($I$) & Aging Stock Relief ($I_{\text{aging}}$)**:
   $$I' = \max(0, I_0 - (Q \times C_{\text{unit}}))$$
   $$I'_{\text{aging}} = \max(0, I_{\text{aging}, 0} - \Delta I_{\text{aging}})$$

4. **Capacity Load ($K_{\text{ful}}$)**:
   $$\Delta K = \frac{Q}{\text{Max Daily Capacity} \times T_{\text{del}}} \times 100\%$$
   $$K' = \min(100\%, K_0 + 0.25 \times \Delta K)$$

5. **Days of Inventory Coverage ($D_{\text{cov}}$)**:
   $$D_{\text{cov}} = \frac{Q_{\text{remain}}}{D_{\text{daily}}}$$

---

### 2.2 Objective Function: Economic Value Created ($EVC$)
$$\begin{aligned}
EVC = & \; w_{\text{contrib}} \cdot CM \\
& + w_{\text{liq}} \cdot \text{LiquidityValue} \\
& + w_{\text{inv}} \cdot \text{InventoryRelief} \\
& + w_{\text{rec}} \cdot \text{ReceivableBenefit} \\
& - w_{\text{risk}} \cdot \text{RiskCost} \\
& - w_{\text{cap}} \cdot \text{CapacityCost} \\
& - w_{\text{stockout}} \cdot \text{StockoutCost}
\end{aligned}$$

#### Default Objective Weights
| Parameter | Weight | Description |
|:---|:---:|:---|
| $w_{\text{contrib}}$ | **0.35** | Contribution Margin / Gross Profit |
| $w_{\text{liq}}$ | **0.25** | Immediate liquid cash unlocked |
| $w_{\text{inv}}$ | **0.15** | Working capital liberated from aging stock (>45d) |
| $w_{\text{rec}}$ | **0.10** | Receivable cycle / DSO acceleration |
| $w_{\text{risk}}$ | **0.10** | Carrying friction and credit default risk |
| $w_{\text{cap}}$ | **0.05** | Overload penalty above 85% capacity |
| $w_{\text{stockout}}$ | **0.05** | Opportunity cost of sub-7-day inventory coverage |

---

## 3. Four-Way Deal Candidate Generator

When an inquiry is received, the generator algorithmically produces 4 distinct commercial options:

1. **Deal A • Standard Terms**:
   - 100% of requested quantity
   - 0% discount (full catalog price)
   - Standard 30-day deferred trade credit
2. **Deal B • Cash Acceleration**:
   - 100% of requested quantity
   - 4% prompt payment discount
   - 0-day immediate payment (UPI / Instant Razorpay settlement)
3. **Deal C • Volume Maximizer**:
   - +15% expanded volume
   - 6.5% volume discount
   - Short 7-day accelerated terms
4. **Deal D • Aging Stock Clearance**:
   - 100% of requested quantity (targeted at aging SKUs)
   - 9% clearance discount
   - 0-day immediate settlement

---

## 4. API Endpoints

### 4.1 Run Counterfactual Simulation
`POST /api/scenarios/simulate`
```json
{
  "scenario_name": "Inquiry: 250 units Valves",
  "request": {
    "requested_quantity": 250,
    "target_budget": 320000.00,
    "max_delivery_days": 5,
    "preferred_payment_timing_days": 0
  },
  "constraints": {
    "min_margin_pct": 12.0,
    "max_credit_days": 30,
    "allow_aging_clearance_bonus": true
  }
}
```

### 4.2 List Historical Scenarios
`GET /api/scenarios`

### 4.3 Get Detailed Scenario by ID
`GET /api/scenarios/{scenario_id}`

### 4.4 Generate Candidate Previews
`POST /api/scenarios/deals/generate`
