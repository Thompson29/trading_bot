# Trade Bot Allocator
Rebalances a Vanguard ETF portfolio based on the users risk profile using the Alpaca API.
* Disclaimer: This trade bot is for educational purposes only and is intended to be used only with paper (non-live) brokerage accounts. This is not investing advice.

## Create Alpaca Paper Account
Create an Alpaca paper trading account on https://alpaca.markets. Generate your API Keys from the Alpca dashboard and save them.

## Setup Development Environment
Add the Alpaca paper API Keys to your environment:
```bash
# Alpaca API paper trading endpoint
export ALPACA_API_BASE_URL="https://paper-api.alpaca.markets/v2"
export ALPACA_API_KEY_ID="<Your API Key ID>"
export ALPACA_API_SECRET_KEY="<Your generated API Secret Key>"
```
Tip: Add these keys to your .bashrc to save them in your environment.

Create the virtual environment and pip install the requirments:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running the trading bot
Set an environment variable to define your risk profile. Valid risk levels include:
 - "very_conservative"
 - "conservative"
 - "moderate"
 - "aggressive"
 - "aggressive_growth"

```bash
export RISK_LEVEL="moderate"
```

To run unit tests:
```bash
pytest -v
```

To execute trades in your paper account based on your risk profile:
```bash
python main.py
```