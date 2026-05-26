"""Pytest configuration and shared fixtures."""

import pytest
import pandas as pd
import numpy as np


@pytest.fixture
def sample_stock_data():
    """Create sample stock data for testing."""
    dates = pd.date_range("2023-01-01", periods=100, freq="D")
    np.random.seed(42)

    returns = np.random.normal(0.001, 0.02, 100)
    prices = 100 * np.exp(np.cumsum(returns))

    df = pd.DataFrame({
        "open": prices + np.random.uniform(-1, 1, 100),
        "high": prices + np.abs(np.random.uniform(0, 1, 100)),
        "low": prices - np.abs(np.random.uniform(0, 1, 100)),
        "close": prices,
        "volume": np.random.randint(1000000, 10000000, 100),
    }, index=dates)

    return df


@pytest.fixture
def sample_benchmark_data():
    """Create sample benchmark data for testing."""
    dates = pd.date_range("2023-01-01", periods=100, freq="D")
    np.random.seed(43)

    returns = np.random.normal(0.0005, 0.015, 100)
    prices = 3000 * np.exp(np.cumsum(returns))

    df = pd.DataFrame({
        "close": prices,
    }, index=dates)

    return df


@pytest.fixture
def sample_historical_data():
    """Create sample historical price data."""
    dates = pd.date_range("2023-01-01", periods=50, freq="B")
    base_price = 1500.0

    prices = [base_price]
    for _ in range(49):
        change = np.random.normal(0, 0.02)
        prices.append(prices[-1] * (1 + change))

    df = pd.DataFrame({
        "open": prices,
        "high": [p * 1.02 for p in prices],
        "low": [p * 0.98 for p in prices],
        "close": prices,
        "volume": [1000000] * 50,
    }, index=dates)

    return df


@pytest.fixture
def portfolio_with_cash():
    """Create a portfolio with initial cash."""
    from wave.core.portfolio import Portfolio

    portfolio = Portfolio(initial_cash=100000.0)
    return portfolio


@pytest.fixture
def data_with_multiple_stocks():
    """Create test data with multiple stock symbols."""
    dates = pd.date_range("2023-01-01", periods=100, freq="D")

    # Stock A
    np.random.seed(42)
    prices_a = 100 * np.exp(np.cumsum(np.random.normal(0.001, 0.02, 100)))

    # Stock B
    np.random.seed(43)
    prices_b = 50 * np.exp(np.cumsum(np.random.normal(0.0005, 0.015, 100)))

    df_a = pd.DataFrame({
        "open": prices_a + np.random.uniform(-1, 1, 100),
        "high": prices_a + np.abs(np.random.uniform(0, 1, 100)),
        "low": prices_a - np.abs(np.random.uniform(0, 1, 100)),
        "close": prices_a,
        "volume": [1000000] * 100,
    }, index=dates)

    df_b = pd.DataFrame({
        "open": prices_b + np.random.uniform(-0.5, 0.5, 100),
        "high": prices_b + np.abs(np.random.uniform(0, 0.5, 100)),
        "low": prices_b - np.abs(np.random.uniform(0, 0.5, 100)),
        "close": prices_b,
        "volume": [500000] * 100,
    }, index=dates)

    return {"stock_a": df_a, "stock_b": df_b}


@pytest.fixture
def double_ma_sample_data():
    """Create sample data suitable for MA strategy testing."""
    dates = pd.date_range("2023-01-01", periods=100, freq="D")
    np.random.seed(42)

    # Generate more volatile series to trigger crossover signals
    returns = np.random.normal(0.002, 0.03, 100)
    prices = 100 * np.exp(np.cumsum(returns))

    df = pd.DataFrame({
        "open": prices + np.random.uniform(-1, 1, 100),
        "high": prices + np.abs(np.random.uniform(0, 1, 100)),
        "low": prices - np.abs(np.random.uniform(0, 1, 100)),
        "close": prices,
        "volume": [1000000] * 100,
    }, index=dates)

    return df
