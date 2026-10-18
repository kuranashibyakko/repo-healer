from math_ops import calculate_discount, calculate_compound_growth

def test_discount_twenty_percent():
    # $100 with 20% discount should be $80.0
    assert calculate_discount(100.0, 20.0) == 80.0

def test_compound_growth():
    assert calculate_compound_growth(1000.0, 0.05, 2) == 1102.50
