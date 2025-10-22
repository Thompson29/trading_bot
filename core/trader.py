"""
Alpaca Trading Client

Handles connection to Alpaca API and executes portfolio rebalancing trades.
"""

import logging
from typing import Dict, Optional
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.requests import MarketOrderRequest 
from alpaca.data.requests import StockLatestQuoteRequest
from alpaca.data.historical.stock import StockHistoricalDataClient
from alpaca.common.exceptions import APIError
from core.utils import calculate_diffs

logger = logging.getLogger(__name__)


class TradingError(Exception):
    """Custom exception for trading-related errors"""
    pass


class AlpacaTrader:
    """
    Alpaca trading client for portfolio management
    
    Attributes:
        client: Alpaca trading client
        data_client: Alpaca historical data client
    """
    
    def __init__(self, api_key: str, secret_key: str, paper: bool = True):
        """
        Initialize Alpaca trader
        
        Args:
            api_key: Alpaca API key
            secret_key: Alpaca secret key
            paper: Whether to use paper trading (default: True)
        
        Raises:
            TradingError: If connection to Alpaca fails
        """
        try:
            self.client = TradingClient(api_key, secret_key, paper=paper)
            self.data_client = StockHistoricalDataClient(api_key, secret_key)
            logger.info(f"Initialized AlpacaTrader (paper={paper})")
        except Exception as e:
            logger.error(f"Failed to initialize Alpaca clients: {e}")
            raise TradingError(f"Failed to connect to Alpaca: {e}") from e

    def get_account_value(self) -> float:
        """
        Get current total account equity
        
        Returns:
            Total account value in dollars
        
        Raises:
            TradingError: If unable to retrieve account information
        """
        try:
            account = self.client.get_account()
            value = float(account.equity)
            logger.info(f"Account equity: ${value:,.2f}")
            return value
        except APIError as e:
            logger.error(f"Alpaca API error getting account: {e}")
            raise TradingError(f"Failed to get account value: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error getting account: {e}")
            raise TradingError(f"Failed to get account value: {e}") from e

    def get_positions_value(self) -> Dict[str, float]:
        """
        Get current positions with their market values
        
        Returns:
            Dictionary mapping symbols to their current market values
        
        Raises:
            TradingError: If unable to retrieve positions
        """
        try:
            positions = self.client.get_all_positions()
            position_values = {
                p.symbol: float(p.market_value) 
                for p in positions
            }
            
            if position_values:
                logger.info(f"Current positions: {len(position_values)} symbols")
                for symbol, value in position_values.items():
                    logger.debug(f"  {symbol}: ${value:,.2f}")
            else:
                logger.info("No current positions")
            
            return position_values
        except APIError as e:
            logger.error(f"Alpaca API error getting positions: {e}")
            raise TradingError(f"Failed to get positions: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error getting positions: {e}")
            raise TradingError(f"Failed to get positions: {e}") from e

    def get_latest_price(self, symbol: str) -> Optional[float]:
        """
        Get latest price for a symbol
        
        Args:
            symbol: Stock/ETF ticker symbol
        
        Returns:
            Latest bid price, or None if unavailable
        """
        try:
            quote_request = StockLatestQuoteRequest(symbol_or_symbols=symbol)
            quote_data = self.data_client.get_stock_latest_quote(quote_request)
            price = float(quote_data[symbol].bid_price)
            logger.debug(f"Latest price for {symbol}: ${price:.2f}")
            return price
        except KeyError:
            logger.warning(f"No price data available for {symbol}")
            return None
        except APIError as e:
            logger.error(f"API error getting price for {symbol}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error getting price for {symbol}: {e}")
            return None

    def submit_order(self, symbol: str, notional: float) -> bool:
        """
        Submit a market order for a given notional value
        
        Args:
            symbol: Stock/ETF ticker symbol
            notional: Dollar amount to buy (positive) or sell (negative)
        
        Returns:
            True if order was submitted successfully, False otherwise
        
        Note:
            Orders under $1 in absolute value are ignored
        """
        # Ignore very small orders
        if abs(notional) < 1:
            logger.debug(f"Skipping order for {symbol}: amount ${notional:.2f} below $1 threshold")
            return False
        
        try:
            # Determine buy or sell
            side = OrderSide.BUY if notional > 0 else OrderSide.SELL
            
            # Get current price
            price = self.get_latest_price(symbol)
            if price is None or price <= 0:
                logger.error(f"Cannot submit order for {symbol}: invalid price")
                return False
            
            # Calculate quantity (integer shares)
            quantity = int(abs(notional) / price)
            
            if quantity == 0:
                logger.warning(
                    f"Order for {symbol} rounds to 0 shares "
                    f"(${abs(notional):.2f} / ${price:.2f})"
                )
                return False
            
            logger.info(
                f"Submitting {side.value} order: {quantity} shares of {symbol} "
                f"@ ${price:.2f} (${notional:+,.2f})"
            )
            
            # Create and submit order
            order = MarketOrderRequest(
                symbol=symbol,
                qty=quantity,
                side=side,
                time_in_force=TimeInForce.DAY,
                extended_hours=False
            )
            
            order_response = self.client.submit_order(order)
            logger.info(f"✅ Order submitted successfully: {order_response.id}")
            return True
            
        except APIError as e:
            logger.error(f"Alpaca API error submitting order for {symbol}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error submitting order for {symbol}: {e}")
            return False

    def rebalance(self, target_alloc: Dict[str, float]) -> Dict[str, bool]:
        """
        Rebalance portfolio to match target allocation
        
        Args:
            target_alloc: Dictionary mapping symbols to target percentages (0-1)
        
        Returns:
            Dictionary mapping symbols to order success status
        
        Raises:
            TradingError: If unable to retrieve account information
        
        Note:
            This method will attempt to submit orders for all required trades,
            logging errors for any that fail but continuing with the rest.
        """
        logger.info("="*60)
        logger.info("Starting portfolio rebalancing")
        logger.info("="*60)
        
        # Validate target allocation
        total_alloc = sum(target_alloc.values())
        if not (0.99 <= total_alloc <= 1.01):
            logger.warning(
                f"Target allocation sums to {total_alloc:.2%}, "
                f"expected ~100%"
            )
        
        # Get current state
        try:
            current_value = self.get_account_value()
            current_alloc = self.get_positions_value()
        except TradingError:
            logger.error("Cannot rebalance: failed to get account information")
            raise
        
        # Calculate required trades
        diffs = calculate_diffs(current_alloc, target_alloc, current_value)
        
        logger.info(f"Current portfolio value: ${current_value:,.2f}")
        logger.info("Required trades:")
        
        # Sort by absolute value to show largest trades first
        sorted_diffs = sorted(
            diffs.items(), 
            key=lambda x: abs(x[1]), 
            reverse=True
        )
        
        total_to_trade = sum(abs(v) for v in diffs.values())
        logger.info(f"Total trading volume: ${total_to_trade:,.2f}")
        
        # Submit orders
        results = {}
        successful = 0
        failed = 0
        skipped = 0
        
        for symbol, notional_diff in sorted_diffs:
            current_pct = (current_alloc.get(symbol, 0) / current_value * 100 
                          if current_value > 0 else 0)
            target_pct = target_alloc[symbol] * 100
            
            logger.info(
                f"\n{symbol}: {current_pct:.1f}% → {target_pct:.1f}% "
                f"(${notional_diff:+,.2f})"
            )
            
            if abs(notional_diff) < 1:
                logger.info(f"  → Skipped (below $1 threshold)")
                results[symbol] = True
                skipped += 1
            else:
                success = self.submit_order(symbol, notional_diff)
                results[symbol] = success
                if success:
                    successful += 1
                else:
                    failed += 1
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("Rebalancing Summary:")
        logger.info(f"  ✅ Successful orders: {successful}")
        logger.info(f"  ⏭️  Skipped (too small): {skipped}")
        if failed > 0:
            logger.warning(f"  ❌ Failed orders: {failed}")
        logger.info("="*60)
        
        return results
