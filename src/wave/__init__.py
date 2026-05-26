"""Wave - 轻量级量化回测框架.

参考 docs/ch07 设计，提供:
- 轻量级回测引擎(无复杂继承)
- 完整评估指标体系 (ch07.1)
- 经典策略示例 (ch07.2-7.3)
- 多种数据源支持 (Tushare API + CSV)

Usage:
    from wave import BacktestEngine, DoubleMAStrategy
    from wave.metrics import calculate_all_metrics

    engine = BacktestEngine(initial_cash=100000)
    engine.add_data('stock', df_stock)
    result = engine.run(DoubleMAStrategy(fast_period=5, slow_period=10))
    print(result.metrics)
"""

from wave.core.engine import BacktestEngine, BacktestResult
from wave.strategies.double_ma import DoubleMAStrategy, double_ma_strategy
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

__version__ = "0.1.0"

__all__ = [
    # Engine
    "BacktestEngine",
    "BacktestResult",
    # Strategies
    "DoubleMAStrategy",
    "double_ma_strategy",
    # Metrics
    "calculate_total_return",
    "calculate_annual_return",
    "calculate_volatility",
    "calculate_max_drawdown",
    "calculate_sharpe_ratio",
    "calculate_information_ratio",
    "calculate_alpha_beta",
    "calculate_calmar_ratio",
    "calculate_sortino_ratio",
    "calculate_all_metrics",
]
