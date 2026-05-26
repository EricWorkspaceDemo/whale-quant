"""Test metrics evaluation module."""

import pytest
import numpy as np
import pandas as pd
from wave.metrics.evaluation import (
    calculate_total_return,
    calculate_annual_return,
    calculate_volatility,
    calculate_max_drawdown,
    calculate_sharpe_ratio,
    calculate_information_ratio,
    calculate_alpha_beta,
    calculate_calmar_ratio,
    calculate_sortino_ratio,
    calculate_all_metrics,
)


class TestTotalReturn:
    """Test total return calculation."""

    def test_positive_return(self):
        """Test calculation with positive returns."""
        nav = pd.Series([100, 110, 121], index=[0, 1, 2])
        result = calculate_total_return(nav)
        assert abs(result - 0.21) < 0.0001

    def test_negative_return(self):
        """Test calculation with negative returns."""
        nav = pd.Series([100, 90, 81], index=[0, 1, 2])
        result = calculate_total_return(nav)
        assert abs(result - (-0.19)) < 0.0001

    def test_no_change(self):
        """Test when NAV doesn't change."""
        nav = pd.Series([100, 100, 100], index=[0, 1, 2])
        result = calculate_total_return(nav)
        assert result == 0.0


class TestAnnualReturn:
    """Test annualized return calculation."""

    def test_one_year_period(self):
        """Test with exactly one year (252 trading days)."""
        total_ret = 0.26
        result = calculate_annual_return(total_ret, 252)
        expected = 0.26
        assert abs(result - expected) < 0.001

    def test_two_year_period(self):
        """Test with two year period."""
        total_ret = 0.5625
        result = calculate_annual_return(total_ret, 504)
        expected = 0.25
        assert abs(result - expected) < 0.01


class TestVolatility:
    """Test volatility calculation."""

    def test_constant_returns(self):
        """Test with constant returns (zero vol)."""
        returns = pd.Series([0.01] * 100)
        result = calculate_volatility(returns)
        assert abs(result) < 1e-10

    def test_high_volatility(self):
        """Test with high variance returns."""
        np.random.seed(42)
        returns = pd.Series(np.random.normal(0.001, 0.03, 100))
        result = calculate_volatility(returns)
        assert result > 0.4 and result < 0.5


class TestMaxDrawdown:
    """Test max drawdown calculation."""

    def test_no_drawdown(self):
        """Test with steadily increasing NAV."""
        nav = pd.Series([100, 110, 120, 130, 140])
        result = calculate_max_drawdown(nav)
        assert result == 0.0

    def test_single_drop(self):
        """Test with single significant drop."""
        nav = pd.Series([100, 110, 100, 90, 100])
        result = calculate_max_drawdown(nav)
        assert abs(result - 0.1818) < 0.01


class TestSharpeRatio:
    """Test Sharpe ratio calculation."""

    def test_zero_volatility(self):
        """Test Sharpe with zero volatility."""
        returns = pd.Series([0.001] * 100)
        result = calculate_sharpe_ratio(returns, risk_free_rate=0.03)
        assert result > 0

    def test_negative_excess_return(self):
        """Test with negative excess returns."""
        np.random.seed(42)
        returns = pd.Series(np.random.normal(-0.0001, 0.02, 100))
        result = calculate_sharpe_ratio(returns, risk_free_rate=0.03)
        assert result < 0


class TestInformationRatio:
    """Test Information ratio calculation."""

    def test_perfect_correlation(self):
        """Test when strategy matches benchmark perfectly."""
        ben_ret = pd.Series([0.01, 0.02, 0.01, 0.03],
                           index=pd.date_range("2023-01-01", periods=4))
        str_ret = ben_ret.copy()

        result = calculate_information_ratio(str_ret, ben_ret)
        assert result == 0.0

    def test_different_returns(self):
        """Test with different strategy/benchmark returns."""
        ben_ret = pd.Series([0.01, 0.01, 0.01, 0.01],
                           index=pd.date_range("2023-01-01", periods=4))
        str_ret = pd.Series([0.02, 0.02, 0.02, 0.02],
                           index=pd.date_range("2023-01-01", periods=4))

        result = calculate_information_ratio(str_ret, ben_ret)
        # Active return has zero std (all same), so IR = 0
        assert result == 0.0


class TestAlphaBeta:
    """Test Alpha and Beta calculation."""

    def test_market_beta_one(self):
        """Test when beta should be approximately 1."""
        np.random.seed(42)
        ben_ret = pd.Series(np.random.normal(0.001, 0.02, 100),
                           index=pd.date_range("2023-01-01", periods=100))
        str_ret = ben_ret * 1.0 + 0.0001

        alpha, beta = calculate_alpha_beta(str_ret, ben_ret)
        assert abs(beta - 1.0) < 0.2
        assert alpha > 0

    def test_zero_beta(self):
        """Test when strategy has no market correlation."""
        ben_ret = pd.Series(np.random.normal(0.001, 0.02, 100),
                           index=pd.date_range("2023-01-01", periods=100))
        str_ret = pd.Series(np.random.normal(0.001, 0.02, 100),
                           index=pd.date_range("2023-01-01", periods=100))

        alpha, beta = calculate_alpha_beta(str_ret, ben_ret)
        assert abs(beta) < 0.5


class TestAllMetrics:
    """Test comprehensive metrics calculation."""

    def test_all_metrics_computation(self, sample_historical_data):
        """Test all metrics are computed correctly."""
        df = sample_historical_data
        nav = df["close"]

        metrics = calculate_all_metrics(nav)

        assert "total_return" in metrics
        assert "annual_return" in metrics
        assert "volatility" in metrics
        assert "max_drawdown" in metrics
        assert "sharpe_ratio" in metrics
        assert metrics["total_return"] != 0
