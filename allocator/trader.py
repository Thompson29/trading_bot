from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.requests import MarketOrderRequest 
from alpaca.data.requests import StockLatestQuoteRequest
from alpaca.data.historical.stock import StockHistoricalDataClient
from allocator.utils import calculate_diffs


class AlpacaTrader:
    def __init__(self, api_key, secret_key, paper=True):
        self.client = TradingClient(api_key, secret_key, paper=paper)
        self.data_client = StockHistoricalDataClient(api_key, secret_key)

    def get_account_value(self):
        account = self.client.get_account()
        return float(account.equity)

    def get_positions_value(self):
        positions = self.client.get_all_positions()
        print(positions)
        # self.prices = {p.symbol: float(p.current_price) for p in positions}
        return {p.symbol: float(p.market_value) for p in positions}

    def submit_order(self, symbol: str, notional: float):
        if abs(notional) < 1:
            return
        side = OrderSide.BUY if notional > 0 else OrderSide.SELL
        quote_request = StockLatestQuoteRequest(symbol_or_symbols=symbol)
        price = self.data_client.get_stock_latest_quote(quote_request)[symbol].bid_price
        print(f"Latest price for {symbol}: {price}")
        quantity = round(abs(notional) / price)
        print(f"Submitting order for {symbol}: {quantity} at price {price}")
        order = MarketOrderRequest(
            symbol=symbol,
            # notional=abs(notional),
            qty=quantity,
            side=side,
            time_in_force=TimeInForce.DAY,
            extened_hours=True
        )
        self.client.submit_order(order)

    def rebalance(self, target_alloc: dict):
        current_value = self.get_account_value()
        current_alloc = self.get_positions_value()
        diffs = calculate_diffs(current_alloc, target_alloc, current_value)
        for symbol, notional_diff in diffs.items():
            print(f"Rebalancing {symbol}: {notional_diff}")
            self.submit_order(symbol, notional_diff)