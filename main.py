import os
from allocator.trader import AlpacaTrader
from allocator.profiles import RISK_PROFILES

RISK_LEVEL = os.getenv("RISK_LEVEL", "moderate")
API_KEY = os.getenv("ALPACA_API_KEY_ID")
SECRET_KEY = os.getenv("ALPACA_API_SECRET_KEY")

def main():
    target_alloc = RISK_PROFILES.get(RISK_LEVEL)
    if not target_alloc:
        raise ValueError("Invalid risk level")

    trader = AlpacaTrader(API_KEY, SECRET_KEY, paper=True)
    trader.rebalance(target_alloc)
    print(f"✅ Rebalanced portfolio to match {RISK_LEVEL} risk profile.")

if __name__ == "__main__":
    main()