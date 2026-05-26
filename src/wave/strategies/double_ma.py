"""Double Moving Average crossover strategy.

Implements a classic dual moving average crossover strategy:
- When fast MA crosses above slow MA (golden cross), go long
- When fast MA crosses below slow MA (death cross), exit/short

This is based on the strategy in docs/ch07.2 and ch07.3.
"""

from typing import Dict, Callable
import pandas as pd


class DoubleMAStrategy:
    """Dual moving average crossover strategy.

    Attributes:
        fast_period: Period for fast moving average (default 5).
        slow_period: Period for slow moving average (default 10).
        fast_ma: Current value of fast moving average.
        slow_ma: Current value of slow moving average.
        prev_fast_ma: Previous fast MA value (for crossover detection).
        prev_slow_ma: Previous slow MA value (for crossover detection).
        position: Current position direction (1=long, -1=short, 0=flat).

    Usage:
        >>> strategy = DoubleMAStrategy(fast_period=5, slow_period=10)
        >>> signal = strategy.signal(df, idx)
        >>> if signal == 1:
        ...     # Buy
        ... elif signal == -1:
        ...     # Sell
    """

    def __init__(self, fast_period: int = 5, slow_period: int = 10):
        """Initialize the strategy.

        Args:
            fast_period: Period for fast moving average.
            slow_period: Period for slow moving average.

        Raises:
            ValueError: If fast_period >= slow_period.
        """
        if fast_period >= slow_period:
            raise ValueError(
                f"fast_period ({fast_period}) must be less than "
                f"slow_period ({slow_period})"
            )

        self.fast_period = fast_period
        self.slow_period = slow_period

        self._prev_fast_ma: float = None
        self._prev_slow_ma: float = None
        self._current_ma_available = False

    def signal(
        self,
        df: pd.DataFrame,
        idx: int,
    ) -> int:
        """Calculate trading signal for current bar.

        Args:
            df: DataFrame with 'close' column containing price data.
            idx: Current row index.

        Returns:
            Trading signal:
                1 = Go long (fast MA crossed above slow MA)
                -1 = Exit/Go short (fast MA crossed below slow MA)
                0 = Hold current position or no data

        Note:
            Signal generation requires at least `slow_period` bars of data.
        """
        if idx < self.slow_period - 1:
            return 0

        # Calculate MAs
        window_data = df['close'].iloc[max(0, idx - self.slow_period + 1):idx + 1]

        # Only use actual available data up to idx
        actual_window = min(idx + 1, len(window_data))
        prices = window_data.iloc[:actual_window].values

        fast_ma = prices[-self.fast_period:].mean() if len(prices) >= self.fast_period else prices.mean()
        slow_ma = prices.mean()

        # Store previous values on first calculation
        if not self._current_ma_available:
            self._prev_fast_ma = fast_ma
            self._prev_slow_ma = slow_ma
            self._current_ma_available = True
            return 0

        # Detect crossover
        prev_cross = self._prev_fast_ma > self._prev_slow_ma
        curr_cross = fast_ma > slow_ma

        signal = 0
        if not prev_cross and curr_cross:
            # Golden cross: fast MA crossed above slow MA
            signal = 1
        elif prev_cross and not curr_cross:
            # Death cross: fast MA crossed below slow MA
            signal = -1

        # Update previous values
        self._prev_fast_ma = fast_ma
        self._prev_slow_ma = slow_ma

        return signal

    def reset(self) -> None:
        """Reset internal state for new backtest run."""
        self._prev_fast_ma = None
        self._prev_slow_ma = None
        self._current_ma_available = False


def double_ma_strategy(
    fast_period: int = 5,
    slow_period: int = 10,
) -> Callable:
    """Factory function to create a DoubleMA strategy closure.

    This creates a strategy function compatible with BacktestEngine.run().

    Args:
        fast_period: Period for fast moving average.
        slow_period: Period for slow moving average.

    Returns:
        Strategy function with signature: fn(engine, idx) -> Dict[str, int]

    Usage:
        >>> strategy_fn = double_ma_strategy(fast_period=5, slow_period=10)
        >>> result = engine.run(strategy_fn)
    """
    strategy = DoubleMAStrategy(fast_period=fast_period, slow_period=slow_period)

    def strategy_fn(engine, idx: int) -> Dict[str, int]:
        """Strategy function for BacktestEngine.

        Args:
            engine: BacktestEngine instance.
            idx: Current index in data series.

        Returns:
            Dictionary mapping symbol to signal (-1, 0, 1).
        """
        # Reset strategy on each run's first call
        if idx == 0:
            strategy.reset()

        # Get primary symbol data
        all_symbols = list(engine._data.keys())
        primary_symbol = all_symbols[0]

        df = engine._data[primary_symbol]
        signal = strategy.signal(df, idx)

        return {primary_symbol: signal}

    return strategy_fn
