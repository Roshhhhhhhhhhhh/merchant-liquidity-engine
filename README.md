# MERCHANT LIQUIDITY ENGINE

> *"Optimize what a transaction does to the business."*  
> Built for the **Razorpay Buildathon**.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3+-61DAFB.svg?style=flat&logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.5+-3178C6.svg?style=flat&logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-3.4+-38B2AC.svg?style=flat&logo=tailwind-css&logoColor=white)](https://tailwindcss.com)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-D71F00.svg?style=flat&logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org)
[![Python Tests](https://img.shields.io/badge/Pytest-12%20Passed-brightgreen.svg)](https://docs.pytest.org)

---

## 1. Executive Summary

**Merchant Liquidity Engine** is a merchant-side economic intelligence platform. 

Rather than viewing transactions merely through top-line revenue or static accounting margins, the engine models the **dynamic future economic state** of the merchant across 10 core dimensions:

1. **Cash Balance** (`₹4.85L`)
2. **Receivables Book** (`₹18.40L`, with `₹5.70L` overdue past 30 days)
3. **Accounts Payable** (`₹12.60L`, with `₹3.50L` due within 12 days)
4. **Inventory Valuation** (`₹34.20L` across 14 active SKUs)
5. **Aging Inventory** (`₹8.90L` locked in stock >45 days)
6. **Blended Gross Margin** (`28.4%`)
7. **Demand Velocity Trend** (`-4.2% MoM`)
8. **Customer Portfolio Value** (`₹48.60L` client exposure)
9. **Fulfillment Capacity Utilization** (`84.0%`)
10. **Cash Runway** (`24 Days` at `₹20,200/day` operating burn)

---

## 2. Monorepo Structure

```
MERCHANT LIQUIDITY ENGINE/
├── backend/                  # FastAPI + SQLAlchemy 2.0 + Pydantic v2
│   ├── app/
│   │   ├── api/              # REST Endpoints (Health, Merchant, Inventory, Receivables, etc.)
│   │   ├── core/             # Configuration & Structured Logging
│   │   ├── database/         # Session & Base ORM Models
│   │   ├── models/           # SQLAlchemy 2.0 Entities (Decimal/Numeric safe)
│   │   ├── schemas/          # Pydantic Schemas & DTOs
│   │   ├── services/         # Deterministic Liquidity, Inventory & Receivables Engine
│   │   ├── seed/             # Realistic MSME Seed Generator ("Aarav Industrial Supplies")
│   │   └── main.py           # Application Entrypoint with CORS & Auto-Seed
│   ├── tests/                # Pytest Unit & Integration Suite
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                 # React 18 + Vite + TypeScript + Tailwind CSS
│   ├── src/
│   │   ├── app/              # Router & Query Providers
│   │   ├── components/       # Common UI, Layout & Recharts Financial Visualizations
│   │   ├── hooks/            # TanStack Query Custom Hooks
│   │   ├── pages/            # Overview, Business State, Inventory, Receivables, etc.
│   │   ├── services/         # Centralized Axios Client
│   │   ├── types/            # TypeScript Schema Definitions
│   │   └── utils/            # Indian Currency (₹ Lakh/Crore) & Metric Formatters
│   ├── package.json
│   └── Dockerfile
├── docs/
│   └── architecture.md       # Comprehensive Architecture & Evolution Roadmap
├── docker-compose.yml        # Multi-Container Deployment Specification
├── .env.example
└── README.md
```

---

## 3. Quick Start (Local Setup)

### Prerequisites
- **Python**: `3.11` or `3.12`
- **Node.js**: `v18+` or `v20+` (npm 9+)

---

### Step 1: Start Backend

```bash
# Navigate to backend directory
cd backend

# Create & activate virtual environment
python -m venv venv
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1
# On macOS/Linux:
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run seed script (auto-creates merchant_liquidity.db if not present)
python -m app.seed.seed_data

# Start backend development server
uvicorn app.main:app --reload --port 8000
```
Backend API will be live at: **`http://localhost:8000`**  
Interactive Swagger Docs: **`http://localhost:8000/docs`**

---

### Step 2: Start Frontend

```bash
# In a new terminal, navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start Vite development server
npm run dev
```
Frontend web application will be live at: **`http://localhost:5173`**

---

### Step 3: Run Backend Test Suite

```bash
cd backend
pytest -v
```
All 12 unit and integration test suites will execute against an in-memory SQLite instance.

---

## 4. Docker Deployment

```bash
# Build and launch both backend and frontend services
docker-compose up --build
```

---

## 5. API Overview

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | System health and database connectivity check |
| `GET` | `/api/merchant` | Merchant profile and metadata |
| `GET` | `/api/merchant/state` | Live 10-dimension economic breakdown, stress score, & pressure drivers |
| `GET` | `/api/inventory` | Inventory item catalogue with category valuation & aging metrics |
| `GET` | `/api/inventory/products`| Product master catalogue |
| `GET` | `/api/receivables` | Receivables ledger with 4-bucket aging distribution (0-15d, 16-30d, 31-60d, 60+d) |
| `GET` | `/api/receivables/customers` | Customer directory with credit limits and payment reliability scores |
| `GET` | `/api/payables` | Accounts payable with near-term dues schedule |
| `GET` | `/api/transactions` | Transaction log with realized net margins and settlement tracking |
| `GET` | `/api/snapshots` | 30-day historical trend points for multi-series correlation charts |
| `GET` | `/api/activity` | Chronological operational event feed with category/severity filters |

---

## 6. Seeded MSME Scenario ("Aarav Industrial Supplies")

The database is pre-populated with realistic industrial flow-control and piping supplies data:
- **Merchant**: Aarav Industrial Supplies Pvt Ltd (`MIDC Bhosari, Pune`)
- **Customers**: 8 Tier-1 B2B accounts (L&T Heavy Engineering, Bharat Heavy Fabricators, Gujarat Petrochem, Deccan Refineries, etc.)
- **Receivables**: `₹18.40L` outstanding, with `₹5.70L` overdue past 30 days (lengthening DSO to 42 days).
- **Payables**: `₹12.60L` total, with `₹3.50L` due within 12 days against available cash of `₹4.85L`.
- **Inventory**: `₹34.20L` total valuation across 14 SKUs, with `₹8.90L` locked in slow-moving actuators & specialized flanges (>45–78 days in stock).
- **Stress Index**: `68/100` (`Warning`), accurately communicating that while revenue and margins are healthy, working capital is compressed.

---

## 7. Next Recommended Phase (Phase 2 Roadmap)

1. **Counterfactual Engine**: Implement state-forking and Monte Carlo simulation to project how discounting slow inventory vs. accepting bulk orders alters 30-day cash runway.
2. **Liquidity-Adjusted Quotation**: Real-time algorithmic calculation of optimal commercial terms.
3. **Razorpay Smart Settlement & Virtual Accounts**: Direct payment webhook listeners for live automatic state updates.
