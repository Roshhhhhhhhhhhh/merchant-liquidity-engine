# Merchant Economic Twin & Economic State Engine — Mathematical Specification

> **Version**: 2.0.0 (Phase 2 Architectural Standard)  
> **Status**: Authoritative & Implemented  
> **Target System**: Merchant Liquidity Engine

---

## 1. Executive Summary & Philosophy

The **Merchant Economic Twin** is a deterministic mathematical representation of a merchant's business health and working capital state at any time $t$. 

Unlike conventional financial reporting systems that only show backward-looking static ledgers, the Economic Twin maintains a continuous, multidimensional state model derived directly from live transactional and ledger data.

```
Transactional Ledgers (Invoices, Payables, Orders, Inventory)
                           │
                           ▼
          [ Economic State Engine (Phase 2) ]
          • Pure Decimal/Numeric Precision (14, 2)
          • 10 Continuous Economic Dimensions
          • 0–100 Composite Pressure Score
          • 5-Tier Business Classification
          • Deterministic Driver Ranking (No Hallucinations)
          • Action Evaluation & Economic Value Foundation
                           │
                           ▼
          [ Economic Twin APIs & Operations Console ]
```

---

## 2. Formal Economic State Definition

The merchant state at time $t$ is represented by the 13-tuple:

$$\text{EconomicState}(t) = \left\langle C(t), R(t), R_{\text{overdue}}(t), P(t), P_{\text{near}}(t), I(t), I_{\text{aging}}(t), GM(t), D(t), V_{\text{pay}}(t), CV(t), K_{\text{ful}}(t), \text{Runway}(t) \right\rangle$$

Where:
- $C(t)$: Cash position (immediately available operating bank balance)
- $R(t)$: Total outstanding receivables book
- $R_{\text{overdue}}(t)$: Receivables balance past due date ($status \in \{\text{Overdue}, \text{Severely Overdue}\}$)
- $P(t)$: Total accounts payable book
- $P_{\text{near}}(t)$: Accounts payable maturing within 12 days ($due\_date \le t + 12\text{d}$)
- $I(t)$: Total inventory valuation ($\sum available\_quantity \times unit\_cost$)
- $I_{\text{aging}}(t)$: Aging inventory value ($days\_in\_stock > 45\text{d}$ or $status \in \{\text{Aging}, \text{Critical}\}$)
- $GM(t)$: Rolling 30-day gross margin percentage ($\frac{Revenue - COGS}{Revenue} \times 100$)
- $D(t)$: Demand trend percentage (15-day recent vs preceding 15-day order velocity)
- $V_{\text{pay}}(t)$: Normalized customer payment velocity index ($0.0 \le V_{\text{pay}} \le 1.0$)
- $CV(t)$: Total customer portfolio lifetime value
- $K_{\text{ful}}(t)$: Warehouse and fulfillment throughput capacity percentage ($0 \le K_{\text{ful}} \le 100$)
- $\text{Runway}(t)$: Sustainable cash runway in days based on normalized net daily burn

---

## 3. Financial Precision & Arithmetic Guarantees

All monetary calculations in the engine adhere to strict enterprise fintech standards:
1. **Zero Floating-Point Representation**: Database columns utilize `Numeric(14, 2)`. Python execution paths cast all monetary operands to `decimal.Decimal`.
2. **Explicit Rounding**: All currency and metric rounding uses `ROUND_HALF_UP` (standard financial rounding).
3. **No Division-by-Zero / NaN / Infinity**: Edge cases (zero revenue, zero burn, zero receivables, empty inventory) resolve to bounded mathematical values (e.g. positive cashflow yields a capped 90+ day runway rather than $\infty$).

---

## 4. The 10 Core Economic Dimensions

| Dimension | Domain Metric | Formula / Source | Status Thresholds |
| :--- | :--- | :--- | :--- |
| **1. Cash** | Liquid operating reserves | Latest snapshot cash balance | $\ge \text{₹5.0L}$: Healthy<br>$\text{₹2.5L–5.0L}$: Watch<br>$< \text{₹2.5L}$: Critical |
| **2. Receivables** | Total open invoice ledger | $\sum \text{Receivable.balance\_due}$ | Overdue ratio $< 15\%$: Healthy<br>$15–30\%$: Watch<br>$> 30\%$: Critical |
| **3. Payables** | Total vendor liabilities | $\sum \text{Payable.balance\_due}$ | Near-term ratio $< 30\%$: Healthy<br>$30–50\%$: Watch<br>$> 50\%$: Critical |
| **4. Inventory Value** | Stock capital deployment | $\sum Q_{\text{avail}} \times Cost_{\text{unit}}$ | Category balanced: Healthy |
| **5. Aging Inventory** | Capital locked $>45$ days | $\sum_{d > 45} Q_{\text{avail}} \times Cost_{\text{unit}}$ | Aging ratio $< 15\%$: Healthy<br>$15–30\%$: Watch<br>$> 30\%$: Critical |
| **6. Gross Margin** | Blended 30-day profitability | $\frac{\text{Gross Revenue} - \text{COGS}}{\text{Gross Revenue}} \times 100$ | $\ge 25\%$: Healthy<br>$20–25\%$: Watch<br>$< 20\%$: Critical |
| **7. Demand Trend** | 15d rolling sales trajectory | $\frac{V_{\text{recent 15d}} - V_{\text{prior 15d}}}{V_{\text{prior 15d}}} \times 100$ | $\ge +2\%$: Healthy<br>$-5\% \text{ to } +2\%$: Watch<br>$< -5\%$: Softening |
| **8. Customer Value** | Portfolio reliability & LTV | $\sum \text{Customer.total\_revenue}$ | Avg score $\ge 80$: Healthy<br>$70–79$: Watch<br>$< 70$: Critical |
| **9. Fulfillment Capacity** | Production utilization | Factory throughput capacity | $70–85\%$: Healthy<br>$85–95\%$: Watch<br>$> 95\%$: Critical |
| **10. Cash Runway** | Days of sustainable burn | $\frac{\text{Cash Balance}}{\text{Net Daily Burn}}$ | $\ge 45\text{d}$: Healthy<br>$20–44\text{d}$: Watch<br>$< 20\text{d}$: Critical |

---

## 5. Economic Pressure Score Formulation

The **Economic Pressure Score** is a composite deterministic metric ranging from $0$ (minimal stress, high liquidity) to $100$ (severe liquidity crisis):

$$\text{Pressure Score} = \min\left(100, \max\left(0, \sum_{i=1}^{6} w_i \cdot S_i\right)\right)$$

### Component Weights ($w_i$) and Stress Functions ($S_i$):

$$\sum_{i=1}^{6} w_i = 0.25 + 0.20 + 0.20 + 0.15 + 0.10 + 0.10 = 1.00$$

1. **Cash Runway Stress ($w_1 = 0.25$)**:
   $$S_1 = \begin{cases} 100 & \text{if } Runway \le 10\text{d} \\ 100 - \frac{Runway - 10}{40} \times 90 & \text{if } 10\text{d} < Runway < 50\text{d} \\ 10 & \text{if } Runway \ge 50\text{d} \end{cases}$$

2. **Overdue Receivables Stress ($w_2 = 0.20$)**:
   $$\text{Ratio}_{\text{rec}} = \frac{R_{\text{overdue}}}{R_{\text{total}}}$$
   $$S_2 = \min(100, \text{Ratio}_{\text{rec}} \times 200)$$

3. **Aging Inventory Stress ($w_3 = 0.20$)**:
   $$\text{Ratio}_{\text{inv}} = \frac{I_{\text{aging}}}{I_{\text{total}}}$$
   $$S_3 = \min(100, \text{Ratio}_{\text{inv}} \times 200)$$

4. **Near-Term Payables Stress ($w_4 = 0.15$)**:
   $$\text{Ratio}_{\text{pay}} = \frac{P_{\text{near-term (12d)}}}{C(t)}$$
   $$S_4 = \min(100, \text{Ratio}_{\text{pay}} \times 100)$$

5. **Demand Softening Stress ($w_5 = 0.10$)**:
   $$S_5 = \begin{cases} \min(100, 30 + |D(t)| \times 3.5) & \text{if } D(t) < 0 \\ \max(0, 30 - D(t) \times 2.0) & \text{if } D(t) \ge 0 \end{cases}$$

6. **Margin Compression Stress ($w_6 = 0.10$)**:
   $$S_6 = \begin{cases} 10 & \text{if } GM \ge 30\% \\ 10 + \frac{30 - GM}{15} \times 90 & \text{if } 15\% \le GM < 30\% \\ 100 & \text{if } GM < 15\% \end{cases}$$

---

## 6. Business State Classification Boundaries

Based on the final composite Pressure Score, the merchant is categorized into one of 5 authoritative business tiers:

| Tier | Pressure Score Range | Semantic Meaning | Recommended Policy |
| :--- | :--- | :--- | :--- |
| **Strong** | $0 \le \text{Score} \le 24$ | Ample liquid reserves, high asset turns | Aggressive growth, volume discounts |
| **Healthy** | $25 \le \text{Score} \le 44$ | Balanced working capital equilibrium | Standard operational terms |
| **Watch** | $45 \le \text{Score} \le 59$ | Emerging working capital friction | Monitor overdue collections, tighten credit |
| **Stressed** | $60 \le \text{Score} \le 74$ | Severe liquidity bottleneck | Prioritize cash acceleration over margin |
| **Critical** | $75 \le \text{Score} \le 100$ | Impending insolvency / payment default | Immediate inventory liquidation, cash upfront |

---

## 7. Deterministic Pressure Driver Ranking

The engine extracts and ranks the top stress contributors by computing individual contribution scores:

$$\text{Contribution}_i = \text{round}\left(w_i \times S_i\right)$$

Drivers are sorted strictly in descending order of contribution points, assigned rank $1, 2, 3 \dots$, and categorized into severity tiers:
- **Critical**: Individual contribution $\ge 15$ points
- **Warning**: Individual contribution $10–14$ points
- **Watch**: Individual contribution $< 10$ points

---

## 8. State Delta & State Transition Formulation

For analyzing temporal shifts or evaluating simulation outcomes, the engine computes the state delta $\Delta \text{State}$:

$$\Delta \text{State} = \text{State}(t_{\text{current}}) - \text{State}(t_{\text{baseline}})$$

For each dimension $M$:
- $\text{Absolute Change} = M_{\text{current}} - M_{\text{baseline}}$
- $\text{Percentage Change} = \frac{M_{\text{current}} - M_{\text{baseline}}}{M_{\text{baseline}}} \times 100$
- $\text{Direction} \in \{\text{Positive}, \text{Negative}, \text{Neutral}\}$

---

## 9. Economic Value Created ($EVC$) Formulation

The prototype objective function quantifying the net economic value delivered by an operational decision or quotation:

$$EVC = CM + \lambda_{\text{liq}} \Delta \text{Liq} + \lambda_{\text{inv}} \text{InvRelief} + \lambda_{\text{rec}} \text{RecRelief} - \text{RiskCost}$$

Where:
- $CM$: Contribution margin realized ($\text{Net Revenue} - \text{COGS}$)
- $\Delta \text{Liq}$: Liquid cash inflow improvement
- $\lambda_{\text{liq}} = 0.15$: Liquidity urgency weight parameter
- $\text{InvRelief}$: Reduction in aged/slow-moving inventory capital
- $\lambda_{\text{inv}} = 0.10$: Inventory carrying relief weight parameter
- $\text{RecRelief}$: Value of overdue receivables accelerated/settled
- $\lambda_{\text{rec}} = 0.08$: Receivables acceleration weight parameter
- $\text{RiskCost}$: Estimated default, discount, or operational carrying risk

---

## 10. Action Evaluation API Specification

`POST /api/merchant/state/evaluate-action`

### Request Payload:
```json
{
  "action": {
    "action_type": "accelerate_payment",
    "target_id": "rec_02",
    "parameters": {
      "discount_pct": 2.0,
      "invoice_amount": 330000.00
    },
    "description": "2% early settlement discount for overdue invoice rec_02"
  }
}
```

### Response Payload:
```json
{
  "action": {
    "action_type": "accelerate_payment",
    "parameters": { "discount_pct": 2.0, "invoice_amount": 330000.00 },
    "description": "2% early settlement discount for overdue invoice rec_02"
  },
  "is_favorable": true,
  "current_pressure_score": 67,
  "projected_pressure_score": 62,
  "pressure_score_delta": -5,
  "current_state": "Stressed",
  "projected_state": "Stressed",
  "economic_value_created": {
    "contribution_margin_value": -6600.00,
    "liquidity_improvement_value": 323400.00,
    "inventory_relief_value": 0.00,
    "receivable_improvement_value": 330000.00,
    "economic_risk_cost": 1500.00,
    "total_economic_value_created": 66810.00,
    "assumptions": {
      "lambda_liquidity_weight": 0.15,
      "lambda_inventory_weight": 0.10,
      "lambda_receivable_weight": 0.08
    }
  },
  "deltas": [
    {
      "metric": "cash",
      "label": "Cash Position",
      "before": 485000.00,
      "after": 808400.00,
      "absolute_change": 323400.00,
      "percentage_change": 66.7,
      "direction": "Positive",
      "unit": "INR",
      "formatted_before": "₹4.85L",
      "formatted_after": "₹8.08L",
      "formatted_change": "+₹3.23L"
    },
    {
      "metric": "overdue_receivables",
      "label": "Overdue Receivables",
      "before": 570000.00,
      "after": 240000.00,
      "absolute_change": -330000.00,
      "percentage_change": -57.9,
      "direction": "Positive",
      "unit": "INR",
      "formatted_before": "₹5.70L",
      "formatted_after": "₹2.40L",
      "formatted_change": "-₹3.30L"
    }
  ],
  "recommendation_summary": "Action is economically favorable: Creates ₹66,810.00 in net economic value and reduces liquidity pressure score by 5 points."
}
```
