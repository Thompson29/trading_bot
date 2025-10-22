import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
from backtest.backtest import PortfolioBacktester
from core.profiles import RISK_PROFILES


class TestPortfolioBacktester:
    """Test suite for PortfolioBacktester class"""

    @pytest.fixture
    def backtester(self):
        """Create a backtester instance with mocked client"""
        with patch('backtest.backtest.StockHistoricalDataClient'):
            return PortfolioBacktester("test_key", "test_secret")

    def test_initialization(self):
        """Test that backtester initializes correctly"""
        with patch('backtest.backtest.StockHistoricalDataClient') as mock_client:
            backtester = PortfolioBacktester("test_key", "test_secret")
            mock_client.assert_called_once_with("test_key", "test_secret")
            assert backtester.results == {}

    def test_calculate_portfolio_value(self, backtester):
        """Test portfolio value calculation"""
        prices = {"VTI": 100.0, "VOO": 200.0, "BND": 50.0}
        holdings = {"VTI": 10, "VOO": 5, "BND": 20}
        
        value = backtester.calculate_portfolio_value(prices, holdings)
        
        assert value == 10 * 100.0 + 5 * 200.0 + 20 * 50.0
        assert value == 3000.0

    def test_calculate_portfolio_value_empty(self, backtester):
        """Test portfolio value with no holdings"""
        prices = {"VTI": 100.0, "VOO": 200.0}
        holdings = {}
        
        value = backtester.calculate_portfolio_value(prices, holdings)
        
        assert value == 0.0

    def test_calculate_portfolio_value_partial_holdings(self, backtester):
        """Test portfolio value when holding only some symbols"""
        prices = {"VTI": 100.0, "VOO": 200.0, "BND": 50.0}
        holdings = {"VTI": 10, "VOO": 5}  # No BND holdings
        
        value = backtester.calculate_portfolio_value(prices, holdings)
        
        assert value == 1500.0

    def test_rebalance_portfolio(self, backtester):
        """Test portfolio rebalancing calculation"""
        current_value = 10000.0
        current_prices = {"VTI": 100.0, "VOO": 200.0, "BND": 50.0}
        target_allocation = {"VTI": 0.5, "VOO": 0.3, "BND": 0.2}
        
        new_holdings = backtester.rebalance_portfolio(
            current_value,
            current_prices,
            target_allocation
        )
        
        # Check that holdings roughly match target allocation
        assert new_holdings["VTI"] == 50  # $5000 / $100 = 50 shares
        assert new_holdings["VOO"] == 15  # $3000 / $200 = 15 shares
        assert new_holdings["BND"] == 40  # $2000 / $50 = 40 shares

    def test_rebalance_portfolio_zero_price(self, backtester):
        """Test rebalancing when a symbol has zero price"""
        current_value = 10000.0
        current_prices = {"VTI": 100.0, "VOO": 0.0}
        target_allocation = {"VTI": 0.5, "VOO": 0.5}
        
        new_holdings = backtester.rebalance_portfolio(
            current_value,
            current_prices,
            target_allocation
        )
        
        assert new_holdings["VTI"] == 50
        assert new_holdings["VOO"] == 0  # Can't buy at zero price

    def test_rebalance_portfolio_fractional_shares(self, backtester):
        """Test that rebalancing uses integer shares"""
        current_value = 10000.0
        current_prices = {"VTI": 333.33}
        target_allocation = {"VTI": 1.0}
        
        new_holdings = backtester.rebalance_portfolio(
            current_value,
            current_prices,
            target_allocation
        )
        
        # Should round down to integer shares
        assert isinstance(new_holdings["VTI"], int)
        assert new_holdings["VTI"] == 30  # 10000 / 333.33 = 30.0

    def test_get_rebalance_dates_monthly(self, backtester):
        """Test monthly rebalance date generation"""
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 4, 1)
        
        dates = backtester._get_rebalance_dates(start_date, end_date, "monthly")
        
        assert len(dates) >= 3  # At least 3 months
        assert start_date in dates

    def test_get_rebalance_dates_quarterly(self, backtester):
        """Test quarterly rebalance date generation"""
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2024, 1, 1)
        
        dates = backtester._get_rebalance_dates(start_date, end_date, "quarterly")
        
        assert len(dates) >= 4  # At least 4 quarters
        assert start_date in dates

    def test_get_rebalance_dates_yearly(self, backtester):
        """Test yearly rebalance date generation"""
        start_date = datetime(2021, 1, 1)
        end_date = datetime(2024, 1, 1)
        
        dates = backtester._get_rebalance_dates(start_date, end_date, "yearly")
        
        assert len(dates) >= 3  # At least 3 years
        assert start_date in dates

    def test_get_rebalance_dates_invalid_frequency(self, backtester):
        """Test that invalid frequency raises error"""
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2024, 1, 1)
        
        with pytest.raises(ValueError, match="Invalid rebalance frequency"):
            backtester._get_rebalance_dates(start_date, end_date, "invalid")

    def test_calculate_metrics_basic(self, backtester):
        """Test basic metrics calculation"""
        portfolio_values = [
            {'date': datetime(2023, 1, 1), 'value': 10000, 'holdings': {}},
            {'date': datetime(2023, 6, 1), 'value': 11000, 'holdings': {}},
            {'date': datetime(2023, 12, 31), 'value': 12000, 'holdings': {}}
        ]
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 12, 31)
        
        metrics = backtester._calculate_metrics(
            portfolio_values,
            10000,
            start_date,
            end_date
        )
        
        assert 'total_return_pct' in metrics
        assert 'annualized_return_pct' in metrics
        assert 'sharpe_ratio' in metrics
        assert 'max_drawdown_pct' in metrics
        assert metrics['total_return_pct'] == 20.0  # (12000-10000)/10000 * 100

    def test_calculate_metrics_with_drawdown(self, backtester):
        """Test metrics calculation with drawdown"""
        portfolio_values = [
            {'date': datetime(2023, 1, 1), 'value': 10000, 'holdings': {}},
            {'date': datetime(2023, 4, 1), 'value': 12000, 'holdings': {}},
            {'date': datetime(2023, 7, 1), 'value': 9000, 'holdings': {}},  # Drawdown
            {'date': datetime(2023, 12, 31), 'value': 11000, 'holdings': {}}
        ]
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 12, 31)
        
        metrics = backtester._calculate_metrics(
            portfolio_values,
            10000,
            start_date,
            end_date
        )
        
        # Max drawdown should be from peak of 12000 to 9000
        assert metrics['max_drawdown_pct'] == 25.0  # (12000-9000)/12000 * 100

    def test_calculate_metrics_empty_portfolio(self, backtester):
        """Test metrics calculation with empty portfolio"""
        portfolio_values = []
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 12, 31)
        
        metrics = backtester._calculate_metrics(
            portfolio_values,
            10000,
            start_date,
            end_date
        )
        
        assert metrics == {}

    def test_calculate_metrics_no_volatility(self, backtester):
        """Test metrics when portfolio has no volatility"""
        portfolio_values = [
            {'date': datetime(2023, 1, 1), 'value': 10000, 'holdings': {}},
            {'date': datetime(2023, 12, 31), 'value': 10000, 'holdings': {}}
        ]
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 12, 31)
        
        metrics = backtester._calculate_metrics(
            portfolio_values,
            10000,
            start_date,
            end_date
        )
        
        assert metrics['total_return_pct'] == 0.0
        assert metrics['annualized_volatility_pct'] == 0.0


class TestBacktestStrategy:
    """Test suite for backtesting strategies"""

    @pytest.fixture
    def mock_backtester(self):
        """Create a backtester with fully mocked data client"""
        with patch('backtest.backtest.StockHistoricalDataClient') as mock_client:
            backtester = PortfolioBacktester("test_key", "test_secret")
            backtester.data_client = Mock()
            return backtester

    def create_mock_price_data(self, symbols, start_date, end_date):
        """Create mock price data for testing"""
        dates = pd.date_range(start_date, end_date, freq='D')
        data = []
        
        for symbol in symbols:
            for date in dates:
                # Create simple upward trending prices
                days_from_start = (date - start_date).days
                price = 100.0 + days_from_start * 0.1
                
                data.append({
                    'symbol': symbol,
                    'timestamp': date,
                    'close': price,
                    'open': price * 0.99,
                    'high': price * 1.01,
                    'low': price * 0.98,
                    'volume': 1000000
                })
        
        df = pd.DataFrame(data)
        df = df.set_index(['symbol', 'timestamp'])
        return df

    def test_backtest_strategy_basic(self, mock_backtester):
        """Test basic backtesting of a strategy"""
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 3, 31)
        
        # Create mock data
        symbols = list(RISK_PROFILES["moderate"].keys())
        mock_data = self.create_mock_price_data(symbols, start_date, end_date)
        mock_backtester.data_client.get_stock_bars = Mock(return_value=Mock(df=mock_data))
        
        result = mock_backtester.backtest_strategy(
            "moderate",
            start_date,
            end_date,
            initial_capital=10000.0,
            rebalance_frequency="monthly"
        )
        
        assert result['risk_profile'] == "moderate"
        assert result['initial_capital'] == 10000.0
        assert 'final_value' in result
        assert 'metrics' in result
        assert len(result['portfolio_values']) > 0

    def test_backtest_invalid_profile(self, mock_backtester):
        """Test backtesting with invalid risk profile"""
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 3, 31)
        
        with pytest.raises(ValueError, match="Invalid risk profile"):
            mock_backtester.backtest_strategy(
                "invalid_profile",
                start_date,
                end_date
            )


class TestBacktestResults:
    """Test suite for backtest results handling"""

    @pytest.fixture
    def backtester_with_results(self):
        """Create backtester with mock results"""
        with patch('backtest.backtest.StockHistoricalDataClient'):
            backtester = PortfolioBacktester("test_key", "test_secret")
            
            # Add mock results
            backtester.results = {
                'moderate': {
                    'risk_profile': 'moderate',
                    'start_date': datetime(2023, 1, 1),
                    'end_date': datetime(2023, 12, 31),
                    'initial_capital': 10000.0,
                    'final_value': 12000.0,
                    'metrics': {
                        'total_return_pct': 20.0,
                        'annualized_return_pct': 20.0,
                        'annualized_volatility_pct': 15.0,
                        'sharpe_ratio': 1.33,
                        'max_drawdown_pct': 10.0,
                        'best_day_pct': 5.0,
                        'worst_day_pct': -3.0,
                        'total_days': 252
                    },
                    'rebalance_dates': [datetime(2023, 1, 1), datetime(2023, 4, 1)]
                }
            }
            
            return backtester

    def test_save_results(self, backtester_with_results, tmp_path):
        """Test saving results to JSON"""
        output_file = tmp_path / "test_results.json"
        
        backtester_with_results.save_results(str(output_file))
        
        assert output_file.exists()
        
        # Verify contents
        import json
        with open(output_file) as f:
            data = json.load(f)
        
        assert 'moderate' in data
        assert data['moderate']['final_value'] == 12000.0

    def test_generate_markdown_report(self, backtester_with_results, tmp_path):
        """Test generating markdown report"""
        output_file = tmp_path / "test_report.md"
        
        backtester_with_results.generate_markdown_report(str(output_file))
        
        assert output_file.exists()
        
        # Verify contents
        with open(output_file) as f:
            content = f.read()
        
        assert "# Backtest Results" in content
        assert "moderate" in content
        assert "20.0%" in content  # Total return

    def test_generate_markdown_report_with_error(self, tmp_path):
        """Test markdown report generation with error results"""
        with patch('backtest.backtest.StockHistoricalDataClient'):
            backtester = PortfolioBacktester("test_key", "test_secret")
            backtester.results = {
                'moderate': {'error': 'API Error'}
            }
            
            output_file = tmp_path / "test_report.md"
            backtester.generate_markdown_report(str(output_file))
            
            assert output_file.exists()
            
            with open(output_file) as f:
                content = f.read()
            
            assert "ERROR" in content


class TestIntegrationScenarios:
    """Integration tests for realistic backtesting scenarios"""

    @pytest.fixture
    def full_backtester(self):
        """Create a fully configured backtester"""
        with patch('backtest.backtest.StockHistoricalDataClient') as mock_client:
            backtester = PortfolioBacktester("test_key", "test_secret")
            backtester.data_client = Mock()
            return backtester

    def test_bull_market_scenario(self, full_backtester):
        """Test backtesting during bull market (all prices rising)"""
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 6, 30)
        symbols = list(RISK_PROFILES["aggressive_growth"].keys())
        
        # Create bull market data (prices increase 20%)
        dates = pd.date_range(start_date, end_date, freq='D')
        data = []
        for symbol in symbols:
            base_price = 100.0
            for i, date in enumerate(dates):
                price = base_price * (1 + 0.20 * i / len(dates))
                data.append({
                    'symbol': symbol,
                    'timestamp': date,
                    'close': price,
                    'open': price,
                    'high': price,
                    'low': price,
                    'volume': 1000000
                })
        
        df = pd.DataFrame(data).set_index(['symbol', 'timestamp'])
        full_backtester.data_client.get_stock_bars = Mock(return_value=Mock(df=df))
        
        result = full_backtester.backtest_strategy(
            "aggressive_growth",
            start_date,
            end_date,
            initial_capital=10000.0
        )
        
        # In bull market, final value should be higher
        assert result['final_value'] > result['initial_capital']

    def test_bear_market_scenario(self, full_backtester):
        """Test backtesting during bear market (prices falling)"""
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 6, 30)
        symbols = list(RISK_PROFILES["very_conservative"].keys())
        
        # Create bear market data (prices decrease 15%)
        dates = pd.date_range(start_date, end_date, freq='D')
        data = []
        for symbol in symbols:
            base_price = 100.0
            for i, date in enumerate(dates):
                # Stock ETFs fall more, bonds fall less
                decline_rate = 0.15 if symbol != "BND" else 0.05
                price = base_price * (1 - decline_rate * i / len(dates))
                data.append({
                    'symbol': symbol,
                    'timestamp': date,
                    'close': price,
                    'open': price,
                    'high': price,
                    'low': price,
                    'volume': 1000000
                })
        
        df = pd.DataFrame(data).set_index(['symbol', 'timestamp'])
        full_backtester.data_client.get_stock_bars = Mock(return_value=Mock(df=df))
        
        result = full_backtester.backtest_strategy(
            "very_conservative",
            start_date,
            end_date,
            initial_capital=10000.0
        )
        
        # Conservative portfolio should have lower drawdown
        assert result['metrics']['max_drawdown_pct'] < 20.0

    def test_volatile_market_scenario(self, full_backtester):
        """Test backtesting in volatile market"""
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 3, 31)
        symbols = list(RISK_PROFILES["moderate"].keys())
        
        # Create volatile market data (prices swing up and down)
        dates = pd.date_range(start_date, end_date, freq='D')
        data = []
        for symbol in symbols:
            base_price = 100.0
            for i, date in enumerate(dates):
                # Oscillating prices
                volatility = 10.0 * (1 if i % 10 < 5 else -1)
                price = base_price + volatility * (i % 10) / 10
                data.append({
                    'symbol': symbol,
                    'timestamp': date,
                    'close': price,
                    'open': price,
                    'high': price * 1.02,
                    'low': price * 0.98,
                    'volume': 1000000
                })
        
        df = pd.DataFrame(data).set_index(['symbol', 'timestamp'])
        full_backtester.data_client.get_stock_bars = Mock(return_value=Mock(df=df))
        
        result = full_backtester.backtest_strategy(
            "moderate",
            start_date,
            end_date,
            initial_capital=10000.0
        )
        
        # Volatile market should show higher volatility metric
        assert result['metrics']['annualized_volatility_pct'] > 0


class TestRunBacktest:
    """Test the convenience run_backtest function"""

    @patch('backtest.backtest.PortfolioBacktester')
    @patch.dict('os.environ', {
        'ALPACA_API_KEY_ID': 'test_key',
        'ALPACA_API_SECRET_KEY': 'test_secret'
    })
    def test_run_backtest_basic(self, mock_backtester_class):
        """Test run_backtest function"""
        from backtest.backtest import run_backtest
        
        mock_instance = Mock()
        mock_instance.backtest_all_profiles.return_value = {'moderate': {}}
        mock_backtester_class.return_value = mock_instance
        
        result = run_backtest(years_back=1, initial_capital=5000.0)
        
        assert mock_instance.backtest_all_profiles.called
        assert mock_instance.save_results.called
        assert mock_instance.generate_markdown_report.called

    @patch.dict('os.environ', {}, clear=True)
    def test_run_backtest_missing_credentials(self):
        """Test run_backtest without API credentials"""
        from backtest.backtest import run_backtest
        
        with pytest.raises(ValueError, match="ALPACA_API_KEY_ID"):
            run_backtest(years_back=1)
