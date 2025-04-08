from trading_plan import calculate_position_size


# test_trading_plan.py


def test_calculate_position_size_normal_case():
    result = calculate_position_size(
        entry_price=100.0,
        stop_loss=90.0,
        account_balance=10000.0,
        risk_per_trade_percent=1.0,
        risked_capital_percent=10.0,
    )
    assert result == 10  # Expected quantity based on calculations

def test_calculate_position_size_max_capital_limit():
    result = calculate_position_size(
        entry_price=200.0,
        stop_loss=190.0,
        account_balance=10000.0,
        risk_per_trade_percent=1.0,
        risked_capital_percent=5.0,
    )
    assert result == 2  # Quantity adjusted to respect max capital allocation

def test_calculate_position_size_zero_division():
    result = calculate_position_size(
        entry_price=100.0,
        stop_loss=100.0,
        account_balance=10000.0,
        risk_per_trade_percent=1.0,
        risked_capital_percent=10.0,
    )
    assert result == 0  # Division by zero should return 0


def test_calculate_position_size_large_account_balance():
    result = calculate_position_size(
        entry_price=50.0,
        stop_loss=40.0,
        account_balance=1_000_000.0,
        risk_per_trade_percent=2.0,
        risked_capital_percent=20.0,
    )
    assert result == 2000  # Expected quantity based on calculations
