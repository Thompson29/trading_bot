"""
Unit tests for core/profiles.py

Tests risk profile configurations and allocations.
"""

import pytest
from core.profiles import RISK_PROFILES


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

    @pytest.mark.parametrize("risk_level", [
        "very_conservative",
        "conservative",
        "moderate",
        "aggressive",
        "aggressive_growth"
    ])
    def test_profile_minimum_allocation(self, risk_level):
        """Test that each ETF has meaningful allocation (at least 5%)"""
        profile = RISK_PROFILES[risk_level]
        for symbol, weight in profile.items():
            assert weight >= 0.05, \
                f"{symbol} in {risk_level} has weight < 5%: {weight}"

    def test_very_conservative_bond_heavy(self):
        """Test that very conservative profile is bond-heavy"""
        profile = RISK_PROFILES["very_conservative"]
        assert profile["BND"] >= 0.5, "Very conservative should have 50%+ bonds"

    def test_aggressive_growth_equity_heavy(self):
        """Test that aggressive growth profile is equity-heavy"""
        profile = RISK_PROFILES["aggressive_growth"]
        stock_allocation = sum(v for k, v in profile.items() if k != "BND")
        assert stock_allocation >= 0.9, "Aggressive growth should have 90%+ stocks"

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

    def test_profile_etf_symbols_valid(self):
        """Test that all ETF symbols are valid tickers"""
        valid_symbols = {"VTI", "VOO", "VUG", "VTWO", "VXUS", "VEA", "BND", "VIG"}
        
        for profile_name, allocations in RISK_PROFILES.items():
            for symbol in allocations.keys():
                assert symbol in valid_symbols, \
                    f"Invalid symbol {symbol} in {profile_name}"

    def test_all_profiles_have_data(self):
        """Test that no profiles are empty"""
        for profile_name, allocations in RISK_PROFILES.items():
            assert len(allocations) > 0, f"{profile_name} is empty"
            assert len(allocations) >= 3, \
                f"{profile_name} should have at least 3 ETFs for diversification"

    def test_risk_profile_values_are_numeric(self):
        """Test that all allocation weights are numeric"""
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


class TestProfileIntegration:
    """Integration tests for profile usage"""
    
    def test_all_profiles_accessible(self):
        """Test that all profiles can be accessed"""
        expected_profiles = [
            "very_conservative",
            "conservative",
            "moderate",
            "aggressive",
            "aggressive_growth"
        ]
        
        for profile in expected_profiles:
            assert profile in RISK_PROFILES
            assert len(RISK_PROFILES[profile]) > 0

    def test_invalid_profile_not_found(self):
        """Test that invalid profiles are not in dictionary"""
        invalid_profiles = ["invalid", "super_aggressive", "ultra_conservative"]
        
        for profile in invalid_profiles:
            assert profile not in RISK_PROFILES
