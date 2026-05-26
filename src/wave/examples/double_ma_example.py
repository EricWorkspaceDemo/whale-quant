"""Example: Double MA Strategy Backtest.

This example demonstrates how to use the Wave backtesting framework
to run a dual moving average crossover strategy.

Based on docs/ch07.2 and ch07.3 double MA strategy.
"""

import pandas as pd
import numpy as np

from wave import BacktestEngine, double_ma_strategy
from wave.metrics import calculate_all_metrics


def create_sample_data(n_days=252):
    """Create synthetic stock data for demonstration."""
    dates = pd.date_range("2023-01-01", periods=n_days, freq="B")

    # Generate random walk price series
    np.random.seed(42)
    returns = np.random.normal(0.0005, 0.02, n_days)
    prices = 100 * np.exp(np.cumsum(returns))

    df = pd.DataFrame({
        "open": prices + np.random.uniform(-1, 1, n_days),
        "high": prices + np.abs(np.random.uniform(0, 1, n_days)),
        "low": prices - np.abs(np.random.uniform(0, 1, n_days)),
        "close": prices,
        "volume": [1000000] * n_days,
    }, index=dates)

    return df


def main():
    """Run double MA strategy backtest example."""
    print("=" * 60)
    print("Wave Quantitative Backtesting Framework - Example")
    print("=" * 60)

    # Create sample data
    print("\n[1/4] Creating sample stock data...")
    stock_df = create_sample_data(n_days=252)
    print(f"    Loaded {len(stock_df)} trading days of data")
    print(f"    Price range: ${stock_df['close'].min():.2f} - ${stock_df['close'].max():.2f}")

    # Initialize engine
    print("\n[2/4] Initializing backtest engine...")
    engine = BacktestEngine(
        initial_cash=100000.0,
        commission=0.001,  # 0.1% per trade
        slippage=0.001,    # 0.1% slippage
    )
    engine.add_data('stock', stock_df)
    print("    Initial cash: $100,000")
    print("    Commission: 0.1%")
    print("    Slippage: 0.1%")

    # Run backtest with Double MA strategy
    print("\n[3/4] Running Double MA strategy (MA5 vs MA10)...")
    strategy_fn = double_ma_strategy(fast_period=5, slow_period=10)
    result = engine.run(strategy_fn)

    # Display results
    print("\n[4/4] Backtest Results:")
    print("-" * 40)

    metrics = result.metrics

    print(f"\nPerformance Metrics:")
    print(f"  Total Return:      {metrics.get('total_return', 0)*100:+.2f}%")
    print(f"  Annual Return:     {metrics.get('annual_return', 0)*100:+.2f}%")
    print(f"  Volatility:        {metrics.get('volatility', 0)*100:.2f}%")
    print(f"  Max Drawdown:      {metrics.get('max_drawdown', 0)*100:.2f}%")
    print(f"  Sharpe Ratio:      {metrics.get('sharpe_ratio', 0):.3f}")
    print(f"  Sortino Ratio:     {metrics.get('sortino_ratio', 0):.3f}")
    print(f"  Calmar Ratio:      {metrics.get('calmar_ratio', 0):.3f}")

    if 'alpha' in metrics:
        print(f"\nRisk-adjusted Metrics (vs Benchmark):")
        print(f"  Alpha (annualized): {metrics['alpha']:.4f}")
        print(f"  Beta:              {metrics['beta']:.3f}")
        print(f"  Information Ratio: {metrics['information_ratio']:.3f}")

    print(f"\nPosition Stats:")
    print(f"  Final Equity:      ${result.portfolio.total_equity:,.2f}")
    print(f"  Day Change:        ${result.portfolio.day_change:,.2f} ({result.portfolio.day_change_pct:+.2f}%)")
    print(f"  Positions Held:    {result.portfolio.num_positions}")

    print(f"\nStrategy Activity:")
    trades = engine.get_trades()
    print(f"  Total Trades:      {len(trades)}")

    # Show NAV curve info
    print(f"\nNAV Summary:")
    print(f"  Starting NAV:      ${result.nav.iloc[0]:,.2f}")
    print(f"  Ending NAV:        ${result.nav.iloc[-1]:,.2f}")
    print(f"  Peak NAV:          ${result.nav.max():,.2f}")
    print(f"  Lowest NAV:        ${result.nav.min():,.2f}")

    # Plot if matplotlib available
    try:
        print("\nGenerating charts...")
        fig = result.plot()
        print("Charts saved to: backtest_result.png")
        fig.savefig('backtest_result.png', dpi=150, bbox_inches='tight')
    except ImportError:
        print("\nNote: Install matplotlib to view charts.")

    print("\n" + "=" * 60)
    print("Example completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
