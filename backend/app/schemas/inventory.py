from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class ProductBase(BaseModel):
    sku: str
    name: str
    category: str
    unit: str = "units"
    unit_cost: Decimal
    current_price: Decimal
    min_stock_threshold: int = 10


class ProductResponse(ProductBase):
    id: str
    merchant_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InventoryItemBase(BaseModel):
    available_quantity: int
    reserved_quantity: int
    days_in_stock: int
    batch_number: Optional[str] = None
    location: str = "Main Warehouse - Pune"
    status: str = "Healthy"  # Healthy, Watch, Aging, Critical
    demand_trend: str = "Stable"  # Increasing, Stable, Softening, Declining


class InventoryItemResponse(InventoryItemBase):
    id: str
    product_id: str
    merchant_id: str
    last_restocked_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InventoryItemWithProduct(InventoryItemBase):
    id: str
    product_id: str
    merchant_id: str
    product_sku: str
    product_name: str
    product_category: str
    unit: str
    unit_cost: Decimal
    current_price: Decimal
    min_stock_threshold: int
    inventory_value: Decimal
    inventory_value_formatted: str
    gross_margin_pct: Decimal
    last_restocked_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CategoryBreakdown(BaseModel):
    category: str
    item_count: int
    total_value: Decimal
    aging_value: Decimal
    percentage: Decimal


class InventorySummary(BaseModel):
    total_skus: int
    total_units: int
    total_inventory_value: Decimal
    total_inventory_value_formatted: str
    total_aging_value: Decimal
    total_aging_value_formatted: str
    aging_pct: Decimal
    low_stock_count: int
    healthy_count: int
    watch_count: int
    aging_count: int
    critical_count: int
    category_breakdown: List[CategoryBreakdown]


class InventoryListResponse(BaseModel):
    summary: InventorySummary
    items: List[InventoryItemWithProduct]
