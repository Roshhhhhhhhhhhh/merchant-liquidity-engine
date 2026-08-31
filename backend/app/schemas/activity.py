from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, ConfigDict


class ActivityEventBase(BaseModel):
    event_type: str
    category: str = "General"  # Liquidity, Inventory, Receivables, Payables, Transactions
    title: str
    description: str
    severity: str = "Info"  # Info, Low, Medium, High, Critical
    metadata_json: Optional[str] = None


class ActivityEventResponse(ActivityEventBase):
    id: str
    merchant_id: str
    parsed_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ActivitySummary(BaseModel):
    total_events: int
    critical_count: int
    high_count: int
    medium_count: int
    info_count: int
    categories: List[str]


class ActivityListResponse(BaseModel):
    summary: ActivitySummary
    events: List[ActivityEventResponse]
