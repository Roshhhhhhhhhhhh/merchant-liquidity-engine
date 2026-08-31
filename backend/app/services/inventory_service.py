from decimal import Decimal
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from app.models.inventory import InventoryItem
from app.models.product import Product
from app.schemas.inventory import (
    InventorySummary,
    InventoryItemWithProduct,
    InventoryListResponse,
    CategoryBreakdown,
)
from app.services.formatters import format_inr


class InventoryService:
    @staticmethod
    def get_inventory_items(
        db: Session,
        merchant_id: str,
        category: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> InventoryListResponse:
        query = (
            db.query(InventoryItem)
            .join(Product, InventoryItem.product_id == Product.id)
            .filter(InventoryItem.merchant_id == merchant_id)
            .options(joinedload(InventoryItem.product))
        )

        all_items: List[InventoryItem] = query.all()

        # Compute summary over all items before filtering
        total_skus = len(all_items)
        total_units = 0
        total_inventory_value = Decimal("0.00")
        total_aging_value = Decimal("0.00")
        low_stock_count = 0
        healthy_count = 0
        watch_count = 0
        aging_count = 0
        critical_count = 0
        cat_map = {}

        detailed_items: List[InventoryItemWithProduct] = []

        for item in all_items:
            product = item.product
            units = item.available_quantity
            cost = Decimal(str(product.unit_cost))
            price = Decimal(str(product.current_price))
            item_val = Decimal(units) * cost
            margin_pct = ((price - cost) / price * Decimal(100)) if price > 0 else Decimal(0)

            total_units += units
            total_inventory_value += item_val

            if item.days_in_stock > 45 or item.status in ("Aging", "Critical"):
                total_aging_value += item_val

            if units <= product.min_stock_threshold:
                low_stock_count += 1

            if item.status == "Healthy":
                healthy_count += 1
            elif item.status == "Watch":
                watch_count += 1
            elif item.status == "Aging":
                aging_count += 1
            elif item.status == "Critical":
                critical_count += 1

            # Category tally
            cat = product.category
            if cat not in cat_map:
                cat_map[cat] = {"count": 0, "total_value": Decimal("0.00"), "aging_value": Decimal("0.00")}
            cat_map[cat]["count"] += 1
            cat_map[cat]["total_value"] += item_val
            if item.days_in_stock > 45 or item.status in ("Aging", "Critical"):
                cat_map[cat]["aging_value"] += item_val

            # Apply filters for item list
            if category and product.category.lower() != category.lower():
                continue
            if status and item.status.lower() != status.lower():
                continue
            if search:
                s = search.lower()
                if (
                    s not in product.name.lower()
                    and s not in product.sku.lower()
                    and s not in product.category.lower()
                ):
                    continue

            detailed_items.append(
                InventoryItemWithProduct(
                    id=item.id,
                    product_id=product.id,
                    merchant_id=item.merchant_id,
                    product_sku=product.sku,
                    product_name=product.name,
                    product_category=product.category,
                    unit=product.unit,
                    unit_cost=cost,
                    current_price=price,
                    min_stock_threshold=product.min_stock_threshold,
                    available_quantity=item.available_quantity,
                    reserved_quantity=item.reserved_quantity,
                    days_in_stock=item.days_in_stock,
                    batch_number=item.batch_number,
                    location=item.location,
                    status=item.status,
                    demand_trend=item.demand_trend,
                    inventory_value=item_val,
                    inventory_value_formatted=format_inr(item_val),
                    gross_margin_pct=round(margin_pct, 1),
                    last_restocked_at=item.last_restocked_at,
                    updated_at=item.updated_at,
                )
            )

        aging_pct = (
            round((total_aging_value / total_inventory_value * Decimal(100)), 1)
            if total_inventory_value > 0
            else Decimal("0.0")
        )

        category_breakdowns = [
            CategoryBreakdown(
                category=k,
                item_count=v["count"],
                total_value=v["total_value"],
                aging_value=v["aging_value"],
                percentage=round((v["total_value"] / total_inventory_value * Decimal(100)), 1)
                if total_inventory_value > 0
                else Decimal(0),
            )
            for k, v in cat_map.items()
        ]
        category_breakdowns.sort(key=lambda x: x.total_value, reverse=True)

        summary = InventorySummary(
            total_skus=total_skus,
            total_units=total_units,
            total_inventory_value=total_inventory_value,
            total_inventory_value_formatted=format_inr(total_inventory_value),
            total_aging_value=total_aging_value,
            total_aging_value_formatted=format_inr(total_aging_value),
            aging_pct=aging_pct,
            low_stock_count=low_stock_count,
            healthy_count=healthy_count,
            watch_count=watch_count,
            aging_count=aging_count,
            critical_count=critical_count,
            category_breakdown=category_breakdowns,
        )

        return InventoryListResponse(summary=summary, items=detailed_items)
