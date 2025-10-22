"""
Trading Bot Main Entry Point

Rebalances portfolio based on risk profile or target date fund strategy.
"""

import os
import sys
import logging
from datetime import datetime
from core.trader import AlpacaTrader
from core.profiles import RISK_PROFILES

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/trading_bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def validate_environment():
    """
    Validate that required environment variables are set
    
    Raises:
        ValueError: If required environment variables are missing
    """
    required_vars = ['ALPACA_API_KEY_ID', 'ALPACA_API_SECRET_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing_vars)}\n"
            f"Please set them in your environment or .env file"
        )
    
    # Check that at least one strategy is configured
    if not os.getenv('RISK_LEVEL') and not os.getenv('TARGET_YEAR'):
        raise ValueError(
            "Must set either RISK_LEVEL or TARGET_YEAR environment variable"
        )


def get_target_allocation():
    """
    Determine target allocation based on environment configuration
    
    Returns:
        tuple: (allocation_dict, strategy_description)
    
    Raises:
        ValueError: If invalid configuration
    """
    risk_level = os.getenv('RISK_LEVEL')
    target_year = os.getenv('TARGET_YEAR')
    
    if target_year:
        # Target date fund (if implemented)
        logger.info(f"Using target date fund strategy for year {target_year}")
        # TODO: Implement target date fund logic
        # For now, fall back to risk level
        logger.warning("Target date fund not yet implemented, falling back to risk level")
        risk_level = os.getenv('RISK_LEVEL', 'moderate')
    
    if risk_level:
        if risk_level not in RISK_PROFILES:
            raise ValueError(
                f"Invalid RISK_LEVEL: {risk_level}. "
                f"Valid options: {', '.join(RISK_PROFILES.keys())}"
            )
        
        allocation = RISK_PROFILES[risk_level]
        description = f"{risk_level} risk profile"
        
        logger.info(f"Using {description}")
        logger.info(f"Target allocation: {allocation}")
        
        return allocation, description
    
    raise ValueError("No valid strategy configuration found")


def main():
    """
    Main execution function
    
    Validates environment, determines strategy, and executes rebalancing
    """
    try:
        logger.info("="*60)
        logger.info("Starting Trading Bot")
        logger.info(f"Timestamp: {datetime.now().isoformat()}")
        logger.info("="*60)
        
        # Validate environment
        logger.info("Validating environment configuration...")
        validate_environment()
        logger.info("✅ Environment validation passed")
        
        # Get target allocation
        target_alloc, strategy_name = get_target_allocation()
        
        # Initialize trader
        logger.info("Initializing Alpaca trader client...")
        api_key = os.getenv('ALPACA_API_KEY_ID')
        secret_key = os.getenv('ALPACA_API_SECRET_KEY')
        paper_mode = os.getenv('PAPER_TRADING', 'true').lower() == 'true'
        
        trader = AlpacaTrader(api_key, secret_key, paper=paper_mode)
        logger.info(f"✅ Connected to Alpaca (paper_mode={paper_mode})")
        
        # Get current account status
        try:
            account_value = trader.get_account_value()
            logger.info(f"Current account value: ${account_value:,.2f}")
        except Exception as e:
            logger.error(f"Failed to retrieve account value: {e}")
            raise
        
        # Execute rebalancing
        logger.info("Starting portfolio rebalancing...")
        trader.rebalance(target_alloc)
        
        logger.info("="*60)
        logger.info(f"✅ Successfully rebalanced portfolio to {strategy_name}")
        logger.info("="*60)
        
        return 0
        
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    exit_code = main()
    sys.exit(exit_code)