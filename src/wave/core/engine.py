"""Engine module for backtest execution.

Core backtest engine that orchestrates:
- Data feeding
- Strategy execution
- Portfolio management
- Performance tracking
"""

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional
import pandas as pd
import numpy as np

from wave.core.portfolio import Portfolio
from wave.metrics.evaluation import calculate_all_metrics


@dataclass
class BacktestResult:
    """Container for backtest results.

    Attributes:
        nav: Net asset value time series.
        returns: Period returns.
        metrics: Dictionary of performance metrics.
        trades: List of executed trades.
        portfolio: Final portfolio state.
    """
    nav: pd.Series = field(default_factory=pd.Series)
    returns: pd.Series = field(default_factory=pd.Series)
    metrics: Dict = field(default_factory=dict)
    trades: List[Dict] = field(default_factory=list)
    portfolio: Optional[Portfolio] = None

    def plot(self, **kwargs):
        """Plot NAV curve and drawdown.

        Args:
            **kwargs: Additional arguments to matplotlib.

        Returns:
            matplotlib figure object.
        """
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            raise ImportError("matplotlib is required for plotting")

        fig, axes = plt.subplots(2, 1, figsize=(12, 8))

        # Plot NAV
        self.nav.plot(ax=axes[0], title='Net Asset Value')
        axes[0].set_ylabel('NAV')
        axes[0].grid(True)

        # Calculate and plot drawdown
        running_max = self.nav.cummax()
        drawdown = (self.nav - running_max) / running_max
        drawdown.plot(ax=axes[1], color='red', alpha=0.5, title='Drawdown')
        axes[1].set_ylabel('Drawdown')
        axes[1].set_xlabel('Date')
        axes[1].fill_between(drawdown.index, drawdown, 0, color='red', alpha=0.3)
        axes[1].axhline(y=0, color='black', linewidth=1)
        axes[1].grid(True)

        return fig


class BacktestEngine:
    """Backtest engine for strategy evaluation.

    This engine provides a simple, flexible interface for running
    backtests with various strategies.

    Attributes:
        initial_cash: Starting capital.
        commission: Fixed commission per trade.
        slippage: Slippage rate as decimal.
        benchmark_symbol: Symbol for benchmark comparison.

    Usage:
        >>> engine = BacktestEngine(initial_cash=100000)
        >>> engine.add_data('stock', df_stock)
        >>> engine.add_data('benchmark', df_benchmark)
        >>> result = engine.run(double_ma_strategy)
        >>> print(result.metrics['sharpe_ratio'])
    """

    def __init__(
        self,
        initial_cash: float = 100000.0,
        commission: float = 0.001,
        slippage: float = 0.0,
    ):
        """Initialize the backtest engine.

        Args:
            initial_cash: Starting cash balance.
            commission: Transaction commission rate (default 0.1%).
            slippage: Expected slippage rate (default 0).
        """
        self.initial_cash = initial_cash
        self.commission = commission
        self.slippage = slippage

        self._data: Dict[str, pd.DataFrame] = {}
        self._portfolio: Portfolio = Portfolio(initial_cash=initial_cash)
        self._results: List[Dict] = []
        self._idx_to_date: Dict[int, pd.Timestamp] = {}

    def add_data(
        self,
        symbol: str,
        df: pd.DataFrame,
    ) -> 'BacktestEngine':
        """Add price data for a symbol.

        Args:
            symbol: Symbol identifier.
            df: DataFrame with columns ['open', 'high', 'low', 'close', 'volume']
               or at minimum ['close'].

        Returns:
            Self for method chaining.
        """
        df_copy = df.copy()

        if isinstance(df_copy.index, pd.DatetimeIndex):
            pass
        elif hasattr(df_copy.index, 'name') and df_copy.index.name == 'date':
            df_copy.index = pd.to_datetime(df_copy.index)
        else:
            df_copy.index = pd.to_datetime(df_copy.index)

        df_copy = df_copy.sort_index()

        self._data[symbol] = df_copy

        # Build index mapping
        for i, date in enumerate(df_copy.index):
            self._idx_to_date[i] = date

        return self

    def run(self, strategy_fn: Callable) -> BacktestResult:
        """Execute backtest with given strategy.

        Args:
            strategy_fn: Strategy function that takes (engine, idx)
                        and returns trading signals.

        Returns:
            BacktestResult containing NAV, metrics, and trades.
        """
        # Reset state
        self._portfolio = Portfolio(initial_cash=self.initial_cash)
        self._results = []

        # Get sorted symbols and dates
        all_symbols = list(self._data.keys())
        primary_symbol = all_symbols[0]
        dates = sorted(self._data[primary_symbol].index)

        # Run backtest loop
        nav_series = []
        date_index = []

        for i, date in enumerate(dates):
            # Call strategy
            signals = strategy_fn(self, i)

            # Execute signals
            self._execute_signals(signals, date)

            # Record NAV
            current_nav = self._portfolio.total_equity
            nav_series.append(current_nav)
            date_index.append(date)

        # Create result
        result = BacktestResult(
            nav=pd.Series(nav_series, index=date_index),
            returns=pd.Series(nav_series, index=date_index).pct_change().dropna(),
            portfolio=self._portfolio,
        )

        # Calculate metrics
        benchmark_returns = None
        if 'benchmark' in self._data:
            bench_nav = self._data['benchmark']['close']
            benchmark_returns = bench_nav.pct_change().dropna()

        result.metrics = calculate_all_metrics(
            result.nav,
            benchmark_returns,
        )

        return result

    def _execute_signals(
        self,
        signals: Dict[str, int],
        date: pd.Timestamp,
    ) -> None:
        """Execute trading signals.

        Args:
            signals: Dict mapping symbol to signal (-1=sell, 0=flat, 1=buy).
            date: Current date.
        """
        trade_log = {'date': date, 'trades': []}

        for symbol, signal in signals.items():
            if symbol not in self._data:
                continue

            df = self._data[symbol]
            row = df.loc[date]

            price = row['close']
            apply_slippage = price * (1 + self.slippage) if signal > 0 else \
                           price * (1 - self.slippage)

            pos = self._portfolio.get_position(symbol)

            if signal > 0 and pos.quantity <= 0:
                # Buy: use available cash
                shares = int(self._portfolio.cash / apply_slippage)
                if shares > 0:
                    cost = shares * apply_slippage * (1 + self.commission)
                    if cost <= self._portfolio.cash:
                        self._portfolio.buy(symbol, shares, apply_slippage)
                        trade_log['trades'].append({
                            'symbol': symbol,
                            'action': 'BUY',
                            'shares': shares,
                            'price': apply_slippage,
                        })

            elif signal < 0 and pos.quantity > 0:
                # Sell: close position
                shares = pos.quantity
                proceeds = shares * apply_slippage * (1 - self.commission)
                self._portfolio.sell(symbol, shares, apply_slippage)
                trade_log['trades'].append({
                    'symbol': symbol,
                    'action': 'SELL',
                    'shares': shares,
                    'price': apply_slippage,
                })

        if trade_log['trades']:
            self._results.append(trade_log)

    def get_trades(self) -> List[Dict]:
        """Get all executed trades.

        Returns:
            List of trade dictionaries.
        """
        trades = []
        for entry in self._results:
            trades.extend(entry.get('trades', []))
        return trades
