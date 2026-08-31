from decimal import Decimal
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models import Product, InventoryItem
from app.schemas.economic_state import EconomicStateModel
from app.schemas.scenario import BuyerRequestModel, MerchantConstraintsModel
from app.services.formatters import round_decimal


class DealCandidateGenerator:
    """
    Algorithmic generation of 4 diverse commercial candidate deals based on merchant
    economic state, catalog pricing, and merchant policy constraints.
    """

    @staticmethod
    def generate_candidates(
        db: Session,
        merchant_id: str,
        current_state: EconomicStateModel,
        request: BuyerRequestModel,
        constraints: MerchantConstraintsModel,
    ) -> List[Dict[str, Any]]:
        # Fetch target product or closest catalog match
        if request.product_id:
            product = db.query(Product).filter(Product.id == request.product_id).first()
        elif request.target_budget and request.requested_quantity > 0:
            target_unit_price = request.target_budget / Decimal(request.requested_quantity)
            all_prods = db.query(Product).filter(Product.merchant_id == merchant_id).all()
            if not all_prods:
                all_prods = db.query(Product).all()
            if all_prods:
                product = min(all_prods, key=lambda p: abs(Decimal(str(p.current_price)) - target_unit_price))
            else:
                product = db.query(Product).first()
        else:
            product = db.query(Product).filter(Product.merchant_id == merchant_id).first()

        if not product:
            product = db.query(Product).first()

        catalog_price = Decimal(str(product.current_price))
        unit_cost = Decimal(str(product.unit_cost))
        qty = request.requested_quantity

        # Check if product has aging inventory
        inv_item = (
            db.query(InventoryItem)
            .filter(InventoryItem.product_id == product.id, InventoryItem.merchant_id == merchant_id)
            .first()
        )
        is_aging = (
            inv_item.days_in_stock > 45 or inv_item.status in ("Aging", "Critical")
        ) if inv_item else False

        # -------------------------------------------------------------
        # Candidate A: Standard Terms (Standard 30d credit, Full catalog price)
        # -------------------------------------------------------------
        deal_a = {
            "id": "cand_a_standard",
            "label": "Deal A • Standard Terms",
            "strategy_tag": "Standard Terms",
            "action_type": "sale",
            "product_id": product.id,
            "quantity": qty,
            "unit_price": catalog_price,
            "payment_timing_days": 30,
            "delivery_days": min(request.max_delivery_days, 6),
            "target_aging_reduction_units": 0,
            "description": f"Standard commercial order of {qty} units at list price {catalog_price} on standard 30-day deferred credit terms.",
        }

        # -------------------------------------------------------------
        # Candidate B: Cash Acceleration (Prompt Pay 4% Discount, 0-Day Immediate Payment)
        # -------------------------------------------------------------
        discount_b_pct = Decimal("4.0")
        price_b = round_decimal(catalog_price * (Decimal("1.0") - (discount_b_pct / Decimal("100.0"))), 2)
        # Ensure margin floor
        if price_b < unit_cost * (Decimal("1.0") + (constraints.min_margin_pct / Decimal("100.0"))):
            price_b = round_decimal(unit_cost * (Decimal("1.0") + (constraints.min_margin_pct / Decimal("100.0"))), 2)

        deal_b = {
            "id": "cand_b_cash_accel",
            "label": "Deal B • Cash Acceleration",
            "strategy_tag": "Cash Acceleration",
            "action_type": "price_change",
            "product_id": product.id,
            "quantity": qty,
            "unit_price": price_b,
            "payment_timing_days": 0,  # Immediate settlement
            "delivery_days": min(request.max_delivery_days, 5),
            "target_aging_reduction_units": 0,
            "description": f"Immediate cash settlement incentive granting 4% discount ({price_b}/unit) with instant Razorpay / UPI settlement.",
        }

        # -------------------------------------------------------------
        # Candidate C: Volume Maximizer (15% higher volume, 6% volume discount, 7-Day short payment)
        # -------------------------------------------------------------
        vol_c_qty = int(round(qty * 1.15))
        discount_c_pct = Decimal("6.5")
        price_c = round_decimal(catalog_price * (Decimal("1.0") - (discount_c_pct / Decimal("100.0"))), 2)
        if price_c < unit_cost * (Decimal("1.0") + (constraints.min_margin_pct / Decimal("100.0"))):
            price_c = round_decimal(unit_cost * (Decimal("1.0") + (constraints.min_margin_pct / Decimal("100.0"))), 2)

        deal_c = {
            "id": "cand_c_volume_boost",
            "label": "Deal C • Volume Maximizer",
            "strategy_tag": "Volume Maximizer",
            "action_type": "quantity_change",
            "product_id": product.id,
            "quantity": vol_c_qty,
            "unit_price": price_c,
            "payment_timing_days": 7,  # Short terms
            "delivery_days": max(4, request.max_delivery_days),
            "target_aging_reduction_units": 0,
            "description": f"Expanded volume order of {vol_c_qty} units at {price_c}/unit (6.5% discount) with accelerated 7-day payment terms.",
        }

        # -------------------------------------------------------------
        # Candidate D: Aging Inventory Clearance / Liquidation Bundle
        # -------------------------------------------------------------
        discount_d_pct = Decimal("9.0")
        price_d = round_decimal(catalog_price * (Decimal("1.0") - (discount_d_pct / Decimal("100.0"))), 2)
        if price_d < unit_cost * Decimal("1.05"):  # Clearance floor
            price_d = round_decimal(unit_cost * Decimal("1.05"), 2)

        aging_units_to_clear = qty if is_aging else int(qty * 0.7)

        deal_d = {
            "id": "cand_d_aging_clearance",
            "label": "Deal D • Aging Stock Clearance",
            "strategy_tag": "Aging Clearance",
            "action_type": "inventory_liquidation",
            "product_id": product.id,
            "quantity": qty,
            "unit_price": price_d,
            "payment_timing_days": 0,  # Immediate settlement
            "delivery_days": min(request.max_delivery_days, 4),
            "target_aging_reduction_units": aging_units_to_clear,
            "description": f"Targeted liquidation of aged inventory units at clearance price {price_d}/unit with 100% immediate cash settlement.",
        }

        return [deal_a, deal_b, deal_c, deal_d]
