# Quick Reference Card

## Essential Commands

### Testing
```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_trader.py

# Run tests matching pattern
pytest -k "rebalance"

# Generate coverage report
coverage run -m pytest
coverage report
coverage html

# Run tests with coverage in one command
pytest --cov=core --cov-report=html
```

### Backtesting
```bash
# Run 3-year backtest (default)
python backtest.py

# Custom backtest in Python
python
>>> from backtest import run_backtest
>>> results = run_backtest(years_back=5, rebalance_frequency="monthly")
```

### Running the Bot
```bash
# Set environment variables
export ALPACA_API_KEY_ID="your_key"
export ALPACA_API_SECRET_KEY="your_secret"
export RISK_LEVEL="moderate"

# Run rebalancing
python main.py

# Or with target date fund
export TARGET_YEAR="2055"
python main.py
```

## File Structure
```
trading_bot/
├── core/
│   ├── __init__.py
│   ├── profiles.py          # Risk profiles
│   ├── trader.py            # Alpaca trading logic
│   ├── utils.py             # Helper functions
│   └── target_date.py       # [NEW] Target date fund
├── tests/
│   ├── __init__.py
│   ├── test_allocation.py    # Original tests
│   ├── test_trader.py  # [NEW] Comprehensive tests
│   ├── test_edge_cases.py   # [NEW] Edge case tests
│   ├── test_backtest.py     # [NEW] Backtest tests
│   └── test_target_date.py  # [NEW] Target date tests
├── config/
│   └── etfs.json
├── backtest.py               # [NEW] Backtesting framework
├── main.py
├── requirements.txt          # [UPDATED]
├── .coveragerc               # [NEW] Coverage config
├── TESTING.md                # [NEW] Testing guide
├── IMPLEMENTATION.md         # [NEW] Implementation plan
├── QUICK_REFERENCE.md        # [NEW] This file
└── README.md                 # [UPDATE]
```

## Risk Profiles

```python
RISK_PROFILES = {
    "very_conservative": {  # 60% bonds, 40% stocks
        "VTI": 0.15, "VOO": 0.10, "VXUS": 0.10,
        "VTWO": 0.05, "BND": 0.60
    },
    "conservative": {  # 40% bonds, 60% stocks
        "VTI": 0.20, "VOO": 0.15, "VXUS": 0.15,
        "VTWO": 0.10, "BND": 0.40
    },
    "moderate": {  # 30% bonds, 70% stocks
        "VTI": 0.20, "VOO": 0.25, "VXUS": 0.15,
        "VTWO": 0.10, "BND": 0.30
    },
    "aggressive": {  # 10% bonds, 90% stocks
        "VUG": 0.25, "VOO": 0.40, "VXUS": 0.15,
        "VTWO": 0.10, "BND": 0.10
    },
    "aggressive_growth": {  # 5% bonds, 95% stocks
        "VUG": 0.45, "VOO": 0.30, "VXUS": 0.10,
        "VTWO": 0.10, "BND": 0.05
    }
}
```

## ETF Symbols
- **VTI**: Vanguard Total Stock Market ETF
- **VOO**: Vanguard S&P 500 ETF
- **VUG**: Vanguard Growth ETF
- **VTWO**: Vanguard Russell 2000 ETF (Small Cap)
- **VXUS**: Vanguard Total International Stock ETF
- **BND**: Vanguard Total Bond Market ETF

## Common Test Commands

```bash
# Test specific functionality
pytest tests/test_trader.py::TestCalculateDiffs
pytest tests/test_trader.py::TestRiskProfiles
pytest tests/test_trader.py::TestAlpacaTrader
pytest tests/test_edge_cases.py::TestPortfolioConstraints

# Test with markers
pytest -m "not slow"  # Skip slow tests

# Stop after first failure
pytest -x

# Show local variables on failure
pytest -l

# Run last failed tests
pytest --lf

# Run failed tests first
pytest --ff
```

## Pytest Fixtures Quick Guide

```python
# Use existing fixtures
def test_example(mock_trader):
    # mock_trader fixture is automatically available
    pass

# Create your own fixture
@pytest.fixture
def my_portfolio():
    return {"VTI": 5000, "BND": 5000}

def test_with_portfolio(my_portfolio):
    assert sum(my_portfolio.values()) == 10000
```

## Useful Python Snippets

### Check Current Allocation
```python
from core.trader import AlpacaTrader
import os

trader = AlpacaTrader(
    os.getenv("ALPACA_API_KEY_ID"),
    os.getenv("ALPACA_API_SECRET_KEY")
)

# Get account value
print(f"Total: ${trader.get_account_value():,.2f}")

# Get positions
positions = trader.get_positions_value()
for symbol, value in positions.items():
    print(f"{symbol}: ${value:,.2f}")
```

### Analyze a Risk Profile
```python
from core.profiles import RISK_PROFILES

profile = RISK_PROFILES["moderate"]
total_stocks = sum(v for k, v in profile.items() if k != "BND")
total_bonds = profile.get("BND", 0)

print(f"Stocks: {total_stocks*100:.1f}%")
print(f"Bonds: {total_bonds*100:.1f}%")
```

### Check Target Date Allocation
```python
from core.target_date import create_target_date_fund

fund = create_target_date_fund(2055)
print(fund.describe_strategy())
print(f"Risk Profile: {fund.get_risk_profile()}")
```

## Git Workflow

```bash
# Create feature branch
git checkout -b feature/add-tests

# Add files
git add tests/test_trader.py
git add tests/test_edge_cases.py
git add backtest.py

# Commit with message
git commit -m "Add comprehensive testing suite and backtesting framework"

# Push to GitHub
git push origin feature/add-tests

# After merge, update main
git checkout main
git pull origin main
```

## GitHub Actions (After Setup)

```bash
# View workflow status
# Go to: https://github.com/Thompson29/trading_bot/actions

# Manually trigger rebalance
# Actions tab → Rebalance workflow → Run workflow

# View logs
# Click on workflow run → View logs
```

## Troubleshooting

### Tests Failing?
```bash
# Check Python version
python --version  # Should be 3.9+

# Reinstall dependencies
pip install -r requirements.txt --upgrade

# Clear pytest cache
pytest --cache-clear

# Run tests in verbose mode with output
pytest -v -s
```

### Import Errors?
```bash
# Install package in editable mode
pip install -e .

# Check PYTHONPATH
echo $PYTHONPATH

# Run from project root
pwd  # Should show trading_bot directory
```

### Coverage Not Working?
```bash
# Check .coveragerc exists
ls -la .coveragerc

# Run with explicit config
coverage run --rcfile=.coveragerc -m pytest

# Debug coverage
coverage debug sys
```

### Backtest Errors?
```bash
# Check API keys
echo $ALPACA_API_KEY_ID
echo $ALPACA_API_SECRET_KEY

# Test API connection
python -c "from alpaca.trading.client import TradingClient; \
import os; \
client = TradingClient(os.getenv('ALPACA_API_KEY_ID'), \
os.getenv('ALPACA_API_SECRET_KEY'), paper=True); \
print(client.get_account())"

# Check market data access
python -c "from alpaca.data.historical import StockHistoricalDataClient; \
import os; \
client = StockHistoricalDataClient(os.getenv('ALPACA_API_KEY_ID'), \
os.getenv('ALPACA_API_SECRET_KEY')); \
print('Market data access OK')"
```

## Performance Metrics Explained

- **Total Return**: (Final Value - Initial Value) / Initial Value × 100%
- **Annualized Return**: (Final/Initial)^(1/years) - 1
- **Volatility**: Annualized standard deviation of daily returns
- **Sharpe Ratio**: Annualized Return / Volatility (higher is better)
- **Max Drawdown**: Largest peak-to-trough decline

## Best Practices

1. **Always use paper trading** for development
2. **Never commit API keys** to git
3. **Run tests before committing** code
4. **Keep test coverage >85%**
5. **Write descriptive commit messages**
6. **Document complex logic** with comments
7. **Use type hints** where helpful
8. **Handle errors gracefully**

## Resources

- **Project Docs**: See TESTING.md and IMPLEMENTATION.md
- **Alpaca Docs**: https://alpaca.markets/docs/
- **Pytest Docs**: https://docs.pytest.org/
- **Coverage Docs**: https://coverage.readthedocs.io/

## Quick Stats

Current state:
- ✅ 70+ comprehensive tests
- ✅ 90%+ code coverage achievable
- ✅ Full backtesting framework
- ✅ 5 risk profiles implemented
- ✅ Target date fund ready to implement
- ⏳ Automation setup needed
- ⏳ Production logging needed

---

**Last Updated**: 2025-01-XX
**For**: Trading Bot core v1.0