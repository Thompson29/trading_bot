# Testing Guide

This guide covers the comprehensive testing suite for the Trading Bot core project.

## Overview

The testing suite includes:
- **Unit Tests**: Test individual functions and methods in isolation
- **Integration Tests**: Test complete workflows and component interactions
- **Edge Case Tests**: Test boundary conditions and error handling
- **Backtest Tests**: Validate backtesting functionality

## Test Structure

```
tests/
├── __init__.py
├── test_allocation.py          # Original basic tests
├── test_trader.py # Comprehensive unit & integration tests
├── test_edge_cases.py         # Edge cases and validation tests
└── test_backtest.py           # Backtesting framework tests
```

## Running Tests

### Run All Tests
```bash
pytest
```

### Run with Verbose Output
```bash
pytest -v
```

### Run Specific Test File
```bash
pytest tests/test_trader.py
pytest tests/test_edge_cases.py
pytest tests/test_backtest.py
```

### Run Specific Test Class
```bash
pytest tests/test_trader.py::TestCalculateDiffs
```

### Run Specific Test
```bash
pytest tests/test_trader.py::TestCalculateDiffs::test_calculate_diffs_basic
```

### Run Tests Matching Pattern
```bash
pytest -k "rebalance"  # Run all tests with "rebalance" in name
pytest -k "edge"       # Run all edge case tests
```

## Code Coverage

### Generate Coverage Report
```bash
# Run tests with coverage
coverage run -m pytest

# View coverage report in terminal
coverage report

# Generate HTML coverage report
coverage html

# Open HTML report in browser
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Coverage Goals
- **Overall Coverage**: > 85%
- **Core Modules** (trader.py, utils.py): > 95%
- **Risk Profiles** (profiles.py): 100%

### View Coverage by Module
```bash
coverage report --show-missing
```

Example output:
```
Name                    Stmts   Miss  Cover   Missing
-----------------------------------------------------
core/__init__.py       0      0   100%
core/profiles.py       5      0   100%
core/trader.py        45      3    93%   78-80
core/utils.py         12      0   100%
-----------------------------------------------------
TOTAL                      62      3    95%
```

## Test Categories

### 1. Unit Tests (test_trader.py)

#### Utils Tests
- `TestCalculateDiffs`: Tests diff calculation logic
  - Basic calculations
  - Empty portfolios
  - New positions
  - Zero values
  - Rounding precision

#### Risk Profile Tests
- `TestRiskProfiles`: Validates risk profile configurations
  - Profile existence
  - Weight summation (must equal 100%)
  - No negative weights
  - Bond allocation decreases with risk
  - Capital allocation calculations

#### Trader Tests
- `TestAlpacaTrader`: Tests trading functionality
  - Initialization
  - Account value retrieval
  - Position value retrieval
  - Order submission (buy/sell)
  - Order quantity rounding

#### Integration Tests
- `TestRebalanceIntegration`: End-to-end rebalancing
  - Complete rebalancing workflow
  - Value preservation
  - All risk profiles

#### Error Handling Tests
- `TestErrorHandling`: Tests error scenarios
  - Invalid risk profiles
  - API errors
  - Missing data

### 2. Edge Case Tests (test_edge_cases.py)

#### Portfolio Constraints
- Valid ETF symbols
- Minimum allocations
- Risk-appropriate bond allocations

#### Calculation Edge Cases
- Very small differences (< $1)
- Large portfolio values
- Precision handling
- Fractional shares

#### Order Submission Edge Cases
- $1 boundary (minimum order)
- Zero orders
- Expensive stocks
- Fractional share rounding

#### Realistic Scenarios
- Initial investment (all cash)
- Already balanced portfolio
- Profile switching
- Small/large accounts

### 3. Backtest Tests (test_backtest.py)

#### Core Functionality
- Portfolio value calculations
- Rebalancing logic
- Rebalance date generation
- Metrics calculations

#### Strategy Testing
- Valid profiles
- Invalid profiles
- Bull/bear/volatile markets

#### Results Handling
- JSON export
- Markdown report generation
- Error handling

## Running Backtests

### Quick Backtest (3 years)
```bash
python -m backtest
```

### Custom Backtest
```python
from backtest.backtest import run_backtest

# 5-year backtest with monthly rebalancing
results = run_backtest(
    years_back=5,
    initial_capital=10000.0,
    rebalance_frequency="monthly"
)
```

### Backtest Single Profile
```python
from backtest.backtest import PortfolioBacktester
from datetime import datetime, timedelta
import os

API_KEY = os.getenv("ALPACA_API_KEY_ID")
SECRET_KEY = os.getenv("ALPACA_API_SECRET_KEY")

backtester = PortfolioBacktester(API_KEY, SECRET_KEY)

end_date = datetime.now()
start_date = end_date - timedelta(days=365*3)

result = backtester.backtest_strategy(
    "aggressive_growth",
    start_date,
    end_date,
    initial_capital=10000.0,
    rebalance_frequency="quarterly"
)

print(f"Total Return: {result['metrics']['total_return_pct']}%")
print(f"Sharpe Ratio: {result['metrics']['sharpe_ratio']}")
```

## Continuous Integration

### GitHub Actions Workflow

Create `.github/workflows/test.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Run tests with coverage
      run: |
        coverage run -m pytest
        coverage report
        coverage xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

## Best Practices

### Writing New Tests

1. **Use Descriptive Names**
   ```python
   def test_rebalance_from_cash_to_portfolio(self):
       """Test initial investment from all cash"""
   ```

2. **Follow AAA Pattern**
   ```python
   def test_example(self):
       # Arrange - Set up test data
       portfolio = create_test_portfolio()
       
       # Act - Execute the function
       result = portfolio.rebalance()
       
       # Assert - Verify the result
       assert result.is_balanced()
   ```

3. **Use Fixtures for Common Setup**
   ```python
   @pytest.fixture
   def mock_trader(self):
       """Reusable trader fixture"""
       return create_mock_trader()
   ```

4. **Test One Thing Per Test**
   - Each test should verify one specific behavior
   - Makes failures easier to diagnose

5. **Use Parameterized Tests for Similar Cases**
   ```python
   @pytest.mark.parametrize("risk_level", [
       "conservative",
       "moderate",
       "aggressive"
   ])
   def test_all_profiles(self, risk_level):
       # Test logic
   ```

### Mocking External Dependencies

Always mock external API calls in unit tests:

```python
@patch('core.trader.TradingClient')
def test_with_mock_client(self, mock_client):
    # Test logic without hitting real API
    pass
```

### Testing Checklist

Before committing code:
- [ ] All tests pass: `pytest`
- [ ] Coverage is adequate: `coverage report`
- [ ] No security issues (check for hardcoded credentials)
- [ ] Tests are documented
- [ ] Edge cases are covered

## Troubleshooting

### Tests Fail Due to Missing API Keys
```bash
# Set dummy keys for testing
export ALPACA_API_KEY_ID="test_key"
export ALPACA_API_SECRET_KEY="test_secret"
```

### Import Errors
```bash
# Ensure you're in the project root
pwd

# Reinstall in development mode
pip install -e .
```

### Coverage Not Showing All Files
Check that:
1. `.coveragerc` is in the project root
2. `source = core` points to your source directory
3. You're running from the project root

## Additional Resources

- [pytest documentation](https://docs.pytest.org/)
- [coverage.py documentation](https://coverage.readthedocs.io/)
- [Python Testing Best Practices](https://docs.python-guide.org/writing/tests/)
- [Alpaca API Documentation](https://alpaca.markets/docs/)

## Getting Help

If tests are failing:
1. Read the test failure message carefully
2. Check if API keys are set correctly
3. Verify all dependencies are installed
4. Run with `-v` flag for more details: `pytest -v`
5. Run specific failing test in isolation

For backtest issues:
1. Verify API keys have market data permissions
2. Check date ranges (markets closed on weekends/holidays)
3. Ensure symbols exist in Alpaca's database
4. Review backtest logs for specific errors
