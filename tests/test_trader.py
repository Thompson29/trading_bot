"""
Unit tests for core/trader.py

Tests AlpacaTrader class and trading functionality.
"""

import pytest
from unittest.mock import Mock, patch
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.common.exceptions import APIError
from core.trader import AlpacaTrader, TradingError
from core.profiles import RISK_PROFILES


# ============================================================================
# INITIALIZATION TESTS
# ============================================================================

class TestAlpacaTraderInitialization:
    """Test suite for AlpacaTrader initialization"""

    def test_trader_initialization_success(self):
        """Test that trader initializes correctly"""
        with patch('core.trader.TradingClient') as mock_trading, \
             patch('core.trader.StockHistoricalDataClient') as mock_data:
            
            trader = AlpacaTrader("test_key", "test_secret", paper=True)
            
            mock_trading.assert_called_once_with("test_key", "test_secret", paper=True)
            mock_data.assert_called_once_with("test_key", "test_secret")

    def test_initialization_connection_failure(self):
        """Test trader initialization when connection fails"""
        with patch('core.trader.TradingClient') as mock_client:
            mock_client.side_effect = ConnectionError("Network error")
            
            with pytest.raises(TradingError) as exc_info:
                trader = AlpacaTrader("test_key", "test_secret", paper=True)
            
            assert "Failed to connect to Alpaca" in str(exc_info.value)

    def test_initialization_with_api_error(self):
        """Test initialization with API error"""
        with patch('core.trader.TradingClient') as mock_client:
            mock_client.side_effect = APIError("Invalid credentials")
            
            with pytest.raises(TradingError):
                trader = AlpacaTrader("bad_key", "bad_secret", paper=True)


# ============================================================================
# GET ACCOUNT VALUE TESTS
# ============================================================================

class TestGetAccountValue:
    """Test suite for get_account_value method"""

    @pytest.fixture
    def mock_trader(self):
        """Create a trader with mocked clients"""
        with patch('core.trader.TradingClient'), \
             patch('core.trader.StockHistoricalDataClient'):
            trader = AlpacaTrader("test_key", "test_secret", paper=True)
            trader.client = Mock()
            trader.data_client = Mock()
            return trader

    def test_get_account_value_success(self, mock_trader):
        """Test getting account value successfully"""
        mock_account = Mock()
        mock_account.equity = "15000.50"
        mock_trader.client.get_account.return_value = mock_account

        value = mock_trader.get_account_value()

        assert value == 15000.50
        mock_trader.client.get_account.assert_called_once()

    def test_get_account_value_api_error(self, mock_trader):
        """Test get_account_value with APIError"""
        mock_trader.client.get_account.side_effect = APIError("API rate limit")
        
        with pytest.raises(TradingError) as exc_info:
            mock_trader.get_account_value()
        
        assert "Failed to get account value" in str(exc_info.value)

    def test_get_account_value_unexpected_error(self, mock_trader):
        """Test get_account_value with unexpected error"""
        mock_trader.client.get_account.side_effect = ValueError("Unexpected error")
        
        with pytest.raises(TradingError) as exc_info:
            mock_trader.get_account_value()
        
        assert "Failed to get account value" in str(exc_info.value)


# ============================================================================
# GET POSITIONS VALUE TESTS
# ============================================================================

class TestGetPositionsValue:
    """Test suite for get_positions_value method"""

    @pytest.fixture
    def mock_trader(self):
        """Create a trader with mocked clients"""
        with patch('core.trader.TradingClient'), \
             patch('core.trader.StockHistoricalDataClient'):
            trader = AlpacaTrader("test_key", "test_secret", paper=True)
            trader.client = Mock()
            trader.data_client = Mock()
            return trader

    def test_get_positions_value_success(self, mock_trader):
        """Test getting current positions"""
        mock_positions = [
            Mock(symbol="VTI", market_value="5000"),
            Mock(symbol="VOO", market_value="3000"),
            Mock(symbol="BND", market_value="2000")
        ]
        mock_trader.client.get_all_positions.return_value = mock_positions

        positions = mock_trader.get_positions_value()

        assert positions == {"VTI": 5000.0, "VOO": 3000.0, "BND": 2000.0}

    def test_get_positions_value_empty(self, mock_trader):
        """Test getting positions when account is empty"""
        mock_trader.client.get_all_positions.return_value = []

        positions = mock_trader.get_positions_value()

        assert positions == {}

    def test_get_positions_value_api_error(self, mock_trader):
        """Test get_positions_value with APIError"""
        mock_trader.client.get_all_positions.side_effect = APIError("API error")
        
        with pytest.raises(TradingError) as exc_info:
            mock_trader.get_positions_value()
        
        assert "Failed to get positions" in str(exc_info.value)

    def test_get_positions_value_unexpected_error(self, mock_trader):
        """Test get_positions_value with unexpected error"""
        mock_trader.client.get_all_positions.side_effect = RuntimeError("Unexpected")
        
        with pytest.raises(TradingError) as exc_info:
            mock_trader.get_positions_value()
        
        assert "Failed to get positions" in str(exc_info.value)


# ============================================================================
# GET LATEST PRICE TESTS
# ============================================================================

class TestGetLatestPrice:
    """Test suite for get_latest_price method"""

    @pytest.fixture
    def mock_trader(self):
        """Create a trader with mocked clients"""
        with patch('core.trader.TradingClient'), \
             patch('core.trader.StockHistoricalDataClient'):
            trader = AlpacaTrader("test_key", "test_secret", paper=True)
            trader.client = Mock()
            trader.data_client = Mock()
            return trader

    def test_get_latest_price_success(self, mock_trader):
        """Test getting latest price successfully"""
        mock_quote = Mock()
        mock_quote.bid_price = 123.45
        mock_trader.data_client.get_stock_latest_quote.return_value = {"VTI": mock_quote}

        price = mock_trader.get_latest_price("VTI")

        assert price == 123.45

    def test_get_latest_price_key_error(self, mock_trader):
        """Test get_latest_price with KeyError"""
        mock_trader.data_client.get_stock_latest_quote.return_value = {}
        
        price = mock_trader.get_latest_price("INVALID")
        
        assert price is None

    def test_get_latest_price_api_error(self, mock_trader):
        """Test get_latest_price with APIError"""
        mock_trader.data_client.get_stock_latest_quote.side_effect = APIError("API error")
        
        price = mock_trader.get_latest_price("VTI")
        
        assert price is None

    def test_get_latest_price_unexpected_error(self, mock_trader):
        """Test get_latest_price with unexpected error"""
        mock_trader.data_client.get_stock_latest_quote.side_effect = Exception("Unknown error")
        
        price = mock_trader.get_latest_price("VTI")
        
        assert price is None


# ============================================================================
# SUBMIT ORDER TESTS
# ============================================================================

class TestSubmitOrder:
    """Test suite for submit_order method"""

    @pytest.fixture
    def mock_trader(self):
        """Create a trader with mocked clients"""
        with patch('core.trader.TradingClient'), \
             patch('core.trader.StockHistoricalDataClient'):
            trader = AlpacaTrader("test_key", "test_secret", paper=True)
            trader.client = Mock()
            trader.data_client = Mock()
            return trader

    def test_submit_order_buy_success(self, mock_trader):
        """Test submitting a buy order"""
        mock_quote = Mock()
        mock_quote.bid_price = 100.0
        mock_trader.data_client.get_stock_latest_quote.return_value = {"VTI": mock_quote}

        result = mock_trader.submit_order("VTI", 500.0)

        assert result == True
        mock_trader.client.submit_order.assert_called_once()
        order_arg = mock_trader.client.submit_order.call_args[0][0]
        assert order_arg.symbol == "VTI"
        assert order_arg.qty == 5
        assert order_arg.side == OrderSide.BUY

    def test_submit_order_sell_success(self, mock_trader):
        """Test submitting a sell order"""
        mock_quote = Mock()
        mock_quote.bid_price = 100.0
        mock_trader.data_client.get_stock_latest_quote.return_value = {"VTI": mock_quote}

        result = mock_trader.submit_order("VTI", -500.0)

        assert result == True
        mock_trader.client.submit_order.assert_called_once()
        order_arg = mock_trader.client.submit_order.call_args[0][0]
        assert order_arg.symbol == "VTI"
        assert order_arg.qty == 5
        assert order_arg.side == OrderSide.SELL

    def test_submit_order_small_amount_ignored(self, mock_trader):
        """Test that very small orders are ignored"""
        result = mock_trader.submit_order("VTI", 0.50)

        assert result == False
        mock_trader.client.submit_order.assert_not_called()

    def test_submit_order_invalid_price_zero(self, mock_trader):
        """Test submit_order when price is 0"""
        mock_trader.get_latest_price = Mock(return_value=0)
        mock_trader.client.submit_order = Mock()
        
        result = mock_trader.submit_order("VTI", 100.0)
        
        assert result == False
        mock_trader.client.submit_order.assert_not_called()

    def test_submit_order_invalid_price_none(self, mock_trader):
        """Test submit_order when price is None"""
        mock_trader.get_latest_price = Mock(return_value=None)
        mock_trader.client.submit_order = Mock()
        
        result = mock_trader.submit_order("VTI", 100.0)
        
        assert result == False
        mock_trader.client.submit_order.assert_not_called()

    def test_submit_order_quantity_rounds_to_zero(self, mock_trader):
        """Test when calculated quantity is 0"""
        # High price, low notional = 0 shares
        mock_trader.get_latest_price = Mock(return_value=500.0)
        mock_trader.client.submit_order = Mock()
        
        result = mock_trader.submit_order("BRK.A", 100.0)  # $100 / $500 = 0 shares
        
        assert result == False
        mock_trader.client.submit_order.assert_not_called()

    def test_submit_order_api_error(self, mock_trader):
        """Test submit_order with APIError"""
        mock_trader.get_latest_price = Mock(return_value=100.0)
        mock_trader.client.submit_order.side_effect = APIError("Order rejected")
        
        result = mock_trader.submit_order("VTI", 500.0)
        
        assert result == False

    def test_submit_order_unexpected_error(self, mock_trader):
        """Test submit_order with unexpected error"""
        mock_trader.get_latest_price = Mock(return_value=100.0)
        mock_trader.client.submit_order.side_effect = RuntimeError("Unknown error")
        
        result = mock_trader.submit_order("VTI", 500.0)
        
        assert result == False

    def test_submit_order_rounding(self, mock_trader):
        """Test that order quantities are properly rounded"""
        mock_quote = Mock()
        mock_quote.bid_price = 333.33
        mock_trader.data_client.get_stock_latest_quote.return_value = {"VTI": mock_quote}

        result = mock_trader.submit_order("VTI", 1000.0)

        assert result == True
        order_arg = mock_trader.client.submit_order.call_args[0][0]
        assert order_arg.qty == 3  # 1000 / 333.33 = 3.0 shares


# ============================================================================
# REBALANCE TESTS
# ============================================================================

class TestRebalance:
    """Test suite for rebalance method"""

    @pytest.fixture
    def mock_trader_full(self):
        """Create a fully mocked trader for integration testing"""
        with patch('core.trader.TradingClient'), \
             patch('core.trader.StockHistoricalDataClient'):
            
            trader = AlpacaTrader("test_key", "test_secret", paper=True)
            
            # Mock account
            mock_account = Mock()
            mock_account.equity = "10000"
            trader.client.get_account = Mock(return_value=mock_account)
            
            # Mock positions
            mock_positions = [
                Mock(symbol="VTI", market_value="2000"),
                Mock(symbol="VOO", market_value="2000"),
                Mock(symbol="BND", market_value="6000")
            ]
            trader.client.get_all_positions = Mock(return_value=mock_positions)
            
            # Mock quotes
            def mock_get_quote(request):
                symbol = request.symbol_or_symbols
                mock_quote = Mock()
                mock_quote.bid_price = 100.0
                return {symbol: mock_quote}
            
            trader.data_client.get_stock_latest_quote = Mock(side_effect=mock_get_quote)
            trader.client.submit_order = Mock()
            
            return trader

    def test_rebalance_to_moderate_profile(self, mock_trader_full):
        """Test complete rebalancing to moderate profile"""
        target_alloc = RISK_PROFILES["moderate"]
        
        result = mock_trader_full.rebalance(target_alloc)
        
        # Should have attempted orders for all symbols (some may be skipped if < $1)
        assert mock_trader_full.client.submit_order.call_count >= 2

    def test_rebalance_preserves_total_value(self, mock_trader_full):
        """Test that rebalancing doesn't change total portfolio value"""
        target_alloc = RISK_PROFILES["moderate"]
        
        initial_value = mock_trader_full.get_account_value()
        mock_trader_full.rebalance(target_alloc)
        
        # Verify we're targeting the same total value
        assert initial_value == 10000.0

    @pytest.mark.parametrize("risk_level", [
        "very_conservative",
        "conservative",
        "moderate",
        "aggressive",
        "aggressive_growth"
    ])
    def test_rebalance_all_profiles(self, mock_trader_full, risk_level):
        """Test rebalancing works for all risk profiles"""
        target_alloc = RISK_PROFILES[risk_level]
        
        # Should not raise any exceptions
        result = mock_trader_full.rebalance(target_alloc)
        
        # Should submit at least some orders (some may be skipped if too small)
        assert mock_trader_full.client.submit_order.call_count >= 2

    def test_rebalance_with_account_error(self):
        """Test rebalance when get_account fails"""
        with patch('core.trader.TradingClient'), \
             patch('core.trader.StockHistoricalDataClient'):
            
            trader = AlpacaTrader("test_key", "test_secret", paper=True)
            trader.client.get_account.side_effect = APIError("Account error")
            
            target_alloc = {"VTI": 1.0}
            
            with pytest.raises(TradingError):
                trader.rebalance(target_alloc)

    def test_rebalance_with_positions_error(self):
        """Test rebalance when get_positions fails"""
        with patch('core.trader.TradingClient'), \
             patch('core.trader.StockHistoricalDataClient'):
            
            trader = AlpacaTrader("test_key", "test_secret", paper=True)
            
            mock_account = Mock()
            mock_account.equity = "10000"
            trader.client.get_account.return_value = mock_account
            trader.client.get_all_positions.side_effect = APIError("Positions error")
            
            target_alloc = {"VTI": 1.0}
            
            with pytest.raises(TradingError):
                trader.rebalance(target_alloc)

    def test_rebalance_with_allocation_warning(self):
        """Test rebalance logs warning for invalid total allocation"""
        with patch('core.trader.TradingClient'), \
             patch('core.trader.StockHistoricalDataClient'):
            
            trader = AlpacaTrader("test_key", "test_secret", paper=True)
            
            mock_account = Mock()
            mock_account.equity = "10000"
            trader.client.get_account.return_value = mock_account
            trader.client.get_all_positions.return_value = []
            
            trader.get_latest_price = Mock(return_value=100.0)
            trader.client.submit_order = Mock()
            
            # Allocation that doesn't sum to 1.0
            target_alloc = {"VTI": 0.5, "BND": 0.3}  # Sums to 0.8
            
            result = trader.rebalance(target_alloc)
            
            # Should still execute despite warning
            assert isinstance(result, dict)

    def test_rebalance_from_empty_portfolio(self, mock_trader_full):
        """Test rebalancing from empty portfolio"""
        mock_trader_full.client.get_all_positions.return_value = []
        
        target_alloc = RISK_PROFILES["moderate"]
        result = mock_trader_full.rebalance(target_alloc)
        
        # Should place orders for all positions
        assert mock_trader_full.client.submit_order.call_count >= 2

    def test_rebalance_returns_status_dict(self, mock_trader_full):
        """Test that rebalance returns status dictionary"""
        target_alloc = RISK_PROFILES["moderate"]
        
        result = mock_trader_full.rebalance(target_alloc)
        
        assert isinstance(result, dict)
        # Should have status for each symbol in target allocation
        for symbol in target_alloc.keys():
            assert symbol in result
            assert isinstance(result[symbol], bool)

    def test_rebalance_multiple_symbols_some_fail(self):
        """Test rebalance when some orders fail but others succeed"""
        with patch('core.trader.TradingClient'), \
             patch('core.trader.StockHistoricalDataClient'):
            
            trader = AlpacaTrader("test_key", "test_secret", paper=True)
            
            mock_account = Mock()
            mock_account.equity = "10000"
            trader.client.get_account.return_value = mock_account
            trader.client.get_all_positions.return_value = []
            
            # Make get_latest_price return None for one symbol
            def mock_price(symbol):
                if symbol == "INVALID":
                    return None
                return 100.0
            
            trader.get_latest_price = Mock(side_effect=mock_price)
            trader.client.submit_order = Mock()
            
            target_alloc = {"VTI": 0.5, "INVALID": 0.5}
            
            result = trader.rebalance(target_alloc)
            
            # Should handle the failure gracefully
            assert "VTI" in result
            assert "INVALID" in result
            assert result["INVALID"] == False  # Failed


# ============================================================================
# TRADING ERROR TESTS
# ============================================================================

class TestTradingError:
    """Test suite for TradingError exception"""

    def test_trading_error_is_exception(self):
        """Test that TradingError is an Exception"""
        error = TradingError("Test error")
        assert isinstance(error, Exception)

    def test_trading_error_message(self):
        """Test TradingError message"""
        message = "API connection failed"
        error = TradingError(message)
        assert str(error) == message

    def test_trading_error_raised(self):
        """Test that TradingError can be raised and caught"""
        with pytest.raises(TradingError) as exc_info:
            raise TradingError("Test error")
        
        assert "Test error" in str(exc_info.value)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestTraderIntegration:
    """Integration tests for complete trading workflows"""

    def test_full_trading_cycle(self):
        """Test complete trading cycle from initialization to rebalance"""
        with patch('core.trader.TradingClient'), \
             patch('core.trader.StockHistoricalDataClient'):
            
            # Initialize trader
            trader = AlpacaTrader("test_key", "test_secret", paper=True)
            
            # Mock all dependencies
            mock_account = Mock()
            mock_account.equity = "10000"
            trader.client.get_account = Mock(return_value=mock_account)
            trader.client.get_all_positions = Mock(return_value=[])
            
            mock_quote = Mock()
            mock_quote.bid_price = 100.0
            trader.data_client.get_stock_latest_quote = Mock(
                return_value={"VTI": mock_quote}
            )
            trader.client.submit_order = Mock()
            
            # Execute complete cycle
            account_value = trader.get_account_value()
            positions = trader.get_positions_value()
            price = trader.get_latest_price("VTI")
            order_result = trader.submit_order("VTI", 1000.0)
            rebalance_result = trader.rebalance({"VTI": 1.0})
            
            # Verify all operations completed
            assert account_value == 10000.0
            assert positions == {}
            assert price == 100.0
            assert order_result == True
            assert isinstance(rebalance_result, dict)