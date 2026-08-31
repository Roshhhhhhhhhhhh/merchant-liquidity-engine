from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.api.deps import get_current_merchant_id
from app.models.product import Product
from app.schemas.inventory import InventoryListResponse, ProductResponse
from app.services.inventory_service import InventoryService

router = APIRouter()


@router.get("", response_model=InventoryListResponse, summary="Get inventory items with summary")
def get_inventory(
    category: Optional[str] = Query(None, description="Filter by product category"),
    status: Optional[str] = Query(None, description="Filter by status: Healthy, Watch, Aging, Critical"),
    search: Optional[str] = Query(None, description="Search product name, SKU, or category"),
    merchant_id: str = Depends(get_current_merchant_id),
    db: Session = Depends(get_db),
):
    return InventoryService.get_inventory_items(
        db=db,
        merchant_id=merchant_id,
        category=category,
        status=status,
        search=search,
    )


@router.get("/products", response_model=List[ProductResponse], summary="Get product master catalogue")
def get_products(
    merchant_id: str = Depends(get_current_merchant_id),
    db: Session = Depends(get_db),
):
    return db.query(Product).filter(Product.merchant_id == merchant_id).all()
