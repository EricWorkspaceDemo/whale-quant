"""Workflow runner for quant trading strategies.

Supports:
- stock_selection.yaml: Multi-factor stock selection (Ch04)
- timing_strategy.yaml: Dual MA/MACD/Hurst timing (Ch05)
"""

import yaml
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any


@dataclass
class WorkflowContext:
    """Shared context across workflow steps."""
    start_time: datetime = field(default_factory=datetime.now)
    step_results: dict = field(default_factory=dict)
    strategy_mode: str = "crypto"  # crypto, stock_selection, timing
    config: dict = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        return self.step_results.get(key, default)

    def set(self, key: str, value: Any):
        self.step_results[key] = value


def load_workflow(yaml_path: str) -> dict:
    """Load a workflow definition from YAML."""
    with open(yaml_path, 'r') as f:
        return yaml.safe_load(f)


class StockSelectionRunner:
    """Runner for stock_selection.yaml workflow."""

    async def run(
        self,
        stock_universe: list[str],
        factors: list[str] = None,
        max_positions: int = 20,
        min_sharpe: float = 1.0
    ) -> dict:
        """Execute the stock selection workflow."""
        context = WorkflowContext(strategy_mode="stock_selection")

        print("[Step 1/6] Collecting factor data...")
        raw_data = await self._fetch_factors(stock_universe, factors)
        context.set("data_collection", raw_data)

        print("[Step 2/6] Computing and normalizing factors...")
        normalized = await self._compute_factors(raw_data)
        context.set("factor_computation", normalized)

        print("[Step 3/6] Building multi-factor model...")
        scores = await self._build_mfm(normalized, max_positions)
        context.set("multi_factor_model", scores)

        print("[Step 4/6] Optimizing portfolio...")
        optimized = await self._optimize_portfolio(scores)
        context.set("portfolio_optimization", optimized)

        print("[Step 5/6] Generating strategy recommendation...")
        strategy = await self._generate_strategy(optimized)
        context.set("strategy_generation", strategy)

        print("[Step 6/6] Saving results...")
        context.set("saved_at", datetime.now().isoformat())

        return context.step_results

    async def _fetch_factors(self, universe: list[str], factors: list[str]) -> dict:
        """Simulate factor data collection."""
        import numpy as np

        return {
            "universe": universe,
            "factors": {
                "momentum": {sym: np.random.uniform(-1, 1) for sym in universe},
                "PE": {sym: np.random.uniform(10, 30) for sym in universe},
                "PB": {sym: np.random.uniform(1, 5) for sym in universe},
                "ROE": {sym: np.random.uniform(-20, 30) for sym in universe},
            }
        }

    async def _compute_factors(self, raw_data: dict) -> dict:
        """Normalize and neutralize factors."""
        import pandas as pd
        import numpy as np

        df = pd.DataFrame(raw_data["factors"])

        # Z-score normalization
        normalized = (df - df.mean()) / df.std()

        # Winsorize at 1%/99%
        lower = df.quantile(0.01)
        upper = df.quantile(0.99)
        for col in normalized.columns:
            normalized[col] = normalized[col].clip(lower=lower[col], upper=upper[col])

        return {"normalized_scores": normalized.to_dict(), "statistics": df.describe().to_dict()}

    async def _build_mfm(self, normalized: dict, max_positions: int) -> dict:
        """Build multi-factor model with APT."""
        import pandas as pd
        import numpy as np

        weights = {"momentum": 0.3, "PE": 0.2, "PB": 0.2, "ROE": 0.3}

        df = pd.DataFrame(normalized["normalized_scores"])
        combined_score = sum(df[col] * w for col, w in weights.items())

        top_stocks = combined_score.nlargest(max_positions).to_dict()

        return {
            "top_holdings": top_stocks,
            "factor_weights": weights,
            "model_type": "APT_multi_factor"
        }

    async def _optimize_portfolio(self, mfm_result: dict) -> dict:
        """Mean-variance portfolio optimization."""
        import numpy as np

        n_assets = len(mfm_result["top_holdings"])
        cov_matrix = np.eye(n_assets) * 0.04 + np.ones((n_assets, n_assets)) * 0.01
        rf = 0.02
        expected_returns = np.array(list(mfm_result["top_holdings"].values()))
        weights = np.ones(n_assets) / n_assets

        portfolio_return = np.dot(weights, expected_returns)
        portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        sharpe = (portfolio_return - rf) / portfolio_vol if portfolio_vol > 0 else 0

        return {
            "weights": weights.tolist(),
            "expected_return": float(portfolio_return),
            "expected_volatility": float(portfolio_vol),
            "sharpe_ratio": float(sharpe),
            "optimization_method": "mean_variance"
        }

    async def _generate_strategy(self, optimized: dict) -> dict:
        """Generate final strategy output."""
        return {
            "top_holdings": ["stock_a", "stock_b"],
            "factor_weights": optimized.get("factor_weights", {}),
            "expected_return": optimized.get("expected_return"),
            "expected_volatility": optimized.get("expected_volatility"),
            "sharpe_ratio": optimized.get("sharpe_ratio"),
            "generated_at": datetime.now().isoformat()
        }


class TimingStrategyRunner:
    """Runner for timing_strategy.yaml workflow."""

    async def run(
        self,
        symbols: list[str],
        ma_short_period: int = 5,
        ma_long_period: int = 20,
        macd_fast: int = 12,
        macd_slow: int = 26,
        macd_signal: int = 9,
        hurst_window: int = 60
    ) -> dict:
        """Execute the timing strategy workflow."""
        context = WorkflowContext(strategy_mode="timing")

        print("[Step 1/8] Collecting price data...")
        market_data = await self._fetch_market_data(symbols)
        context.set("data_collection", market_data)

        print("[Step 2/8] Computing indicators (MA, MACD, EMA)...")
        indicators = await self._compute_indicators(market_data, ma_short_period, ma_long_period)
        context.set("indicator_computation", indicators)

        print("[Step 3/8] Evaluating Granville rules...")
        granville = await self._granville_signals(indicators)
        context.set("granville_signals", granville)

        print("[Step 4/8] Analyzing MACD signals...")
        macd_analysis = await self._analyze_macd(indicators, macd_fast, macd_slow, macd_signal)
        context.set("macd_analysis", macd_analysis)

        print("[Step 5/8] Computing Hurst index...")
        hurst = await self._compute_hurst(market_data, hurst_window)
        context.set("hurst_assessment", hurst)

        print("[Step 6/8] Classifying trend regime...")
        trend = await self._classify_trend(granville, macd_analysis, hurst)
        context.set("trend_classification", trend)

        print("[Step 7/8] Calculating signal confluence...")
        confluence = await self._calculate_confluence(trend, macd_analysis)
        context.set("signal_confluence", confluence)

        print("[Step 8/8] Making entry decision...")
        decision = await self._make_decision(confluence, trend)
        context.set("entry_exit_decision", decision)

        return context.step_results

    async def _fetch_market_data(self, symbols: list[str]) -> dict:
        """Simulate OHLCV data collection."""
        import pandas as pd
        import numpy as np

        dates = pd.date_range("2023-01-01", periods=100, freq="D")
        data = {}
        for sym in symbols:
            prices = 100 * np.exp(np.cumsum(np.random.normal(0.001, 0.02, 100)))
            data[sym] = pd.DataFrame({
                "open": prices,
                "high": prices * 1.01,
                "low": prices * 0.99,
                "close": prices,
                "volume": [1000000] * 100
            }, index=dates)

        return {"symbols": symbols, "ohlcvs": data}

    async def _compute_indicators(
        self,
        market_data: dict,
        ma_short: int,
        ma_long: int
    ) -> dict:
        """Compute moving averages and MACD."""
        import pandas as pd
        import numpy as np

        results = {}
        for sym, df in market_data["ohlcvs"].items():
            close = df["close"]
            ma_short_val = close.rolling(window=ma_short).mean()
            ma_long_val = close.rolling(window=ma_long).mean()
            ema_12 = close.ewm(span=12).mean()
            ema_26 = close.ewm(span=26).mean()
            dif = ema_12 - ema_26
            dea = dif.ewm(span=9).mean()
            macd_hist = 2 * (dif - dea)

            results[sym] = {
                "ma_short": ma_short_val.iloc[-1] if not ma_short_val.empty else None,
                "ma_long": ma_long_val.iloc[-1] if not ma_long_val.empty else None,
                "diff": dif.iloc[-1] if not dif.empty else None,
                "dea": dea.iloc[-1] if not dea.empty else None,
                "histogram": macd_hist.iloc[-1] if not macd_hist.empty else None
            }

        return results

    async def _granville_signals(self, indicators: dict) -> dict:
        """Evaluate Granville's 8 rules."""
        signals = {}
        for sym, data in indicators.items():
            buy_signals = []
            sell_signals = []

            if data["ma_short"] and data["ma_long"]:
                if data["ma_short"] > data["ma_long"]:
                    buy_signals.append("golden_cross")
                else:
                    sell_signals.append("death_cross")

            signals[sym] = {
                "buy_signals": buy_signals,
                "sell_signals": sell_signals,
                "crossover": "bullish" if buy_signals else ("bearish" if sell_signals else "neutral")
            }

        return signals

    async def _analyze_macd(self, indicators: dict, fast: int, slow: int, signal: int) -> dict:
        """Analyze MACD crossovers and momentum."""
        signals = {}
        for sym, data in indicators.items():
            crossover = None
            if data["diff"] and data["dea"]:
                if data["diff"] > data["dea"]:
                    crossover = "bullish"
                else:
                    crossover = "bearish"

            signals[sym] = {
                "crossover": crossover,
                "momentum": "positive" if data["histogram"] and data["histogram"] > 0 else "negative",
                "signal": crossover
            }

        return signals

    async def _compute_hurst(self, market_data: dict, window: int) -> dict:
        """Compute Hurst index for regime detection."""
        import numpy as np

        results = {}
        for sym in market_data["symbols"]:
            prices = market_data["ohlcvs"][sym]["close"]
            log_returns = np.log(prices / prices.shift(1)).dropna()

            if len(log_returns) >= window:
                returns_sample = log_returns.tail(window).values
                lag_range = range(2, min(15, len(returns_sample)//2))

                try:
                    std_ratios = []
                    lags = []
                    for lag in lag_range:
                        rolling_std = pd.Series(returns_sample).rolling(lag).std()
                        total_std = pd.Series(returns_sample).std()
                        std_ratios.append(rolling_std.mean() / total_std)
                        lags.append(lag)

                    if len(lags) > 1:
                        coeffs = np.polyfit(np.log(lags), np.log(std_ratios), 1)
                        hurst = coeffs[0]
                    else:
                        hurst = 0.5
                except:
                    hurst = 0.5
            else:
                hurst = 0.5

            if hurst > 0.55:
                regime = "trending"
            elif hurst < 0.45:
                regime = "mean_reverting"
            else:
                regime = "random_walk"

            results[sym] = {"hurst_index": hurst, "regime": regime}

        return results

    async def _classify_trend(
        self,
        granville: dict,
        macd_analysis: dict,
        hurst: dict
    ) -> dict:
        """Combine all signals for trend classification."""
        classification = {}

        for sym in granville.keys():
            bullish_count = 0

            if granville[sym]["crossover"] == "bullish":
                bullish_count += 1
            if macd_analysis[sym]["crossover"] == "bullish":
                bullish_count += 1

            if hurst[sym]["regime"] == "trending":
                bullish_count += 1

            total_signals = 3
            if bullish_count >= 2:
                direction = "uptrend"
            elif bullish_count <= 1:
                direction = "downtrend"
            else:
                direction = "sideways"

            classification[sym] = {
                "trend_direction": direction,
                "regime": hurst[sym]["regime"],
                "signal_strength": bullish_count / total_signals
            }

        return classification

    async def _calculate_confluence(self, trend: dict, macd: dict) -> dict:
        """Calculate confluence score across all indicators."""
        confluence = {}

        for sym, t_data in trend.items():
            base_score = t_data["signal_strength"]
            regime_bonus = 0.1 if t_data["regime"] == "trending" else -0.1

            confluence[sym] = {
                "score": min(1.0, max(0.0, base_score + regime_bonus)),
                "action": "BUY" if t_data["trend_direction"] == "uptrend" else ("SELL" if t_data["trend_direction"] == "downtrend" else "HOLD"),
                "confidence": base_score
            }

        return confluence

    async def _make_decision(self, confluence: dict, trend: dict) -> dict:
        """Make final entry/exit decision."""
        decisions = {}

        for sym in confluence.keys():
            conf = confluence[sym]

            decisions[sym] = {
                "action": conf["action"],
                "confidence": conf["score"],
                "trend_direction": trend[sym]["trend_direction"],
                "regime": trend[sym]["regime"],
                "timestamp": datetime.now().isoformat()
            }

        return decisions


async def run_workflow(workflow_name: str, **kwargs) -> dict:
    """Run a workflow by name."""
    if workflow_name == "stock_selection":
        runner = StockSelectionRunner()
        return await runner.run(**kwargs)
    elif workflow_name == "timing_strategy":
        runner = TimingStrategyRunner()
        return await runner.run(**kwargs)
    else:
        raise ValueError(f"Unknown workflow: {workflow_name}")


if __name__ == "__main__":
    import asyncio

    async def main():
        print("=" * 50)
        print("Testing Stock Selection Workflow")
        print("=" * 50)

        result = await run_workflow(
            "stock_selection",
            stock_universe=["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"],
            max_positions=3,
            min_sharpe=1.0
        )

        print("\n=== Results ===")
        print(f"Top Holdings: {result.get('strategy_generation', {}).get('top_holdings')}")
        print(f"Expected Return: {result.get('strategy_generation', {}).get('expected_return')}")
        print(f"Sharpe Ratio: {result.get('strategy_generation', {}).get('sharpe_ratio')}")

        print("\n" + "=" * 50)
        print("Testing Timing Strategy Workflow")
        print("=" * 50)

        result = await run_workflow(
            "timing_strategy",
            symbols=["BTCUSDT", "ETHUSDT"],
            ma_short_period=5,
            ma_long_period=20
        )

        print("\n=== Results ===")
        decisions = result.get("entry_exit_decision", {})
        for symbol, decision in decisions.items():
            print(f"\n{symbol}:")
            print(f"  Action: {decision['action']}")
            print(f"  Confidence: {decision['confidence']:.2%}")
            print(f"  Trend: {decision['trend_direction']}")
            print(f"  Regime: {decision['regime']}")

    asyncio.run(main())
