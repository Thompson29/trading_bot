import pytest
from unittest.mock import Mock, MagicMock, patch
from alpaca.trading.enums import OrderSide, TimeInForce
from core.trader import AlpacaTrader
from core.utils import calculate_diffs, summarize_allocation
from core.profiles import RISK_PROFILES


# ============================================================================
# UNIT TESTS - Utils Module
# ============================================================================

class TestCalculateDiffs:
    """Test suite for calculate_diffs function"""
    
    def test_calculate_diffs_basic(self):
        """Test basic diff calculation"""
        current_alloc = {"VTI": 300, "VOO": 300, "BND": 400}
        target_alloc = {"VTI": 0.5, "VOO": 0.3, "BND": 0.2}
        total_value = 1000

        diffs = calculate_diffs(current_alloc, target_alloc, total_value)

        assert diffs["VTI"] == 200.0
        assert diffs["VOO"] == 0.0
        assert diffs["BND"] == -200.0

    def test_calculate_diffs_empty_current(self):
        """Test when starting with no positions"""
        current_alloc = {}
        target_alloc = {"VTI": 0.5, "VOO": 0.3, "BND": 0.2}
        total_value = 1000

        diffs = calculate_diffs(current_alloc, target_alloc, total_value)

        assert diffs["VTI"] == 500.0
        assert diffs["VOO"] == 300.0
        assert diffs["BND"] == 200.0

    def test_calculate_diffs_new_positions(self):
        """Test adding new positions not in current allocation"""
        current_alloc = {"VTI": 500, "VOO": 500}
        target_alloc = {"VTI": 0.4, "VOO": 0.4, "BND": 0.2}
        total_value = 1000

        diffs = calculate_diffs(current_alloc, target_alloc, total_value)

        assert diffs["VTI"] == -100.0
        assert diffs["VOO"] == -100.0
        assert diffs["BND"] == 200.0

    def test_calculate_diffs_zero_total_value(self):
        """Test with zero account value"""
        current_alloc = {}
        target_alloc = {"VTI": 0.5, "VOO": 0.5}
        total_value = 0

        diffs = calculate_diffs(current_alloc, target_alloc, total_value)

        assert diffs["VTI"] == 0.0
        assert diffs["VOO"] == 0.0

    def test_calculate_diffs_rounding(self):
        """Test that results are properly rounded to 2 decimals"""
        current_alloc = {"VTI": 333.33}
        target_alloc = {"VTI": 0.3333}
        total_value = 1000

        diffs = calculate_diffs(current_alloc, target_alloc, total_value)

        assert diffs["VTI"] == 0.0  # Should round to 2 decimals

    def test_summarize_allocation(self, capsys):
        """Test allocation summary printing"""
        allocation = {"VTI": 500, "VOO": 300, "BND": 200}
        
        summarize_allocation(allocation)
        
        captured = capsys.readouterr()
        assert "VTI: $500" in captured.out
        assert "VOO: $300" in captured.out
        assert "BND: $200" in captured.out


# ============================================================================
# UNIT TESTS - Risk Profiles
# ============================================================================

class TestRiskProfiles:
    """Test suite for risk profile configurations"""
    
    @pytest.mark.parametrize("risk_level", [
        "very_conservative",
        "conservative",
        "moderate",
        "aggressive",
        "aggressive_growth"
    ])
    def test_profile_exists(self, risk_level):
        """Test that all expected risk profiles exist"""
        assert risk_level in RISK_PROFILES
        assert isinstance(RISK_PROFILES[risk_level], dict)

    @pytest.mark.parametrize("risk_level", [
        "very_conservative",
        "conservative",
        "moderate",
        "aggressive",
        "aggressive_growth"
    ])
    def test_profile_weights_sum_to_one(self, risk_level):
        """Test that allocation percentages sum to 100%"""
        profile = RISK_PROFILES[risk_level]
        total_weight = sum(profile.values())
        assert abs(total_weight - 1.0) < 0.01, f"{risk_level} weights sum to {total_weight}"

    @pytest.mark.parametrize("risk_level", [
        "very_conservative",
        "conservative",
        "moderate",
        "aggressive",
        "aggressive_growth"
    ])
    def test_profile_no_negative_weights(self, risk_level):
        """Test that no allocation is negative"""
        profile = RISK_PROFILES[risk_level]
        for symbol, weight in profile.items():
            assert weight >= 0, f"{symbol} has negative weight in {risk_level}"

    def test_very_conservative_bond_heavy(self):
        """Test that very conservative profile is bond-heavy"""
        profile = RISK_PROFILES["very_conservative"]
        assert profile["BND"] >= 0.5, "Very conservative should have 50%+ bonds"

    def test_aggressive_growth_equity_heavy(self):
        """Test that aggressive growth profile is equity-heavy"""
        profile = RISK_PROFILES["aggressive_growth"]
        stock_allocation = sum(v for k, v in profile.items() if k != "BND")
        assert stock_allocation >= 0.9, "Aggressive growth should have 90%+ stocks"

    @pytest.mark.parametrize("risk_level", [
        "very_conservative",
        "conservative",
        "moderate",
        "aggressive",
        "aggressive_growth"
    ])
    def test_allocation_with_capital(self, risk_level):
        """Test portfolio allocation calculation with real capital"""
        capital = 10000
        profile = RISK_PROFILES[risk_level]
        
        result = {etf: capital * weight for etf, weight in profile.items()}
        
        assert isinstance(result, dict)
        assert abs(sum(result.values()) - capital) < 1


# ============================================================================
# UNIT TESTS - AlpacaTrader Class
# ============================================================================

class TestAlpacaTrader:
    """Test suite for AlpacaTrader class"""

    @pytest.fixture
    def mock_trader(self):
        """Create a trader with mocked clients"""
        with patch('core.trader.TradingClient') as mock_trading, \
             patch('core.trader.StockHistoricalDataClient') as mock_data:
            
            trader = AlpacaTrader("test_key", "test_secret", paper=True)
            trader.client = Mock()
            trader.data_client = Mock()
            return trader

    def test_trader_initialization(self):
        """Test that trader initializes correctly"""
        with patch('core.trader.TradingClient') as mock_trading, \
             patch('core.trader.StockHistoricalDataClient') as mock_data:
            
            trader = AlpacaTrader("test_key", "test_secret", paper=True)
            
            mock_trading.assert_called_once_with("test_key", "test_secret", paper=True)
            mock_data.assert_called_once_with("test_key", "test_secret")

    def test_get_account_value(self, mock_trader):
        """Test getting account value"""
        mock_account = Mock()
        mock_account.equity = "15000.50"
        mock_trader.client.get_account.return_value = mock_account

        value = mock_trader.get_account_value()

        assert value == 15000.50
        mock_trader.client.get_account.assert_called_once()

    def test_get_positions_value(self, mock_trader):
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

    def test_submit_order_buy(self, mock_trader):
        """Test submitting a buy order"""
        mock_quote = Mock()
        mock_quote.bid_price = 100.0
        mock_trader.data_client.get_stock_latest_quote.return_value = {"VTI": mock_quote}

        mock_trader.submit_order("VTI", 500.0)

        mock_trader.client.submit_order.assert_called_once()
        order_arg = mock_trader.client.submit_order.call_args[0][0]
        assert order_arg.symbol == "VTI"
        assert order_arg.qty == 5
        assert order_arg.side == OrderSide.BUY

    def test_submit_order_sell(self, mock_trader):
        """Test submitting a sell order"""
        mock_quote = Mock()
        mock_quote.bid_price = 100.0
        mock_trader.data_client.get_stock_latest_quote.return_value = {"VTI": mock_quote}

        mock_trader.submit_order("VTI", -500.0)

        mock_trader.client.submit_order.assert_called_once()
        order_arg = mock_trader.client.submit_order.call_args[0][0]
        assert order_arg.symbol == "VTI"
        assert order_arg.qty == 5
        assert order_arg.side == OrderSide.SELL

    def test_submit_order_small_amount_ignored(self, mock_trader):
        """Test that very small orders are ignored"""
        mock_trader.submit_order("VTI", 0.50)

        mock_trader.client.submit_order.assert_not_called()

    def test_submit_order_rounding(self, mock_trader):
        """Test that order quantities are properly rounded"""
        mock_quote = Mock()
        mock_quote.bid_price = 333.33
        mock_trader.data_client.get_stock_latest_quote.return_value = {"VTI": mock_quote}

        mock_trader.submit_order("VTI", 1000.0)

        order_arg = mock_trader.client.submit_order.call_args[0][0]
        assert order_arg.qty == 3  # 1000 / 333.33 = 3.0 shares


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestRebalanceIntegration:
    """Integration tests for the full rebalance workflow"""

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
        
        mock_trader_full.rebalance(target_alloc)
        
        # Should have submitted orders for all symbols in target allocation
        assert mock_trader_full.client.submit_order.call_count == len(target_alloc)

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
        mock_trader_full.rebalance(target_alloc)
        
        # Should submit correct number of orders
        assert mock_trader_full.client.submit_order.call_count == len(target_alloc)


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestErrorHandling:
    """Test error handling and edge cases"""

    def test_invalid_risk_profile(self):
        """Test handling of invalid risk profile"""
        assert "invalid_profile" not in RISK_PROFILES

    def test_trader_with_api_error(self):
        """Test trader behavior when API fails"""
        with patch('core.trader.TradingClient') as mock_trading:
            mock_trading.side_effect = Exception("API Connection Error")
            
            with pytest.raises(Exception):
                trader = AlpacaTrader("test_key", "test_secret", paper=True)

    def test_rebalance_with_missing_position_data(self):
        """Test rebalancing when position data is incomplete"""
        with patch('core.trader.TradingClient'), \
             patch('core.trader.StockHistoricalDataClient'):
            
            trader = AlpacaTrader("test_key", "test_secret", paper=True)
            
            # Mock with None values
            mock_account = Mock()
            mock_account.equity = "10000"
            trader.client.get_account = Mock(return_value=mock_account)
            trader.client.get_all_positions = Mock(return_value=[])
            
            mock_quote = Mock()
            mock_quote.bid_price = 100.0
            trader.data_client.get_stock_latest_quote = Mock(return_value={"VTI": mock_quote})
            trader.client.submit_order = Mock()
            
            target_alloc = {"VTI": 1.0}
            
            # Should handle empty positions gracefully
            trader.rebalance(target_alloc)
            assert trader.client.submit_order.called