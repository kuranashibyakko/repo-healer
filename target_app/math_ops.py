def calculate_discount(price: float, discount_percent: float) -> float:
    """Returns the final price after applying a percentage discount."""
    if discount_percent < 0 or discount_percent > 100:
        raise ValueError("Discount must be between 0 and 100")
    # BUG: Adding the discount instead of subtracting it!
    discount_amount = price * (discount_percent / 100.0)
    return price + discount_amount


def calculate_compound_growth(principal: float, rate: float, years: int) -> float:
    """Returns compound growth."""
    return round(principal * ((1 + rate) ** years), 2)
