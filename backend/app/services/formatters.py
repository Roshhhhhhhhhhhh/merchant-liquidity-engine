from decimal import Decimal, ROUND_HALF_UP
from typing import Union


def round_decimal(value: Union[Decimal, float, int, str], places: int = 2) -> Decimal:
    """
    Rounds a value safely to specified decimal places using standard financial ROUND_HALF_UP.
    """
    if value is None:
        return Decimal("0.00")
    d = Decimal(str(value))
    exp = Decimal("10") ** (-places) if places > 0 else Decimal("1")
    return d.quantize(exp, rounding=ROUND_HALF_UP)


def format_inr(amount: Union[Decimal, float, int], compact: bool = True) -> str:
    """
    Format monetary amounts to INR formatting:
    e.g. ₹4.85L, ₹18.40L, ₹1.25Cr, or ₹4,85,000.00
    """
    if amount is None:
        return "₹0.00"
    
    val = float(amount)
    sign = "-" if val < 0 else ""
    val = abs(val)

    if compact:
        if val >= 10000000:  # 1 Crore
            return f"{sign}₹{val / 10000000:.2f}Cr"
        elif val >= 100000:  # 1 Lakh
            return f"{sign}₹{val / 100000:.2f}L"
        elif val >= 1000:  # 1 Thousand
            return f"{sign}₹{val / 1000:.1f}k"
        else:
            return f"{sign}₹{val:.2f}"
    
    # Detailed Indian numbering format
    s = f"{val:.2f}"
    parts = s.split(".")
    integer_part = parts[0]
    decimal_part = parts[1]

    if len(integer_part) <= 3:
        formatted_int = integer_part
    else:
        last3 = integer_part[-3:]
        other = integer_part[:-3]
        groups = []
        while len(other) > 2:
            groups.insert(0, other[-2:])
            other = other[:-2]
        if other:
            groups.insert(0, other)
        groups.append(last3)
        formatted_int = ",".join(groups)

    return f"{sign}₹{formatted_int}.{decimal_part}"
