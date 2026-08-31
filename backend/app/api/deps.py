from typing import Generator
from sqlalchemy.orm import Session
from app.database.session import get_db

DEFAULT_MERCHANT_ID = "mch_aarav_001"


def get_current_merchant_id() -> str:
    # Configurable default merchant for Phase 1 single-tenant/sandbox MSME context
    return DEFAULT_MERCHANT_ID
