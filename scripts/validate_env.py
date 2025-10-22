#!/usr/bin/env python3
"""
Configuration Validation Script

Checks that the trading bot is properly configured before running.
"""

import os
import sys
from pathlib import Path


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(text):
    """Print a formatted header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")


def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")


def print_warning(text):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")


def print_error(text):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.END}")


def check_python_version():
    """Check Python version is 3.9+"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print_error(f"Python 3.9+ required, found {version.major}.{version.minor}")
        return False
    print_success(f"Python version: {version.major}.{version.minor}.{version.micro}")
    return True


def check_project_structure():
    """Check that required files and directories exist"""
    print("\nChecking project structure...")
    
    required_files = [
        'main.py',
        'backtest.py',
        'requirements.txt',
        '.env',
        '.gitignore',
        'core/profiles.py',
        'core/trader.py',
        'core/utils.py',
    ]
    
    missing_files = []
    for file_path in required_files:
        if Path(file_path).exists():
            print_success(f"Found: {file_path}")
        else:
            print_error(f"Missing: {file_path}")
            missing_files.append(file_path)
    
    return len(missing_files) == 0


def check_environment_variables():
    """Check that required environment variables are set"""
    print("\nChecking environment variables...")
    
    required_vars = {
        'ALPACA_API_KEY_ID': 'Alpaca API Key',
        'ALPACA_API_SECRET_KEY': 'Alpaca Secret Key',
    }
    
    optional_vars = {
        'RISK_LEVEL': 'Risk profile selection',
        'TARGET_YEAR': 'Target date fund year',
        'PAPER_TRADING': 'Paper trading mode',
    }
    
    issues = []
    
    # Check required variables
    for var, description in required_vars.items():
        value = os.getenv(var)
        if not value:
            print_error(f"Missing: {var} ({description})")
            issues.append(var)
        elif value == 'your_api_key_here' or value == 'your_secret_key_here':
            print_error(f"Not configured: {var} (still has placeholder value)")
            issues.append(var)
        elif 'PK09GIKYQ8U8O53E8WPL' in value or 'acmXhvU0jUxebAlgYPM0O9XgTJ3a8cBrRTXLG4fP' in value:
            print_error(f"SECURITY RISK: {var} contains hardcoded example key!")
            issues.append(var)
        else:
            print_success(f"Set: {var}")
    
    # Check that at least one strategy is configured
    risk_level = os.getenv('RISK_LEVEL')
    target_year = os.getenv('TARGET_YEAR')
    
    if not risk_level and not target_year:
        print_error("Neither RISK_LEVEL nor TARGET_YEAR is set")
        issues.append('STRATEGY')
    elif risk_level:
        valid_levels = ['very_conservative', 'conservative', 'moderate', 'aggressive', 'aggressive_growth']
        if risk_level not in valid_levels:
            print_error(f"Invalid RISK_LEVEL: {risk_level}")
            print_error(f"Valid options: {', '.join(valid_levels)}")
            issues.append('RISK_LEVEL')
        else:
            print_success(f"Risk level: {risk_level}")
    elif target_year:
        try:
            year = int(target_year)
            if year < 2025 or year > 2100:
                print_warning(f"Unusual target year: {year}")
            else:
                print_success(f"Target year: {year}")
        except ValueError:
            print_error(f"Invalid TARGET_YEAR: {target_year} (must be a number)")
            issues.append('TARGET_YEAR')
    
    # Check optional variables
    paper_trading = os.getenv('PAPER_TRADING', 'true').lower()
    if paper_trading != 'true':
        print_warning(f"PAPER_TRADING={paper_trading} (not using paper trading!)")
    else:
        print_success("Paper trading mode enabled")
    
    return len(issues) == 0


def check_dependencies():
    """Check that required Python packages are installed"""
    print("\nChecking dependencies...")
    
    required_packages = [
        'alpaca',
        'pytest',
        'coverage',
        'pandas',
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
            print_success(f"Installed: {package}")
        except ImportError:
            print_error(f"Missing: {package}")
            missing.append(package)
    
    if missing:
        print_error("\nInstall missing packages with:")
        print(f"  pip install -r requirements.txt")
    
    return len(missing) == 0


def check_api_connection():
    """Test connection to Alpaca API"""
    print("\nTesting Alpaca API connection...")
    
    try:
        from alpaca.trading.client import TradingClient
        
        api_key = os.getenv('ALPACA_API_KEY_ID')
        secret_key = os.getenv('ALPACA_API_SECRET_KEY')
        
        if not api_key or not secret_key:
            print_warning("Skipping API test (credentials not set)")
            return True  # Don't fail validation, just skip
        
        client = TradingClient(api_key, secret_key, paper=True)
        account = client.get_account()
        
        print_success("Successfully connected to Alpaca")
        print_success(f"Account status: {account.status}")
        print_success(f"Account equity: ${float(account.equity):,.2f}")
        
        return True
    except ImportError:
        print_error("Cannot test API (alpaca-py not installed)")
        return False
    except Exception as e:
        print_error(f"API connection failed: {e}")
        print_warning("Check your API credentials and internet connection")
        return False


def check_logs_directory():
    """Check that logs directory exists"""
    print("\nChecking logs directory...")
    
    logs_dir = Path('logs')
    if logs_dir.exists():
        print_success("Logs directory exists")
        
        # Check for any existing logs
        log_files = list(logs_dir.glob('*.log'))
        if log_files:
            print_success(f"Found {len(log_files)} existing log file(s)")
        
        return True
    else:
        print_warning("Logs directory doesn't exist (will be created automatically)")
        logs_dir.mkdir(exist_ok=True)
        print_success("Created logs directory")
        return True


def check_gitignore():
    """Check that sensitive files are in .gitignore"""
    print("\nChecking .gitignore...")
    
    gitignore_path = Path('.gitignore')
    if not gitignore_path.exists():
        print_error(".gitignore file not found")
        return False
    
    with open(gitignore_path) as f:
        content = f.read()
    
    required_entries = ['.env', 'logs/', '__pycache__/']
    missing_entries = []
    
    for entry in required_entries:
        if entry in content:
            print_success(f"Ignoring: {entry}")
        else:
            print_warning(f"Not in .gitignore: {entry}")
            missing_entries.append(entry)
    
    return len(missing_entries) == 0


def main():
    """Run all validation checks"""
    print_header("Trading Bot Configuration Validator")
    
    checks = [
        ("Python Version", check_python_version),
        ("Project Structure", check_project_structure),
        ("Dependencies", check_dependencies),
        ("Environment Variables", check_environment_variables),
        ("Logs Directory", check_logs_directory),
        (".gitignore", check_gitignore),
        ("API Connection", check_api_connection),
    ]
    
    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print_error(f"Check failed with error: {e}")
            results[name] = False
    
    # Print summary
    print_header("Validation Summary")
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    for name, result in results.items():
        if result:
            print_success(f"{name}: PASSED")
        else:
            print_error(f"{name}: FAILED")
    
    print(f"\n{Colors.BOLD}Results: {passed}/{total} checks passed{Colors.END}\n")
    
    if passed == total:
        print_success("All checks passed! You're ready to run the trading bot.")
        print("\nNext steps:")
        print("  1. Run tests: pytest -v")
        print("  2. Run bot: python main.py")
        print("  3. Run backtest: python backtest.py")
        return 0
    else:
        print_error("Some checks failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("  1. Set environment variables: edit .env file")
        print("  2. Install dependencies: pip install -r requirements.txt")
        print("  3. Check API credentials at https://alpaca.markets")
        return 1


if __name__ == '__main__':
    sys.exit(main())
