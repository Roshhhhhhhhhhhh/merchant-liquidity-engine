from fastapi import APIRouter
from app.api.routes import (
    health,
    merchant,
    inventory,
    receivables,
    payables,
    transactions,
    snapshots,
    activity,
    scenarios,
    agent_routes,
    payment_routes,
)

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(merchant.router, prefix="/merchant", tags=["Merchant"])
api_router.include_router(inventory.router, prefix="/inventory", tags=["Inventory"])
api_router.include_router(receivables.router, prefix="/receivables", tags=["Receivables"])
api_router.include_router(payables.router, prefix="/payables", tags=["Payables"])
api_router.include_router(transactions.router, prefix="/transactions", tags=["Transactions"])
api_router.include_router(snapshots.router, prefix="/snapshots", tags=["Snapshots"])
api_router.include_router(activity.router, prefix="/activity", tags=["Activity"])
api_router.include_router(scenarios.router, prefix="/scenarios", tags=["Scenarios"])
api_router.include_router(agent_routes.router, prefix="/agent", tags=["Agentic Negotiation"])
api_router.include_router(payment_routes.router, prefix="/payments", tags=["Payments & Settlement"])
api_router.include_router(payment_routes.router, prefix="/webhooks", tags=["Webhooks"])
