"""
Utility functions for portfolio allocation and rebalancing
"""

import logging
from typing import Dict

logger = logging.getLogger(__name__)


def summarize_allocation(allocation: Dict[str, float]) -> None:
    """
    Print a summary of portfolio allocation
    
    Args:
        allocation: Dictionary mapping symbols to dollar amounts
    """
    total = sum(allocation.values())
    
    logger.info("Portfolio Allocation:")
    for etf, amount in sorted(allocation.items(), key=lambda x: x[1], reverse=True):
        percentage = (amount / total * 100) if total > 0 else 0
        logger.info(f"  {etf}: ${amount:,.2f} ({percentage:.1f}%)")
    logger.info(f"  TOTAL: ${total:,.2f}")


def calculate_diffs(
    current_alloc: Dict[str, float],
    target_alloc: Dict[str, float],
    total_value: float
) -> Dict[str, float]:
    """
    Calculate the dollar difference between current and target allocations
    
    Args:
        current_alloc: Current position values by symbol
        target_alloc: Target allocation percentages by symbol (0-1)
        total_value: Total portfolio value
    
    Returns:
        Dictionary mapping symbols to dollar amounts to buy (+) or sell (-)
    
    Examples:
        >>> current = {"VTI": 3000, "BND": 7000}
        >>> target = {"VTI": 0.5, "BND": 0.5}
        >>> calculate_diffs(current, target, 10000)
        {'VTI': 2000.0, 'BND': -2000.0}
    """
    diffs = {}
    
    for symbol, target_pct in target_alloc.items():
        current_value = current_alloc.get(symbol, 0)
        target_value = total_value * target_pct
        diff = target_value - current_value
        diffs[symbol] = round(diff, 2)
    
    return diffs


def validate_allocation(allocation: Dict[str, float]) -> tuple[bool, str]:
    """
    Validate that an allocation is properly configured
    
    Args:
        allocation: Dictionary mapping symbols to percentages (0-1)
    
    Returns:
        Tuple of (is_valid, error_message)
    
    Examples:
        >>> validate_allocation({"VTI": 0.5, "BND": 0.5})
        (True, '')
        >>> validate_allocation({"VTI": 0.6, "BND": 0.5})
        (False, 'Allocation sums to 110.0%, expected 100%')
    """
    # Check for empty allocation
    if not allocation:
        return False, "Allocation is empty"
    
    # Check for negative values
    for symbol, pct in allocation.items():
        if pct < 0:
            return False, f"Negative allocation for {symbol}: {pct:.1%}"
    
    # Check sum
    total = sum(allocation.values())
    if not (0.99 <= total <= 1.01):
        return False, f"Allocation sums to {total:.1%}, expected 100%"
    
    return True, ""


def calculate_portfolio_metrics(
    positions: Dict[str, float],
    target_alloc: Dict[str, float]
) -> Dict[str, float]:
    """
    Calculate metrics about current portfolio vs target
    
    Args:
        positions: Current position values by symbol
        target_alloc: Target allocation percentages by symbol
    
    Returns:
        Dictionary with metrics:
        - total_value: Total portfolio value
        - drift: Total absolute percentage point drift from target
        - max_drift: Maximum drift for any single position
    """
    total_value = sum(positions.values())
    
    if total_value == 0:
        return {
            'total_value': 0,
            'drift': 0,
            'max_drift': 0
        }
    
    drifts = []
    for symbol, target_pct in target_alloc.items():
        current_value = positions.get(symbol, 0)
        current_pct = current_value / total_value
        drift = abs(current_pct - target_pct)
        drifts.append(drift)
    
    return {
        'total_value': total_value,
        'drift': sum(drifts),
        'max_drift': max(drifts) if drifts else 0
    }


def format_currency(amount: float) -> str:
    """
    Format a dollar amount for display
    
    Args:
        amount: Dollar amount
    
    Returns:
        Formatted string with dollar sign and commas
    
    Examples:
        >>> format_currency(1234.56)
        '$1,234.56'
        >>> format_currency(-1234.56)
        '-$1,234.56'
    """
    if amount < 0:
        return f"-${abs(amount):,.2f}"
    return f"${amount:,.2f}"


def format_percentage(value: float) -> str:
    """
    Format a decimal as a percentage
    
    Args:
        value: Decimal value (0-1)
    
    Returns:
        Formatted percentage string
    
    Examples:
        >>> format_percentage(0.5)
        '50.0%'
        >>> format_percentage(0.123)
        '12.3%'
    """
    return f"{value * 100:.1f}%"
