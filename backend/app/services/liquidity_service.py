from sqlalchemy.orm import Session
from app.schemas.merchant import (
    BusinessStateResponse,
    DimensionState,
    LiquidityPressureDriver,
)
from app.services.economic_state_service import EconomicStateService


class LiquidityService:
    @staticmethod
    def get_business_state(db: Session, merchant_id: str) -> BusinessStateResponse:
        state = EconomicStateService.calculate_current_state(db=db, merchant_id=merchant_id)

        drivers = [
            LiquidityPressureDriver(
                id=d.id,
                title=d.title,
                impact_amount=d.impact_amount,
                impact_formatted=d.impact_formatted,
                category=d.category,
                description=d.description,
                severity=d.severity,
            )
            for d in state.top_drivers
        ]

        def to_dim(d) -> DimensionState:
            return DimensionState(
                dimension=d.dimension,
                name=d.name,
                value=d.value,
                formatted_value=d.formatted_value,
                status=d.status,
                label=d.label,
                trend=d.trend,
                trend_pct=d.trend_pct,
                benchmark=d.benchmark,
            )

        return BusinessStateResponse(
            merchant_id=state.merchant_id,
            merchant_name=state.merchant_name,
            trade_name=state.trade_name,
            gst_number=state.gst_number,
            industry=state.industry,
            as_of=state.as_of,
            liquidity_stress_score=state.pressure_score,
            liquidity_status=state.liquidity_status,
            liquidity_outlook_headline=state.liquidity_outlook_headline,
            liquidity_outlook_summary=state.liquidity_outlook_summary,
            drivers=drivers,
            cash=to_dim(state.cash),
            receivables=to_dim(state.receivables),
            payables=to_dim(state.payables),
            inventory_value=to_dim(state.inventory_value),
            aging_inventory=to_dim(state.aging_inventory),
            gross_margin=to_dim(state.gross_margin),
            demand_trend=to_dim(state.demand_trend),
            customer_value=to_dim(state.customer_value),
            fulfillment_capacity=to_dim(state.fulfillment_capacity),
            cash_runway=to_dim(state.cash_runway),
            working_capital=state.working_capital,
            working_capital_formatted=state.working_capital_formatted,
            quick_ratio=state.quick_ratio,
            current_ratio=state.current_ratio,
            dso_days=state.dso_days,
            dpo_days=state.dpo_days,
            dio_days=state.dio_days,
            cash_conversion_cycle=state.cash_conversion_cycle,
        )
