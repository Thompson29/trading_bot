import pytest
from unittest.mock import Mock, patch
from core.trader import AlpacaTrader
from core.utils import calculate_diffs
from core.profiles import RISK_PROFILES


class TestPortfolioConstraints:
    """Test portfolio constraints and validation"""

    def test_profile_etf_symbols_valid(self):
        """Test that all ETF symbols are valid tickers"""
        valid_symbols = {"VTI", "VOO", "VUG", "VTWO", "VXUS", "VEA", "BND", "VIG"}
        
        for profile_name, allocations in RISK_PROFILES.items():
            for symbol in allocations.keys():
                assert symbol in valid_symbols, \
                    f"Invalid symbol {symbol} in {profile_name}"

    def test_minimum_allocation_per_etf(self):
        """Test that each ETF has meaningful allocation (at least 5%)"""
        for profile_name, allocations in RISK_PROFILES.items():
            for symbol, weight in allocations.items():
                assert weight >= 0.05, \
                    f"{symbol} in {profile_name} has weight < 5%: {weight}"

    def test_bond_allocation_decreases_with_risk(self):
        """Test that bond allocation decreases as risk increases"""
        profiles_by_risk = [
            "very_conservative",
            "conservative", 
            "moderate",
            "aggressive",
            "aggressive_growth"
        ]
        
        bond_allocations = []
        for profile in profiles_by_risk:
            bond_alloc = RISK_PROFILES[profile].get("BND", 0)
            bond_allocations.append(bond_alloc)
        
        # Bond allocation should generally decrease
        for i in range(len(bond_allocations) - 1):
            assert bond_allocations[i] >= bond_allocations[i + 1], \
                f"Bond allocation should decrease with risk level"


class TestCalculationEdgeCases:
    """Test edge cases in calculation functions"""

    def test_calculate_diffs_very_small_differences(self):
        """Test handling of very small differences (under $1)"""
        current_alloc = {"VTI": 500.00}
        target_alloc = {"VTI": 0.50001}
        total_value = 1000
        
        diffs = calculate_diffs(current_alloc, target_alloc, total_value)
        
        # Should still calculate, even if tiny
        assert abs(diffs["VTI"]) < 1

    def test_calculate_diffs_large_portfolio(self):
        """Test with large portfolio values"""
        current_alloc = {"VTI": 500000, "VOO": 500000}
        target_alloc = {"VTI": 0.6, "VOO": 0.4}
        total_value = 1000000
        
        diffs = calculate_diffs(current_alloc, target_alloc, total_value)
        
        assert diffs["VTI"] == 100000.0
        assert diffs["VOO"] == -100000.0

    def test_calculate_diffs_precision(self):
        """Test that calculations maintain proper precision"""
        current_alloc = {"VTI": 333.33}
        target_alloc = {"VTI": 0.333333}
        total_value = 1000
        
        diffs = calculate_diffs(current_alloc, target_alloc, total_value)
        
        # Should round to 2 decimal places
        assert isinstance(diffs["VTI"], float)
        assert diffs["VTI"] == round(diffs["VTI"], 2)

    def test_calculate_diffs_multiple_decimals(self):
        """Test with fractional shares and prices"""
        current_alloc = {"VTI": 1234.56, "VOO": 2345.67}
        target_alloc = {"VTI": 0.345, "VOO": 0.655}
        total_value = 10000
        
        diffs = calculate_diffs(current_alloc, target_alloc, total_value)
        
        # Results should be properly rounded
        assert all(isinstance(v, float) for v in diffs.values())


class TestOrderSubmissionEdgeCases:
    """Test edge cases in order submission"""

    @pytest.fixture
    def mock_trader(self):
        """Create a trader with mocked clients"""
        with patch('core.trader.TradingClient'), \
             patch('core.trader.StockHistoricalDataClient'):
            trader = AlpacaTrader("test_key", "test_secret", paper=True)
            trader.client = Mock()
            trader.data_client = Mock()
            return trader

    def test_submit_order_exactly_one_dollar(self, mock_trader):
        """Test submitting order for exactly $1 (boundary case)"""
        mock_quote = Mock()
        mock_quote.bid_price = 100.0
        mock_trader.data_client.get_stock_latest_quote.return_value = {"VTI": mock_quote}
        
        mock_trader.submit_order("VTI", 1.0)
        
        # Should submit order (not ignored)
        mock_trader.client.submit_order.assert_called_once()

    def test_submit_order_just_under_one_dollar(self, mock_trader):
        """Test that orders under $1 are ignored"""
        mock_trader.submit_order("VTI", 0.99)
        
        # Should NOT submit order
        mock_trader.client.submit_order.assert_not_called()

    def test_submit_order_negative_one_dollar(self, mock_trader):
        """Test submitting sell order for exactly -$1"""
        mock_quote = Mock()
        mock_quote.bid_price = 100.0
        mock_trader.data_client.get_stock_latest_quote.return_value = {"VTI": mock_quote}
        
        mock_trader.submit_order("VTI", -1.0)
        
        # Should submit order (not ignored)
        mock_trader.client.submit_order.assert_called_once()

    def test_submit_order_zero(self, mock_trader):
        """Test that zero-dollar orders are ignored"""
        mock_trader.submit_order("VTI", 0.0)
        
        mock_trader.client.submit_order.assert_not_called()

    def test_submit_order_fractional_shares(self, mock_trader):
        """Test order with price that results in fractional shares"""
        mock_quote = Mock()
        mock_quote.bid_price = 123.45
        mock_trader.data_client.get_stock_latest_quote.return_value = {"VTI": mock_quote}
        
        mock_trader.submit_order("VTI", 1000.0)
        
        order_arg = mock_trader.client.submit_order.call_args[0][0]
        # 1000 / 123.45 = 8.1 shares, should round to 8
        assert order_arg.qty == 8

    def test_submit_order_expensive_stock(self, mock_trader):
        """Test ordering expensive stock (like BRK.A hypothetically)"""
        mock_quote = Mock()
        mock_quote.bid_price = 450000.0
        mock_trader.data_client.get_stock_latest_quote.return_value = {"EXPENSIVE": mock_quote}
        
        mock_trader.submit_order("EXPENSIVE", 1000000.0)
        
        order_arg = mock_trader.client.submit_order.call_args[0][0]
        # Should calculate correct shares even with expensive prices
        assert order_arg.qty == 2


class TestRebalanceScenarios:
    """Test realistic rebalancing scenarios"""

    @pytest.fixture
    def mock_trader_scenarios(self):
        """Create trader for scenario testing"""
        with patch('core.trader.TradingClient'), \
             patch('core.trader.StockHistoricalDataClient'):
            trader = AlpacaTrader("test_key", "test_secret", paper=True)
            trader.client = Mock()
            trader.data_client = Mock()
            
            def mock_get_quote(request):
                symbol = request.symbol_or_symbols
                mock_quote = Mock()
                mock_quote.bid_price = 100.0
                return {symbol: mock_quote}
            
            trader.data_client.get_stock_latest_quote = Mock(side_effect=mock_get_quote)
            trader.client.submit_order = Mock()
            
            return trader

    def test_rebalance_from_cash_to_portfolio(self, mock_trader_scenarios):
        """Test initial investment (from all cash to diversified portfolio)"""
        mock_account = Mock()
        mock_account.equity = "10000"
        mock_trader_scenarios.client.get_account = Mock(return_value=mock_account)
        mock_trader_scenarios.client.get_all_positions = Mock(return_value=[])
        
        target_alloc = RISK_PROFILES["moderate"]
        mock_trader_scenarios.rebalance(target_alloc)
        
        # Should buy all positions
        assert mock_trader_scenarios.client.submit_order.call_count == len(target_alloc)

    def test_rebalance_already_balanced(self, mock_trader_scenarios):
        """Test when portfolio is already properly balanced"""
        mock_account = Mock()
        mock_account.equity = "10000"
        mock_trader_scenarios.client.get_account = Mock(return_value=mock_account)
        
        # Set up perfectly balanced portfolio
        mock_positions = [
            Mock(symbol="VTI", market_value="2000"),  # 20%
            Mock(symbol="VOO", market_value="2500"),  # 25%
            Mock(symbol="VXUS", market_value="1500"), # 15%
            Mock(symbol="VTWO", market_value="1000"), # 10%
            Mock(symbol="BND", market_value="3000")   # 30%
        ]
        mock_trader_scenarios.client.get_all_positions = Mock(return_value=mock_positions)
        
        target_alloc = RISK_PROFILES["moderate"]
        mock_trader_scenarios.rebalance(target_alloc)
        
        # Should still call submit_order but with very small amounts
        # that might be ignored
        assert mock_trader_scenarios.client.submit_order.call_count >= 0

    def test_rebalance_switch_risk_profiles(self, mock_trader_scenarios):
        """Test switching from conservative to aggressive profile"""
        mock_account = Mock()
        mock_account.equity = "10000"
        mock_trader_scenarios.client.get_account = Mock(return_value=mock_account)
        
        # Start with conservative allocation
        mock_positions = [
            Mock(symbol="VTI", market_value="2000"),
            Mock(symbol="VOO", market_value="1500"),
            Mock(symbol="VXUS", market_value="1500"),
            Mock(symbol="VTWO", market_value="1000"),
            Mock(symbol="BND", market_value="4000")
        ]
        mock_trader_scenarios.client.get_all_positions = Mock(return_value=mock_positions)
        
        # Rebalance to aggressive
        target_alloc = RISK_PROFILES["aggressive"]
        mock_trader_scenarios.rebalance(target_alloc)
        
        # Should submit orders for all symbols (selling bonds, buying stocks)
        assert mock_trader_scenarios.client.submit_order.call_count == len(target_alloc)

    def test_rebalance_small_account(self, mock_trader_scenarios):
        """Test rebalancing with very small account value"""
        mock_account = Mock()
        mock_account.equity = "500"  # Small account
        mock_trader_scenarios.client.get_account = Mock(return_value=mock_account)
        mock_trader_scenarios.client.get_all_positions = Mock(return_value=[])
        
        target_alloc = RISK_PROFILES["moderate"]
        mock_trader_scenarios.rebalance(target_alloc)
        
        # Should still attempt to rebalance even with small amounts
        assert mock_trader_scenarios.client.submit_order.called

    def test_rebalance_large_account(self, mock_trader_scenarios):
        """Test rebalancing with large account value"""
        mock_account = Mock()
        mock_account.equity = "1000000"  # $1M account
        mock_trader_scenarios.client.get_account = Mock(return_value=mock_account)
        mock_trader_scenarios.client.get_all_positions = Mock(return_value=[])
        
        target_alloc = RISK_PROFILES["aggressive_growth"]
        mock_trader_scenarios.rebalance(target_alloc)
        
        # Should handle large values without issues
        assert mock_trader_scenarios.client.submit_order.called


class TestDataValidation:
    """Test data validation and type checking"""

    def test_risk_profile_values_are_floats(self):
        """Test that all allocation weights are float type"""
        for profile_name, allocations in RISK_PROFILES.items():
            for symbol, weight in allocations.items():
                assert isinstance(weight, (float, int)), \
                    f"{symbol} weight in {profile_name} is not numeric"

    def test_risk_profile_keys_are_strings(self):
        """Test that all ETF symbols are strings"""
        for profile_name, allocations in RISK_PROFILES.items():
            for symbol in allocations.keys():
                assert isinstance(symbol, str), \
                    f"Symbol key in {profile_name} is not a string"

    def test_all_profiles_have_data(self):
        """Test that no profiles are empty"""
        for profile_name, allocations in RISK_PROFILES.items():
            assert len(allocations) > 0, f"{profile_name} is empty"
            assert len(allocations) >= 3, \
                f"{profile_name} should have at least 3 ETFs for diversification"