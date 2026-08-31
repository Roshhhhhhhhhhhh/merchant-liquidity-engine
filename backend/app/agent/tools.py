from decimal import Decimal
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from app.models import Product, InventoryItem, Merchant
from app.schemas.economic_state import EconomicStateModel
from app.schemas.scenario import BuyerRequestModel, MerchantConstraintsModel
from app.schemas.agent import BuyerRequest
from app.services.economic_state_service import EconomicStateService
from app.services.counterfactual_service import CounterfactualStateService
from app.services.deal_generator import DealCandidateGenerator
from app.services.deal_optimizer import DealOptimizationService


class AgentTools:
    """
    Deterministic backend tools exposed to the Merchant Agent and AI Buyer Agent.
    All financial, inventory, pricing, and valuation operations execute through these tools.
    """

    @staticmethod
    def get_merchant_state(db: Session, merchant_id: str) -> EconomicStateModel:
        """Retrieves the live 10-dimensional Economic Twin state of the merchant."""
        return EconomicStateService.calculate_current_state(db=db, merchant_id=merchant_id)

    @staticmethod
    def get_inventory(db: Session, merchant_id: str) -> List[Dict[str, Any]]:
        """Retrieves inventory levels, aging classifications, and days in stock."""
        items = (
            db.query(InventoryItem)
            .filter(InventoryItem.merchant_id == merchant_id)
            .all()
        )
        result = []
        for it in items:
            prod = it.product
            result.append({
                "inventory_id": it.id,
                "product_id": it.product_id,
                "product_name": prod.name if prod else "Unknown",
                "sku": prod.sku if prod else "",
                "available_quantity": it.available_quantity,
                "days_in_stock": it.days_in_stock,
                "status": it.status,
                "is_aging": it.days_in_stock > 45 or it.status in ("Aging", "Critical"),
            })
        return result

    @staticmethod
    def get_product_catalog(db: Session, merchant_id: str) -> List[Dict[str, Any]]:
        """Retrieves official product catalog with list prices and baseline unit costs."""
        products = db.query(Product).filter(Product.merchant_id == merchant_id).all()
        if not products:
            products = db.query(Product).all()
        return [
            {
                "product_id": p.id,
                "name": p.name,
                "sku": p.sku,
                "category": p.category,
                "unit": p.unit,
                "list_price": float(p.current_price),
                "unit_cost": float(p.unit_cost),
                "min_stock_threshold": p.min_stock_threshold,
            }
            for p in products
        ]

    @staticmethod
    def get_merchant_constraints(merchant_id: str) -> MerchantConstraintsModel:
        """Retrieves hard commercial boundaries (margin floors, credit limits)."""
        return MerchantConstraintsModel(
            min_margin_pct=Decimal("12.0"),
            max_credit_days=30,
            require_advance_payment=False,
            max_discount_pct=Decimal("10.0"),
            allow_aging_clearance_bonus=True,
        )

    @staticmethod
    def generate_deal_candidates(
        db: Session,
        merchant_id: str,
        buyer_req: BuyerRequest,
        constraints: Optional[MerchantConstraintsModel] = None,
    ) -> List[Dict[str, Any]]:
        """Generates 4 strategic deal candidates using the deterministic DealCandidateGenerator."""
        current_state = AgentTools.get_merchant_state(db=db, merchant_id=merchant_id)
        effective_constraints = constraints or AgentTools.get_merchant_constraints(merchant_id)
        
        scenario_req = BuyerRequestModel(
            product_id=buyer_req.product_id,
            product_name=buyer_req.product_name,
            requested_quantity=buyer_req.quantity,
            target_budget=buyer_req.maximum_budget,
            max_delivery_days=buyer_req.maximum_delivery_days,
            preferred_payment_timing_days=buyer_req.preferred_payment_days,
            custom_notes=buyer_req.raw_inquiry_text,
        )
        return DealCandidateGenerator.generate_candidates(
            db=db,
            merchant_id=merchant_id,
            current_state=current_state,
            request=scenario_req,
            constraints=effective_constraints,
        )

    @staticmethod
    def simulate_deal(
        db: Session,
        merchant_id: str,
        product_id: str,
        quantity: int,
        unit_price: Decimal,
        payment_timing_days: int = 0,
        delivery_days: int = 5,
        target_aging_reduction_units: int = 0,
    ) -> Dict[str, Any]:
        """Simulates counterfactual balance sheet state transition for a proposed deal."""
        current_state = AgentTools.get_merchant_state(db=db, merchant_id=merchant_id)
        return CounterfactualStateService.simulate_deal(
            db=db,
            merchant_id=merchant_id,
            current_state=current_state,
            product_id=product_id,
            quantity=quantity,
            unit_price=unit_price,
            payment_timing_days=payment_timing_days,
            delivery_days=delivery_days,
            target_aging_reduction_units=target_aging_reduction_units,
        )

    @staticmethod
    def compare_and_optimize_deals(
        evaluated_candidates: List[Dict[str, Any]],
    ) -> Tuple[List[Any], Any, str]:
        """Ranks candidates strictly by Economic Value Created ($EVC$) and generates deterministic decision rationale."""
        return DealOptimizationService.optimize_and_rank_candidates(evaluated_candidates)
