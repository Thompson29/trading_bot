"""
Unit tests for core/utils.py

Tests utility functions for portfolio calculations and formatting.
"""

import pytest
import logging
from core.utils import (
    calculate_diffs,
    summarize_allocation,
    validate_allocation,
    calculate_portfolio_metrics,
    format_currency,
    format_percentage
)


# ============================================================================
# CALCULATE DIFFS TESTS
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

        # 333.3 target - 333.33 current = -0.03 (rounded to 2 decimals)
        assert diffs["VTI"] == -0.03

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


# ============================================================================
# SUMMARIZE ALLOCATION TESTS
# ============================================================================

class TestSummarizeAllocation:
    """Test suite for summarize_allocation function"""

    def test_summarize_allocation(self, caplog):
        """Test allocation summary logging"""
        caplog.set_level(logging.INFO)
        
        allocation = {"VTI": 500, "VOO": 300, "BND": 200}
        
        summarize_allocation(allocation)
        
        # Check that log messages were created
        log_text = caplog.text
        assert "VTI" in log_text
        assert "VOO" in log_text
        assert "BND" in log_text

    def test_summarize_allocation_with_percentages(self, caplog):
        """Test that percentages are included in summary"""
        caplog.set_level(logging.INFO)
        
        allocation = {"VTI": 6000, "BND": 4000}
        
        summarize_allocation(allocation)
        
        log_text = caplog.text
        # Should include percentage info
        assert "60" in log_text or "40" in log_text
        assert "TOTAL" in log_text

    def test_summarize_allocation_empty(self, caplog):
        """Test summarizing empty allocation"""
        caplog.set_level(logging.INFO)
        
        allocation = {}
        
        summarize_allocation(allocation)
        
        log_text = caplog.text
        assert "TOTAL: $0.00" in log_text


# ============================================================================
# VALIDATE ALLOCATION TESTS
# ============================================================================

class TestValidateAllocation:
    """Test suite for validate_allocation function"""
    
    def test_validate_allocation_valid(self):
        """Test validation with valid allocation"""
        allocation = {"VTI": 0.6, "BND": 0.4}
        
        is_valid, error = validate_allocation(allocation)
        
        assert is_valid == True
        assert error == ""
    
    def test_validate_allocation_empty(self):
        """Test validation with empty allocation"""
        allocation = {}
        
        is_valid, error = validate_allocation(allocation)
        
        assert is_valid == False
        assert "empty" in error.lower()
    
    def test_validate_allocation_negative(self):
        """Test validation with negative value"""
        allocation = {"VTI": 0.7, "BND": -0.3}
        
        is_valid, error = validate_allocation(allocation)
        
        assert is_valid == False
        assert "Negative" in error
        assert "BND" in error
    
    def test_validate_allocation_sum_too_high(self):
        """Test validation when sum > 1.01"""
        allocation = {"VTI": 0.7, "BND": 0.5}
        
        is_valid, error = validate_allocation(allocation)
        
        assert is_valid == False
        assert "120" in error  # 120%
    
    def test_validate_allocation_sum_too_low(self):
        """Test validation when sum < 0.99"""
        allocation = {"VTI": 0.5, "BND": 0.3}
        
        is_valid, error = validate_allocation(allocation)
        
        assert is_valid == False
        assert "80" in error  # 80%

    def test_validate_allocation_exactly_one(self):
        """Test validation when sum is exactly 1.0"""
        allocation = {"VTI": 0.5, "BND": 0.5}
        
        is_valid, error = validate_allocation(allocation)
        
        assert is_valid == True
        assert error == ""

    def test_validate_allocation_within_tolerance(self):
        """Test validation within 0.99-1.01 range"""
        allocation = {"VTI": 0.50, "BND": 0.495}  # Sums to 0.995
        
        is_valid, error = validate_allocation(allocation)
        
        assert is_valid == True
        assert error == ""


# ============================================================================
# CALCULATE PORTFOLIO METRICS TESTS
# ============================================================================

class TestCalculatePortfolioMetrics:
    """Test suite for calculate_portfolio_metrics function"""
    
    def test_calculate_metrics_basic(self):
        """Test basic metrics calculation"""
        positions = {"VTI": 5000, "BND": 5000}
        target_alloc = {"VTI": 0.6, "BND": 0.4}
        
        metrics = calculate_portfolio_metrics(positions, target_alloc)
        
        assert metrics['total_value'] == 10000
        assert metrics['drift'] > 0  # Should have some drift
        assert metrics['max_drift'] > 0
    
    def test_calculate_metrics_zero_value(self):
        """Test metrics with zero portfolio value"""
        positions = {}
        target_alloc = {"VTI": 0.6, "BND": 0.4}
        
        metrics = calculate_portfolio_metrics(positions, target_alloc)
        
        assert metrics['total_value'] == 0
        assert metrics['drift'] == 0
        assert metrics['max_drift'] == 0
    
    def test_calculate_metrics_perfect_allocation(self):
        """Test metrics with perfect allocation"""
        positions = {"VTI": 6000, "BND": 4000}
        target_alloc = {"VTI": 0.6, "BND": 0.4}
        
        metrics = calculate_portfolio_metrics(positions, target_alloc)
        
        assert metrics['total_value'] == 10000
        # Drift should be near zero (perfect allocation)
        assert metrics['drift'] < 0.01
        assert metrics['max_drift'] < 0.01
    
    def test_calculate_metrics_large_drift(self):
        """Test metrics with large drift"""
        positions = {"VTI": 9000, "BND": 1000}
        target_alloc = {"VTI": 0.6, "BND": 0.4}
        
        metrics = calculate_portfolio_metrics(positions, target_alloc)
        
        assert metrics['total_value'] == 10000
        assert metrics['drift'] > 0.5  # Large drift
        assert metrics['max_drift'] > 0.2

    def test_calculate_metrics_missing_positions(self):
        """Test metrics when some target positions are missing"""
        positions = {"VTI": 10000}
        target_alloc = {"VTI": 0.6, "BND": 0.4}
        
        metrics = calculate_portfolio_metrics(positions, target_alloc)
        
        assert metrics['total_value'] == 10000
        # Should show drift because BND is missing
        assert metrics['drift'] > 0.3


# ============================================================================
# FORMAT HELPERS TESTS
# ============================================================================

class TestFormatCurrency:
    """Test suite for format_currency function"""
    
    def test_format_currency_positive(self):
        """Test formatting positive currency"""
        result = format_currency(1234.56)
        assert result == "$1,234.56"
    
    def test_format_currency_negative(self):
        """Test formatting negative currency"""
        result = format_currency(-1234.56)
        assert result == "-$1,234.56"
    
    def test_format_currency_zero(self):
        """Test formatting zero"""
        result = format_currency(0)
        assert result == "$0.00"
    
    def test_format_currency_large(self):
        """Test formatting large amount"""
        result = format_currency(1234567.89)
        assert result == "$1,234,567.89"

    def test_format_currency_small(self):
        """Test formatting small amount"""
        result = format_currency(0.99)
        assert result == "$0.99"

    def test_format_currency_no_cents(self):
        """Test formatting whole dollar amount"""
        result = format_currency(1000.00)
        assert result == "$1,000.00"


class TestFormatPercentage:
    """Test suite for format_percentage function"""
    
    def test_format_percentage_basic(self):
        """Test formatting percentage"""
        result = format_percentage(0.5)
        assert result == "50.0%"
    
    def test_format_percentage_decimal(self):
        """Test formatting decimal percentage"""
        result = format_percentage(0.123)
        assert result == "12.3%"
    
    def test_format_percentage_zero(self):
        """Test formatting zero percentage"""
        result = format_percentage(0)
        assert result == "0.0%"
    
    def test_format_percentage_over_one(self):
        """Test formatting >100%"""
        result = format_percentage(1.5)
        assert result == "150.0%"

    def test_format_percentage_small(self):
        """Test formatting small percentage"""
        result = format_percentage(0.001)
        assert result == "0.1%"

    def test_format_percentage_exactly_one(self):
        """Test formatting exactly 100%"""
        result = format_percentage(1.0)
        assert result == "100.0%"
