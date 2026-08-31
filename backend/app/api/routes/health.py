from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database.session import get_db

router = APIRouter()


@router.get("/health", summary="Health check")
def health_check(db: Session = Depends(get_db)):
    db_status = "healthy"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "ok" if db_status == "healthy" else "degraded",
        "service": "Merchant Liquidity Engine API",
        "version": "1.0.0",
        "environment": "sandbox",
        "database": db_status,
        "timestamp": datetime.utcnow().isoformat(),
    }
