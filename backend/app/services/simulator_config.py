from decimal import Decimal


class SimulatorConfig:
    """
    Centralized, transparent configuration parameters for the Counterfactual Economic Simulator.
    """
    # Objective Function Weights: EVC = w_contrib*CM + w_liq*Liq + w_inv*InvRelief + w_rec*Rec - w_risk*Risk - w_cap*Cap - w_stockout*Stockout
    WEIGHT_CONTRIBUTION: Decimal = Decimal("0.35")
    WEIGHT_LIQUIDITY: Decimal = Decimal("0.25")
    WEIGHT_INVENTORY_RELIEF: Decimal = Decimal("0.15")
    WEIGHT_RECEIVABLE_BENEFIT: Decimal = Decimal("0.10")
    WEIGHT_RISK_COST: Decimal = Decimal("0.10")
    WEIGHT_CAPACITY_COST: Decimal = Decimal("0.05")
    WEIGHT_STOCKOUT_COST: Decimal = Decimal("0.05")

    # Payment Timing Liquidity Multipliers
    TIMING_MULTIPLIERS = {
        0: Decimal("1.00"),    # Immediate payment: 100% liquid cash value
        7: Decimal("0.85"),    # 7-day payment: 85% liquidity equivalent
        15: Decimal("0.70"),   # 15-day payment: 70% liquidity equivalent
        30: Decimal("0.45"),   # 30-day payment: 45% liquidity equivalent (standard trade credit)
        45: Decimal("0.25"),   # 45-day payment: 25% liquidity equivalent
        60: Decimal("0.10"),   # 60-day payment: high delay penalty
    }

    # Capacity Limits & Penalties
    OPTIMAL_CAPACITY_MAX_PCT: Decimal = Decimal("85.0")
    HARD_CAPACITY_LIMIT_PCT: Decimal = Decimal("100.0")
    CAPACITY_OVERLOAD_PENALTY_RATE: Decimal = Decimal("250.0")  # Cost per 1% overload above optimal

    # Stockout & Coverage Thresholds
    MIN_COVERAGE_DAYS_HEALTHY: Decimal = Decimal("25.0")
    MIN_COVERAGE_DAYS_WATCH: Decimal = Decimal("15.0")
    MIN_COVERAGE_DAYS_CONSTRAINED: Decimal = Decimal("7.0")

    # Aging Inventory Clearance Bonus
    AGING_CLEARANCE_PREMIUM_RATE: Decimal = Decimal("0.20")  # 20% bonus on working capital unlocked from >45d aging stock
