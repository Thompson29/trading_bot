"""
Backtesting framework for risk profile strategies using Alpaca historical data.

This module allows backtesting of different risk profiles to evaluate their
historical performance across various market conditions.
"""

import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import json
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from core.profiles import RISK_PROFILES


class PortfolioBacktester:
    """Backtest portfolio strategies using historical data"""
    
    def __init__(self, api_key: str, secret_key: str):
        self.data_client = StockHistoricalDataClient(api_key, secret_key)
        self.results = {}
    
    def get_historical_prices(
        self, 
        symbols: List[str], 
        start_date: datetime, 
        end_date: datetime,
        timeframe: TimeFrame = TimeFrame.Day
    ) -> Dict:
        """
        Fetch historical price data for given symbols
        
        Args:
            symbols: List of ETF ticker symbols
            start_date: Start date for historical data
            end_date: End date for historical data
            timeframe: Data granularity (Day, Hour, etc.)
            
        Returns:
            Dictionary mapping symbols to their historical bar data
        """
        request = StockBarsRequest(
            symbol_or_symbols=symbols,
            timeframe=timeframe,
            start=start_date,
            end=end_date
        )
        
        bars = self.data_client.get_stock_bars(request)
        return bars.df
    
    def calculate_portfolio_value(
        self,
        prices: Dict[str, float],
        holdings: Dict[str, float]
    ) -> float:
        """
        Calculate total portfolio value given current prices and holdings
        
        Args:
            prices: Current price for each symbol
            holdings: Number of shares held for each symbol
            
        Returns:
            Total portfolio value
        """
        return sum(holdings.get(symbol, 0) * price 
                   for symbol, price in prices.items())
    
    def rebalance_portfolio(
        self,
        current_value: float,
        current_prices: Dict[str, float],
        target_allocation: Dict[str, float],
        transaction_cost: float = 0.0
    ) -> Dict[str, float]:
        """
        Calculate new holdings after rebalancing
        
        Args:
            current_value: Current total portfolio value
            current_prices: Current price for each symbol
            target_allocation: Target percentage allocation for each symbol
            transaction_cost: Cost per transaction (default 0 for Alpaca)
            
        Returns:
            Dictionary of new share holdings for each symbol
        """
        new_holdings = {}
        
        for symbol, target_pct in target_allocation.items():
            target_value = current_value * target_pct
            price = current_prices.get(symbol, 0)
            
            if price > 0:
                shares = int(target_value / price)
                new_holdings[symbol] = shares
            else:
                new_holdings[symbol] = 0
        
        return new_holdings
    
    def backtest_strategy(
        self,
        risk_profile: str,
        start_date: datetime,
        end_date: datetime,
        initial_capital: float = 10000.0,
        rebalance_frequency: str = "quarterly"
    ) -> Dict:
        """
        Backtest a specific risk profile strategy
        
        Args:
            risk_profile: Name of risk profile to test
            start_date: Start date for backtest
            end_date: End date for backtest
            initial_capital: Starting portfolio value
            rebalance_frequency: How often to rebalance (monthly, quarterly, yearly)
            
        Returns:
            Dictionary containing backtest results and metrics
        """
        if risk_profile not in RISK_PROFILES:
            raise ValueError(f"Invalid risk profile: {risk_profile}")
        
        allocation = RISK_PROFILES[risk_profile]
        symbols = list(allocation.keys())
        
        # Fetch historical data
        print(f"Fetching historical data for {symbols}...")
        price_data = self.get_historical_prices(symbols, start_date, end_date)
        
        # Initialize portfolio
        holdings = {}
        portfolio_values = []
        rebalance_dates = []
        
        # Get rebalancing schedule
        rebalance_periods = self._get_rebalance_dates(
            start_date, end_date, rebalance_frequency
        )
        
        current_value = initial_capital
        
        # Iterate through each trading day
        grouped = price_data.groupby(level='symbol')
        dates = price_data.index.get_level_values('timestamp').unique().sort_values()
        
        for date in dates:
            # Get prices for this date
            current_prices = {}
            for symbol in symbols:
                try:
                    symbol_data = grouped.get_group(symbol)
                    date_data = symbol_data[symbol_data.index.get_level_values('timestamp') == date]
                    if not date_data.empty:
                        current_prices[symbol] = float(date_data['close'].iloc[0])
                except (KeyError, IndexError):
                    # If no data for this symbol on this date, use last known price
                    if symbol in current_prices:
                        pass  # Keep last price
                    else:
                        current_prices[symbol] = 100.0  # Default fallback
            
            # Check if we need to rebalance
            if date in rebalance_periods or not holdings:
                holdings = self.rebalance_portfolio(
                    current_value,
                    current_prices,
                    allocation
                )
                rebalance_dates.append(date)
            
            # Calculate current portfolio value
            current_value = self.calculate_portfolio_value(current_prices, holdings)
            portfolio_values.append({
                'date': date,
                'value': current_value,
                'holdings': holdings.copy()
            })
        
        # Calculate performance metrics
        metrics = self._calculate_metrics(
            portfolio_values,
            initial_capital,
            start_date,
            end_date
        )
        
        return {
            'risk_profile': risk_profile,
            'start_date': start_date,
            'end_date': end_date,
            'initial_capital': initial_capital,
            'final_value': current_value,
            'portfolio_values': portfolio_values,
            'rebalance_dates': rebalance_dates,
            'metrics': metrics
        }
    
    def _get_rebalance_dates(
        self,
        start_date: datetime,
        end_date: datetime,
        frequency: str
    ) -> List[datetime]:
        """Generate list of rebalancing dates"""
        dates = []
        current = start_date
        
        if frequency == "monthly":
            delta = timedelta(days=30)
        elif frequency == "quarterly":
            delta = timedelta(days=91)
        elif frequency == "yearly":
            delta = timedelta(days=365)
        else:
            raise ValueError(f"Invalid rebalance frequency: {frequency}")
        
        while current <= end_date:
            dates.append(current)
            current += delta
        
        return dates
    
    def _calculate_metrics(
        self,
        portfolio_values: List[Dict],
        initial_capital: float,
        start_date: datetime,
        end_date: datetime
    ) -> Dict:
        """Calculate performance metrics for backtest"""
        if not portfolio_values:
            return {}
        
        values = [pv['value'] for pv in portfolio_values]
        final_value = values[-1]
        
        # Total return
        total_return = ((final_value - initial_capital) / initial_capital) * 100
        
        # Annualized return
        days = (end_date - start_date).days
        years = days / 365.25
        annualized_return = (((final_value / initial_capital) ** (1 / years)) - 1) * 100 if years > 0 else 0
        
        # Calculate daily returns for volatility and Sharpe
        daily_returns = []
        for i in range(1, len(values)):
            daily_return = (values[i] - values[i-1]) / values[i-1]
            daily_returns.append(daily_return)
        
        # Volatility (annualized standard deviation)
        if daily_returns:
            import statistics
            daily_volatility = statistics.stdev(daily_returns) if len(daily_returns) > 1 else 0
            annualized_volatility = daily_volatility * (252 ** 0.5) * 100  # 252 trading days
        else:
            annualized_volatility = 0
        
        # Sharpe Ratio (assuming 0% risk-free rate for simplicity)
        sharpe_ratio = (annualized_return / annualized_volatility) if annualized_volatility > 0 else 0
        
        # Maximum Drawdown
        peak = values[0]
        max_drawdown = 0
        for value in values:
            if value > peak:
                peak = value
            drawdown = ((peak - value) / peak) * 100
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        # Best and worst day
        best_day = max(daily_returns) * 100 if daily_returns else 0
        worst_day = min(daily_returns) * 100 if daily_returns else 0
        
        return {
            'total_return_pct': round(total_return, 2),
            'annualized_return_pct': round(annualized_return, 2),
            'annualized_volatility_pct': round(annualized_volatility, 2),
            'sharpe_ratio': round(sharpe_ratio, 2),
            'max_drawdown_pct': round(max_drawdown, 2),
            'best_day_pct': round(best_day, 2),
            'worst_day_pct': round(worst_day, 2),
            'total_days': len(values)
        }
    
    def backtest_all_profiles(
        self,
        start_date: datetime,
        end_date: datetime,
        initial_capital: float = 10000.0,
        rebalance_frequency: str = "quarterly"
    ) -> Dict[str, Dict]:
        """
        Backtest all risk profiles
        
        Args:
            start_date: Start date for backtest
            end_date: End date for backtest
            initial_capital: Starting portfolio value
            rebalance_frequency: How often to rebalance
            
        Returns:
            Dictionary mapping risk profiles to their backtest results
        """
        results = {}
        
        for profile_name in RISK_PROFILES.keys():
            print(f"\n{'='*60}")
            print(f"Backtesting {profile_name} profile...")
            print(f"{'='*60}")
            
            try:
                result = self.backtest_strategy(
                    profile_name,
                    start_date,
                    end_date,
                    initial_capital,
                    rebalance_frequency
                )
                results[profile_name] = result
                
                # Print summary
                metrics = result['metrics']
                print(f"\nResults for {profile_name}:")
                print(f"  Total Return: {metrics['total_return_pct']}%")
                print(f"  Annualized Return: {metrics['annualized_return_pct']}%")
                print(f"  Volatility: {metrics['annualized_volatility_pct']}%")
                print(f"  Sharpe Ratio: {metrics['sharpe_ratio']}")
                print(f"  Max Drawdown: {metrics['max_drawdown_pct']}%")
                
            except Exception as e:
                print(f"Error backtesting {profile_name}: {e}")
                results[profile_name] = {'error': str(e)}
        
        self.results = results
        return results
    
    def save_results(self, filename: str = "backtest_results.json"):
        """Save backtest results to JSON file"""
        # Convert datetime objects to strings for JSON serialization
        serializable_results = {}
        
        for profile, data in self.results.items():
            if 'error' in data:
                serializable_results[profile] = data
                continue
                
            serializable_data = {
                'risk_profile': data['risk_profile'],
                'start_date': data['start_date'].isoformat(),
                'end_date': data['end_date'].isoformat(),
                'initial_capital': data['initial_capital'],
                'final_value': data['final_value'],
                'metrics': data['metrics'],
                'rebalance_count': len(data['rebalance_dates'])
            }
            serializable_results[profile] = serializable_data
        
        with open(filename, 'w') as f:
            json.dump(serializable_results, f, indent=2)
        
        print(f"\n✅ Results saved to {filename}")
    
    def generate_markdown_report(self, filename: str = "BACKTEST_RESULTS.md"):
        """Generate a markdown report of backtest results"""
        with open(filename, 'w') as f:
            f.write("# Backtest Results\n\n")
            f.write("Performance analysis of different risk profiles using historical data.\n\n")
            
            if not self.results:
                f.write("No results available. Run backtest first.\n")
                return
            
            # Get date range from first result
            first_result = next(iter(self.results.values()))
            if 'start_date' in first_result:
                f.write(f"**Backtest Period:** {first_result['start_date'].strftime('%Y-%m-%d')} ")
                f.write(f"to {first_result['end_date'].strftime('%Y-%m-%d')}\n\n")
                f.write(f"**Initial Capital:** ${first_result['initial_capital']:,.2f}\n\n")
            
            # Summary table
            f.write("## Summary Table\n\n")
            f.write("| Risk Profile | Total Return | Annualized Return | Volatility | Sharpe Ratio | Max Drawdown |\n")
            f.write("|-------------|--------------|-------------------|------------|--------------|-------------|\n")
            
            for profile, data in self.results.items():
                if 'error' in data:
                    f.write(f"| {profile} | ERROR | - | - | - | - |\n")
                    continue
                
                metrics = data['metrics']
                f.write(f"| {profile} | ")
                f.write(f"{metrics['total_return_pct']}% | ")
                f.write(f"{metrics['annualized_return_pct']}% | ")
                f.write(f"{metrics['annualized_volatility_pct']}% | ")
                f.write(f"{metrics['sharpe_ratio']} | ")
                f.write(f"{metrics['max_drawdown_pct']}% |\n")
            
            # Detailed results for each profile
            f.write("\n## Detailed Results\n\n")
            
            for profile, data in self.results.items():
                if 'error' in data:
                    f.write(f"### {profile}\n\n")
                    f.write(f"**Error:** {data['error']}\n\n")
                    continue
                
                f.write(f"### {profile}\n\n")
                f.write(f"**Final Portfolio Value:** ${data['final_value']:,.2f}\n\n")
                
                metrics = data['metrics']
                f.write("**Performance Metrics:**\n")
                f.write(f"- Total Return: {metrics['total_return_pct']}%\n")
                f.write(f"- Annualized Return: {metrics['annualized_return_pct']}%\n")
                f.write(f"- Annualized Volatility: {metrics['annualized_volatility_pct']}%\n")
                f.write(f"- Sharpe Ratio: {metrics['sharpe_ratio']}\n")
                f.write(f"- Maximum Drawdown: {metrics['max_drawdown_pct']}%\n")
                f.write(f"- Best Day: {metrics['best_day_pct']}%\n")
                f.write(f"- Worst Day: {metrics['worst_day_pct']}%\n")
                f.write(f"- Total Trading Days: {metrics['total_days']}\n\n")
                
                # Allocation
                allocation = RISK_PROFILES[profile]
                f.write("**Target Allocation:**\n")
                for symbol, pct in allocation.items():
                    f.write(f"- {symbol}: {pct*100}%\n")
                f.write("\n")
        
        print(f"✅ Markdown report saved to {filename}")


def run_backtest(
    years_back: int = 3,
    initial_capital: float = 10000.0,
    rebalance_frequency: str = "quarterly"
):
    """
    Convenience function to run backtest with default parameters
    
    Args:
        years_back: Number of years of historical data to test
        initial_capital: Starting portfolio value
        rebalance_frequency: How often to rebalance (monthly, quarterly, yearly)
    """
    API_KEY = os.getenv("ALPACA_API_KEY_ID")
    SECRET_KEY = os.getenv("ALPACA_API_SECRET_KEY")
    
    if not API_KEY or not SECRET_KEY:
        raise ValueError("ALPACA_API_KEY_ID and ALPACA_API_SECRET_KEY must be set")
    
    # Set date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=years_back * 365)
    
    print(f"Starting backtest from {start_date.date()} to {end_date.date()}")
    print(f"Initial capital: ${initial_capital:,.2f}")
    print(f"Rebalance frequency: {rebalance_frequency}")
    
    # Run backtest
    backtester = PortfolioBacktester(API_KEY, SECRET_KEY)
    results = backtester.backtest_all_profiles(
        start_date,
        end_date,
        initial_capital,
        rebalance_frequency
    )
    
    # Save results
    backtester.save_results("backtest_results.json")
    backtester.generate_markdown_report("BACKTEST_RESULTS.md")
    
    return results


if __name__ == "__main__":
    # Run 3-year backtest with quarterly rebalancing
    results = run_backtest(years_back=3, initial_capital=10000.0, rebalance_frequency="quarterly")
