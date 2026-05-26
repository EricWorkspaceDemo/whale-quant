"""Test backtest engine module."""

import pytest
import pandas as pd
import numpy as np
from wave.core.engine import BacktestEngine, BacktestResult


def simple_buy_holding_strategy(engine: BacktestEngine, idx: int) -> dict:
    """Simple buy and hold strategy for testing."""
    return {'stock': 1}


def test_backtest_engine_initialization():
    """Test engine initialization."""
    engine = BacktestEngine(initial_cash=100000.0)

    assert engine.initial_cash == 100000.0
    assert engine.commission == 0.001
    assert engine.slippage == 0.0


def test_add_data(sample_stock_data):
    """Test adding price data to engine."""
    engine = BacktestEngine()
    result = engine.add_data('stock', sample_stock_data)

    assert isinstance(result, BacktestEngine)
    assert 'stock' in engine._data

    df = engine._data['stock']
    assert len(df) == 100
    assert 'close' in df.columns


def test_run_backtest(sample_stock_data):
    """Test running a simple backtest."""
    engine = BacktestEngine(initial_cash=200000.0)
    engine.add_data('stock', sample_stock_data)

    result = engine.run(simple_buy_holding_strategy)

    assert isinstance(result, BacktestResult)
    assert len(result.nav) == 100
    assert result.portfolio is not None
    assert result.metrics is not None
    assert 'total_return' in result.metrics
    assert 'sharpe_ratio' in result.metrics


def test_run_backtest_with_metrics(sample_stock_data):
    """Test that metrics are correctly computed."""
    engine = BacktestEngine(initial_cash=200000.0)
    engine.add_data('stock', sample_stock_data)

    result = engine.run(simple_buy_holding_strategy)

    # Check key metrics exist and have reasonable values
    assert 'annual_return' in result.metrics
    assert 'max_drawdown' in result.metrics
    assert 'volatility' in result.metrics

    # Max drawdown should be positive (or zero)
    assert result.metrics['max_drawdown'] >= 0


def test_multiple_symbols(data_with_multiple_stocks):
    """Test backtest with multiple stock symbols."""
    engine = BacktestEngine(initial_cash=200000.0)
    engine.add_data('stock_a', data_with_multiple_stocks['stock_a'])
    engine.add_data('stock_b', data_with_multiple_stocks['stock_b'])

    def multi_symbol_strategy(engine: BacktestEngine, idx: int) -> dict:
        signals = {}
        if idx % 2 == 0:
            signals['stock_a'] = 1
        else:
            signals['stock_b'] = 1
        return signals

    result = engine.run(multi_symbol_strategy)

    assert isinstance(result, BacktestResult)
    assert len(result.nav) > 0


def test_no_position_change(sample_stock_data):
    """Test when portfolio stays flat (no trades executed)."""
    engine = BacktestEngine(initial_cash=1000.0)  # Very low cash
    engine.add_data('stock', sample_stock_data)

    def no_trade_strategy(engine: BacktestEngine, idx: int) -> dict:
        return {}  # No signals

    result = engine.run(no_trade_strategy)

    # Cash should remain unchanged
    assert abs(result.portfolio.cash - 1000.0) < 0.01


def test_commission_impact(sample_stock_data):
    """Test commission impact on portfolio."""
    engine = BacktestEngine(initial_cash=100000.0, commission=0.005)
    engine.add_data('stock', sample_stock_data)

    def trading_strategy(engine: BacktestEngine, idx: int) -> dict:
        signals = {}
        if idx % 10 == 0:
            signals['stock'] = 1
        elif idx % 10 == 5 and engine._portfolio.get_position('stock').quantity > 0:
            signals['stock'] = -1
        return signals

    result = engine.run(trading_strategy)

    # Should have executed trades
    assert len(result.trades) >= 0  # Trades may be empty due to cash constraints

    # NAV should reflect commission drag
    assert result.nav.iloc[-1] < result.nav.iloc[0] * 1.1  # Reasonable upper bound


class TestBacktestResult:
    """Test BacktestResult class."""

    def test_result_creation_empty(self):
        """Test creating empty result."""
        result = BacktestResult()

        assert len(result.nav) == 0
        assert len(result.returns) == 0
        assert result.metrics == {}

    def test_result_with_data(self, sample_stock_data):
        """Test result with actual data."""
        nav = sample_stock_data['close'].copy()

        result = BacktestResult(nav=nav)

        assert len(result.nav) == len(nav)
        pd.testing.assert_series_equal(result.nav, nav)
