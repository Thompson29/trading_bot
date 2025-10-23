# Portfolio Trade Bot

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

An automated portfolio rebalancing bot that manages a diversified Vanguard ETF portfolio using the Alpaca API. Features multiple risk profiles, comprehensive backtesting, and 90%+ test coverage.

> **⚠️ Disclaimer**: This trade bot is for educational purposes only and is intended to be used only with paper (non-live) brokerage accounts. This is not investing advice.

## 🎯 Features

- **5 Risk Profiles**: From very conservative (60% bonds) to aggressive growth (95% stocks)
- **Automated Rebalancing**: Maintains target allocation percentages
- **Comprehensive Testing**: 70+ tests with >90% code coverage
- **Historical Backtesting**: Evaluate strategies using 3-5 years of data
- **Professional Logging**: Detailed logs for auditing and debugging
- **Error Handling**: Graceful handling of API failures and edge cases
- **Paper Trading**: Safe testing environment with real market data

## 📊 Risk Profiles

| Profile | Stocks | Bonds | Typical Use Case |
|---------|--------|-------|------------------|
| Very Conservative | 40% | 60% | Near retirement, capital preservation |
| Conservative | 60% | 40% | Low risk tolerance, income focus |
| Moderate | 70% | 30% | Balanced growth and stability |
| Aggressive | 90% | 10% | Long-term growth, higher risk tolerance |
| Aggressive Growth | 95% | 5% | Maximum growth, 30+ year horizon |

### ETF Composition

- **VTI**: Vanguard Total Stock Market ETF (U.S. broad market)
- **VOO**: Vanguard S&P 500 ETF (Large cap U.S.)
- **VUG**: Vanguard Growth ETF (Growth stocks)
- **VTWO**: Vanguard Russell 2000 ETF (Small cap U.S.)
- **VXUS**: Vanguard Total International Stock ETF (Ex-U.S. stocks)
- **BND**: Vanguard Total Bond Market ETF (U.S. bonds)

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.9 or higher
- An Alpaca paper trading account ([sign up here](https://alpaca.markets/))

### 2. Installation

```bash
# Clone the repository
git clone https://github.com/Thompson29/trading_bot.git
cd trading_bot

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your Alpaca API credentials
vi .env  # or use your preferred editor
```

Required environment variables:
```bash
ALPACA_API_KEY_ID=your_api_key_here
ALPACA_API_SECRET_KEY=your_secret_key_here
RISK_LEVEL=moderate  # Choose your risk profile
```

### 4. Run the Bot

```bash
# Run portfolio rebalancing
python main.py
```

## 🧪 Testing

The project includes comprehensive testing with >90% code coverage.

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Generate coverage report
coverage run -m pytest
coverage report
coverage html  # Creates htmlcov/index.html

# Run specific test categories
pytest tests/test_trader.py  # Unit & integration tests
pytest tests/test_edge_cases.py          # Edge cases
pytest tests/test_backtest.py            # Backtesting tests
```

See [TESTING.md](TESTING.md) for detailed testing documentation.

## 📈 Backtesting

Evaluate historical performance of risk profiles:

```bash
# Run 3-year backtest (default)
python backtest.py
```

This generates:
- `backtest_results.json`: Machine-readable results
- `BACKTEST_RESULTS.md`: Human-readable report

### Custom Backtests

```python
from backtest.backtest import run_backtest

# 5-year backtest with monthly rebalancing
results = run_backtest(
    years_back=5,
    initial_capital=10000.0,
    rebalance_frequency="monthly"  # or "quarterly", "yearly"
)
```

### Example Results

```
Risk Profile       | Total Return | Sharpe Ratio | Max Drawdown
-------------------|--------------|--------------|-------------
Very Conservative  |    +15.2%    |     0.56     |    -7.2%
Conservative       |    +22.5%    |     0.62     |   -10.5%
Moderate           |    +35.8%    |     0.75     |   -15.8%
Aggressive         |    +48.2%    |     0.79     |   -22.1%
Aggressive Growth  |    +62.5%    |     0.81     |   -28.5%
```

## 📁 Project Structure

```
trading_bot/
├── core/              # Core trading logic
│   ├── __init__.py
│   ├── profiles.py        # Risk profile definitions
│   ├── trader.py          # Alpaca API integration
│   └── utils.py           # Helper functions
├── docs/                  # Project documentation
├── tests/                 # Comprehensive test suite
│   ├── test_trader.py
│   ├── test_edge_cases.py
│   └── test_backtest.py
├── logs/                  # Trading logs (created automatically)
├── backtest.py           # Backtesting framework
├── main.py               # Main entry point
├── requirements.txt      # Python dependencies
├── .env.example          # Environment variable template
├── .gitignore            # Git ignore rules
├── .coveragerc           # Coverage configuration
├── TESTING.md            # Testing documentation
└── README.md             # This file
```

## 🔧 How It Works

1. **Connect to Alpaca**: Establishes connection to paper trading account
2. **Fetch Current State**: Retrieves account value and current positions
3. **Calculate Differences**: Determines required trades to match target allocation
4. **Execute Orders**: Submits market orders for rebalancing
5. **Log Results**: Records all transactions and outcomes

### Example Rebalancing

```
Current Portfolio: $10,000
- VTI: $2,000 (20%)
- VOO: $2,000 (20%)
- BND: $6,000 (60%)

Target (Moderate): 
- VTI: 20% → $2,000 ✓ No change
- VOO: 25% → $2,500 (Buy $500)
- VXUS: 15% → $1,500 (Buy $1,500)
- VTWO: 10% → $1,000 (Buy $1,000)
- BND: 30% → $3,000 (Sell $3,000)
```

## 🛡️ Safety Features

- **Paper Trading Default**: Uses paper trading by default (no real money at risk)
- **Order Validation**: Skips orders under $1 and validates prices
- **Error Handling**: Gracefully handles API failures and continues with other orders
- **Comprehensive Logging**: All actions logged for audit trail
- **Environment Validation**: Checks configuration before executing trades

## 📊 Performance Metrics

The backtesting framework calculates:

- **Total Return**: Overall gain/loss percentage
- **Annualized Return**: Year-over-year average return
- **Volatility**: Annualized standard deviation (risk measure)
- **Sharpe Ratio**: Risk-adjusted return (higher is better)
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Best/Worst Day**: Largest single-day gains and losses

## 🔄 Automation (Coming Soon)

Future enhancements include:
- GitHub Actions workflow for quarterly rebalancing
- Target date fund with automatic risk reduction
- Email notifications for rebalancing events
- Performance dashboard

See [IMPLEMENTATION.md](docs/IMPLEMENTATION.md) for roadmap details.

## 📚 Documentation

- [TESTING.md](docs/TESTING.md) - Comprehensive testing guide
- [IMPLEMENTATION.md](docs/IMPLEMENTATION.md) - Implementation roadmap
- [QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md) - Command reference

## 🤝 Contributing

This is a personal portfolio project, but suggestions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 🐛 Troubleshooting

### Common Issues

**"Missing required environment variables"**
- Ensure `.env` file exists and contains your Alpaca API keys
- Check that variable names match exactly (case-sensitive)

**"Failed to connect to Alpaca"**
- Verify your API keys are correct
- Check that you're using paper trading keys (not live trading)
- Ensure you have internet connectivity

**Import errors**
- Make sure you're in the virtual environment: `source venv/bin/activate`
- Reinstall dependencies: `pip install -r requirements.txt`

**Tests failing**
- Run from project root directory
- Ensure all dependencies are installed
- Check that you have pytest installed: `pip install pytest`

### Getting Help

1. Check the [TESTING.md](TESTING.md) and [QUICK_REFERENCE.md](QUICK_REFERENCE.md) docs
2. Review logs in the `logs/` directory
3. Enable debug logging: Set `LOG_LEVEL=DEBUG` in `.env`
4. Open an issue with full error messages and logs

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚖️ Legal Disclaimer

This software is provided for educational and informational purposes only. It does not constitute financial advice, investment advice, trading advice, or any other sort of advice. You should not treat any of the software's content as such.

The author(s) are not responsible for any losses or damages resulting from the use of this software. Trading stocks and ETFs involves substantial risk and is not suitable for every investor. Past performance is not indicative of future results.

Always consult with a qualified financial advisor before making investment decisions.

## 🙏 Acknowledgments

- **Alpaca**: For providing commission-free trading API
- **Vanguard**: For low-cost, diversified ETFs
- **pytest**: For excellent testing framework
- **Python community**: For amazing open-source tools

## 📧 Contact

Thompson29 - [GitHub Profile](https://github.com/Thompson29)

Project Link: [https://github.com/Thompson29/trading_bot](https://github.com/Thompson29/trading_bot)

---

**Built with Python 🐍 | Powered by Alpaca 🦙 | Invested in Your Future 📈**