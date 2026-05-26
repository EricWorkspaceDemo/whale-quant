# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Context

**WhaleQuant** (量化开源课程) is an educational quantitative finance course from Datawhale. It provides a complete learning journey from investment fundamentals to live trading, covering data acquisition, strategy research, backtesting, and paper trading. The content is delivered through Jupyter notebooks and documentation built with docsify.

## High-Level Architecture

### Documentation Site (docs/)

The main documentation is built with **docsify** and served statically:

- `docs/index.html` - Entry point for the site
- `docs/_sidebar.md` - Navigation structure
- `docs/chXX_*` - Chapter folders containing markdown documentation and images

To preview locally:
```bash
cd docs
pip install docsify-cli
docsify serve .
```

### Notebook Examples (notebook/)

Jupyter notebooks mirroring the documentation chapters:

| Folder | Topic |
|--------|-------|
| `ch01_投资与量化投资` | Investment basics and quantitative investing concepts |
| `ch02_金融市场的基础概念` | Financial market fundamentals (macro, monetary, statistics) |
| `ch03_股票数据获取` | Stock data acquisition using Tushare API |
| `ch04_量化选股策略` | Quantitative stock selection strategies |
| `ch05_量化择时策略` | Market timing strategies |
| `ch06_量化调仓策略` | Portfolio rebalancing strategies |
| `ch07_量化回测` | Backtesting framework and methodology |
| `ch08_机器学习与量化策略` | Machine learning applications in quant strategies |

### Learning Code (code/)

Self-contained Python modules demonstrating concepts:

- `code/ch03/` - Module examples including pandas operations, file I/O, NumPy integration, and custom modules
- Key files: `lec_pd_dataframes.py`, `lec_pd_csv.py`, `lec_pd_indexing.py`, `lec_pd_joins.py`, `lec_fileio.py`

### Risk Management Configuration (risk/)

Trading constraint definitions for the educational trading system:

- `risk/config.yaml` - Global limits (max positions, position size, leverage, risk per trade)
- `risk/blacklist.json` - Forbidden trading symbols
- `risk/limits.json` - Per-symbol position and leverage overrides

### Prompt Templates (prompts/)

AI prompt templates for agent-based trading workflows:

- `prompts/system/` - Agent role definitions (strategist, trader, risk, execution, reviewer)
- `prompts/user/` - User-facing entry points (market scan, open/close position, emergency)
- `prompts/templates/` - JSON schemas for structured output (order plan, signal, journal)

### Workflows (workflows/)

YAML orchestration blueprints defining multi-step trading processes:

- `daily_scan.yaml` - Scheduled daily market analysis workflow
- `entry.yaml` - Position entry process with risk checks
- `exit.yaml` - Position exit evaluation workflow
- `emergency_stop.yaml` - Critical override to close all positions immediately

### Backtest Framework (src/wave/)

Wave 是一个轻量级量化回测框架，基于 docs/ch07 设计：

```
src/wave/
├── core/
│   ├── engine.py        # 回测引擎
│   ├── portfolio.py     # 资金管理
│   └── order.py         # 订单管理
├── metrics/
│   └── evaluation.py    # 性能评估指标 (ch07.1)
├── strategies/
│   └── double_ma.py     # 双均线策略示例 (ch07.2-7.3)
└── examples/
    └── double_ma_example.py  # 使用示例
```

主要功能:
- 轻量级回测引擎（无复杂继承）
- 完整评估指标体系（累计收益、年化收益、波动率、最大回撤、夏普比率等）
- 经典策略示例（双均线策略）
- 单标的和组合回测支持
- CSV/Tushare API 数据源

使用方法:
```python
from wave import BacktestEngine, double_ma_strategy

engine = BacktestEngine(initial_cash=100000)
engine.add_data('stock', df)
result = engine.run(double_ma_strategy())
print(result.metrics)
```

运行示例:
```bash
cd src
PYTHONPATH=. python wave/examples/double_ma_example.py
```

### Skills System (.agents/skills/)

External skills imported from Binance's skills-hub:

```json
// From skills-lock.json
- binance/binance-skills-hub → binance SKILL.md (spot, futures, derivatives)
- binance-web3/crypto-market-rank → crypto market rankings
- binance-web3/query-token-audit → token contract auditing
- binance-web3/query-token-info → token metadata queries
```

Skills are referenced by agents during workflow execution via YAML templating syntax (`{{skill_name.method}}`).

## Dependencies

Python 3.9.x required due to dependency compatibility:

```txt
tushare==1.3.7    # Data acquisition API
pandas==2.1.4     # Data manipulation
numpy==1.26.3     # Numerical computing
matplotlib==3.8.2 # Visualization
```

Install:
```bash
pip install -r requirements.txt
```

## Running Notebooks

Use Jupyter or JupyterLab:

```bash
pip install jupyter
jupyter notebook notebook/
jupyter lab notebook/
```

Or use Google Colab / Kaggle / other cloud notebooks.

## Development Workflow

### For Adding New Chapter Content

1. Add markdown to `docs/chXX_Topic/Topic.md` for documentation
2. Add corresponding notebook to `notebook/chXX_Topic/` with code examples
3. Update `docs/_sidebar.md` navigation if needed
4. Include any helper scripts in `code/chXX/` for self-contained examples

### For Modifying Existing Notebooks

1. Open notebook in Jupyter Lab/Desktop
2. Run cells sequentially to verify output
3. Commit both `.ipynb` and any updated `*.png` references in docs

### For Testing Trading Workflows

Note: This is primarily educational; real trading requires careful configuration:

1. Ensure `docker-compose.yml` services are up:
   ```bash
   docker-compose up -d redis postgres
   ```

2. Configure API credentials in `.env` (do not commit):
   ```
   TUSHARE_TOKEN=your_token
   ANTHROPIC_API_KEY=your_key
   BINANCE_API_KEY=your_key
   BINANCE_API_SECRET=your_secret
   ```

3. Execute workflows via appropriate runner scripts (not present in repo - would need custom implementation)

## File Organization Summary

```
trading-os/
├── code/           # Self-contained Python module examples
├── dashboards/     # Visualization dashboards
├── data/           # Local data storage (gitignored)
├── docs/           # Docsify static site
├── logs/           # Runtime logs
├── memory/         # Persistent trading state
│   ├── market/
│   ├── strategy/
│   └── trades/
├── notebook/       # Jupyter notebooks
├── prompts/        # AI prompt templates
├── resources/      # Images and static assets
├── risk/           # Trading constraint configs
└── workflows/      # Workflow orchestration YAMLs
```

## Key Notes

- **Data Source**: Uses Tushare API for Chinese market data; requires token registration at tushare.pro
- **Docsify Sidebar**: Edit `docs/_sidebar.md` when adding/removing chapter entries
- **Git LFS**: Large image files may need Git LFS setup
- **Educational Focus**: Primarily designed for learning; production deployment requires additional safety measures
