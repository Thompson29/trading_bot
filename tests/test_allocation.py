import pytest
import os
from core.trader import AlpacaTrader
from core.utils import calculate_diffs
from core.profiles import RISK_PROFILES

# --- Allocation Tests ---

@pytest.mark.parametrize("risk_level", [
    "very_conservative",
    "conservative",
    "moderate",
    "aggressive",
    "aggressive_growth"
])
def test_allocate_portfolio(risk_level):
    capital = 1000
    profile = RISK_PROFILES.get(risk_level)
    if not profile:
        raise ValueError("Invalid risk level")
    result = {etf: round(capital * weight, 2) for etf, weight in profile.items()}
    assert isinstance(result, dict)
    assert abs(sum(result.values()) - capital) < 1 or "CASH" in result


# --- Rebalance Diff Calculation ---

def test_calculate_diffs():
    current_alloc = {"VTI": 300, "VOO": 300, "BND": 400}
    target_alloc = {"VTI": 0.5, "VOO": 0.3, "BND": 0.2}
    total_value = 1000

    diffs = calculate_diffs(current_alloc, target_alloc, total_value)

    assert round(diffs["VTI"], 2) == 200.0
    assert round(diffs["BND"], 2) == -200.0


# --- Trader Mock Rebalance ---

class MockClient:
    def __init__(self):
        self.orders = []
        self.account = type("Account", (), {"equity": "1000"})()
    
    def get_account(self):
        return self.account

    def get_all_positions(self):
        return [
            type("Pos", (), {"symbol": "VTI", "market_value": "400"})(),
            type("Pos", (), {"symbol": "VOO", "market_value": "400"})(),
            type("Pos", (), {"symbol": "BND", "market_value": "300"})()
        ]

    def submit_order(self, order):
        self.orders.append(order)


def test_trader_rebalance(monkeypatch):
    API_KEY = os.getenv("ALPACA_API_KEY_ID")
    SECRET_KEY = os.getenv("ALPACA_API_SECRET_KEY")
    trader = AlpacaTrader(API_KEY, SECRET_KEY, paper=True)
    mock = MockClient()
    monkeypatch.setattr(trader, "client", mock)

    target_alloc = {"VTI": 0.2, "VOO": 0.5, "BND": 0.3}
    trader.rebalance(target_alloc)

    assert len(mock.orders) == 3
