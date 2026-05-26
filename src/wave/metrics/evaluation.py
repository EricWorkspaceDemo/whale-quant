"""Metrics module for backtest evaluation.

Implements performance evaluation indicators from docs/ch07.1:
- Total return (累计收益率)
- Annualized return (年化收益率)
- Volatility (波动率)
- Max drawdown (最大回撤)
- Sharpe ratio (夏普比率)
- Information ratio (信息比率)
- Alpha/Beta coefficients (Alpha/Beta 系数)
"""

from typing import Optional
import numpy as np
import pandas as pd
from scipy import stats


def calculate_total_return(nav_series: pd.Series) -> float:
    """Calculate total (cumulative) return.

    Formula: R_t = (P_T - P_t) / P_t = P_T / P_t - 1

    Args:
        nav_series: Net asset value time series.

    Returns:
        Total return as a decimal (e.g., 0.25 for 25%).
    """
    return nav_series.iloc[-1] / nav_series.iloc[0] - 1


def calculate_annual_return(
    total_return: float,
    days: int,
    trading_days_per_year: int = 252,
) -> float:
    """Calculate annualized return.

    Formula: R_p = (1 + R)^(252/n) - 1

    Args:
        total_return: Total return over the period.
        days: Number of days in the period.
        trading_days_per_year: Trading days per year (default 252).

    Returns:
        Annualized return as a decimal.
    """
    if days <= 0:
        return 0.0
    return (1 + total_return) ** (trading_days_per_year / days) - 1


def calculate_volatility(
    returns: pd.Series,
    trading_days_per_year: int = 252,
) -> float:
    """Calculate annualized volatility (standard deviation).

    Formula: Volatility = sqrt(252/(n-1) * sum((r_p - mean)^2))

    Args:
        returns: Period returns (e.g., daily returns).
        trading_days_per_year: Trading days per year (default 252).

    Returns:
        Annualized volatility as a decimal.
    """
    if len(returns) < 2:
        return 0.0
    return np.std(returns, ddof=1) * np.sqrt(trading_days_per_year)


def calculate_max_drawdown(nav_series: pd.Series) -> float:
    """Calculate maximum drawdown.

    Formula: MaxDrawdown = max((Pi - Pj) / Pi)
    where Pi is a peak and Pj is a subsequent trough.

    Args:
        nav_series: Net asset value time series.

    Returns:
        Maximum drawdown as a positive decimal (e.g., 0.20 for 20% DD).
    """
    running_max = nav_series.cummax()
    drawdown = (nav_series - running_max) / running_max
    return abs(drawdown.min())


def calculate_sharpe_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.03,
    trading_days_per_year: int = 252,
) -> float:
    """Calculate Sharpe ratio.

    Formula: Sharpe = (R_p - R_f) / σ_p

    Where:
        R_p = Portfolio expected return
        R_f = Risk-free rate
        σ_p = Portfolio standard deviation

    Args:
        returns: Period returns (e.g., daily returns).
        risk_free_rate: Annual risk-free rate (default 3%).
        trading_days_per_year: Trading days per year (default 252).

    Returns:
        Sharpe ratio.
    """
    if len(returns) < 2:
        return 0.0

    daily_rf = risk_free_rate / trading_days_per_year
    excess_returns = returns - daily_rf

    if np.std(excess_returns, ddof=1) == 0:
        return 0.0

    return np.mean(excess_returns) / np.std(excess_returns, ddof=1) * np.sqrt(trading_days_per_year)


def calculate_information_ratio(
    strategy_returns: pd.Series,
    benchmark_returns: pd.Series,
    trading_days_per_year: int = 252,
) -> float:
    """Calculate Information ratio.

    Formula: IR = (R_p - R_b) / σ_tracking
    where σ_tracking is the standard deviation of active returns.

    Args:
        strategy_returns: Strategy returns.
        benchmark_returns: Benchmark returns.
        trading_days_per_year: Trading days per year (default 252).

    Returns:
        Information ratio.
    """
    common_idx = strategy_returns.index.intersection(benchmark_returns.index)
    str_ret = strategy_returns.loc[common_idx]
    ben_ret = benchmark_returns.loc[common_idx]

    active_returns = str_ret - ben_ret

    if len(active_returns) < 2:
        return 0.0

    if np.std(active_returns, ddof=1) == 0:
        return 0.0

    return np.mean(active_returns) / np.std(active_returns, ddof=1) * np.sqrt(trading_days_per_year)


def calculate_alpha_beta(
    strategy_returns: pd.Series,
    benchmark_returns: pd.Series,
    risk_free_rate: float = 0.03,
    trading_days_per_year: int = 252,
) -> tuple[float, float]:
    """Calculate Alpha and Beta coefficients using CAPM model.

    CAPM Model: r_i = α + β*r_m + ε

    Where:
        r_i = Asset/portfolio return
        r_m = Market/benchmark return
        α = Alpha (excess return not explained by market)
        β = Beta (systematic risk measure)

    Args:
        strategy_returns: Strategy returns.
        benchmark_returns: Benchmark returns.
        risk_free_rate: Annual risk-free rate (default 3%).
        trading_days_per_year: Trading days per year (default 252).

    Returns:
        Tuple of (annualized_alpha, beta).
    """
    common_idx = strategy_returns.index.intersection(benchmark_returns.index)
    str_ret = strategy_returns.loc[common_idx].dropna()
    ben_ret = benchmark_returns.loc[common_idx].dropna()

    if len(str_ret) < 2 or len(ben_ret) < 2:
        return 0.0, 0.0

    min_len = min(len(str_ret), len(ben_ret))
    str_ret = str_ret.iloc[:min_len]
    ben_ret = ben_ret.iloc[:min_len]

    slope, intercept, r_value, p_value, std_err = stats.linregress(ben_ret, str_ret)

    annual_alpha = intercept * trading_days_per_year

    return annual_alpha, slope


def calculate_calmar_ratio(
    nav_series: pd.Series,
    annual_return: float,
) -> float:
    """Calculate Calmar ratio.

    Formula: Calmar = Annual Return / |Max Drawdown|

    Args:
        nav_series: Net asset value time series.
        annual_return: Annualized return.

    Returns:
        Calmar ratio.
    """
    max_dd = calculate_max_drawdown(nav_series)
    if max_dd == 0:
        return 0.0
    return annual_return / max_dd


def calculate_sortino_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.03,
    trading_days_per_year: int = 252,
) -> float:
    """Calculate Sortino ratio (downside deviation version).

    Similar to Sharpe but uses only downside deviation.

    Args:
        returns: Period returns.
        risk_free_rate: Annual risk-free rate.
        trading_days_per_year: Trading days per year.

    Returns:
        Sortino ratio.
    """
    if len(returns) < 2:
        return 0.0

    daily_rf = risk_free_rate / trading_days_per_year
    excess_returns = returns - daily_rf

    downside_returns = excess_returns[excess_returns < 0]
    if len(downside_returns) == 0:
        return float('inf') if np.mean(excess_returns) > 0 else 0.0

    downside_std = np.std(downside_returns, ddof=1)
    if downside_std == 0:
        return 0.0

    return np.mean(excess_returns) / downside_std * np.sqrt(trading_days_per_year)


def calculate_win_rate(returns: pd.Series) -> float:
    """Calculate win rate (percentage of positive returns).

    Args:
        returns: Period returns.

    Returns:
        Win rate as a decimal (e.g., 0.55 for 55%).
    """
    if len(returns) == 0:
        return 0.0
    winning_trades = (returns > 0).sum()
    return winning_trades / len(returns)


def calculate_avg_win_loss_ratio(returns: pd.Series) -> float:
    """Calculate average win / average loss ratio.

    Args:
        returns: Period returns.

    Returns:
        Average win divided by absolute average loss.
    """
    winning_returns = returns[returns > 0]
    losing_returns = returns[returns < 0]

    if len(winning_returns) == 0 or len(losing_returns) == 0:
        return 0.0

    avg_win = winning_returns.mean()
    avg_loss = abs(losing_returns.mean())

    if avg_loss == 0:
        return 0.0

    return avg_win / avg_loss


def calculate_all_metrics(
    nav_series: pd.Series,
    benchmark_returns: Optional[pd.Series] = None,
    risk_free_rate: float = 0.03,
    trading_days_per_year: int = 252,
) -> dict:
    """Calculate all performance metrics at once.

    Args:
        nav_series: Net asset value time series.
        benchmark_returns: Optional benchmark returns for comparison metrics.
        risk_free_rate: Annual risk-free rate.
        trading_days_per_year: Trading days per year.

    Returns:
        Dictionary containing all calculated metrics.
    """
    total_return = calculate_total_return(nav_series)
    days = len(nav_series) - 1
    annual_return = calculate_annual_return(total_return, days, trading_days_per_year)

    returns = nav_series.pct_change().dropna()

    volatility = calculate_volatility(returns, trading_days_per_year)
    max_drawdown = calculate_max_drawdown(nav_series)
    sharpe = calculate_sharpe_ratio(returns, risk_free_rate, trading_days_per_year)
    sortino = calculate_sortino_ratio(returns, risk_free_rate, trading_days_per_year)
    calmar = calculate_calmar_ratio(nav_series, annual_return)

    win_rate = calculate_win_rate(returns)
    avg_win_loss = calculate_avg_win_loss_ratio(returns)

    result = {
        "total_return": total_return,
        "annual_return": annual_return,
        "volatility": volatility,
        "max_drawdown": max_drawdown,
        "sharpe_ratio": sharpe,
        "sortino_ratio": sortino,
        "calmar_ratio": calmar,
        "win_rate": win_rate,
        "avg_win_loss_ratio": avg_win_loss,
    }

    if benchmark_returns is not None:
        common_idx = returns.index.intersection(benchmark_returns.index)
        if len(common_idx) >= 2:
            str_ret = returns.loc[common_idx]
            ben_ret = benchmark_returns.loc[common_idx]

            result["information_ratio"] = calculate_information_ratio(
                str_ret, ben_ret, trading_days_per_year
            )
            alpha, beta = calculate_alpha_beta(
                str_ret, ben_ret, risk_free_rate, trading_days_per_year
            )
            result["alpha"] = alpha
            result["beta"] = beta

    return result
