# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Context

Trading OS is a multi-agent trading system that coordinates five specialized AI agents to analyze markets, develop strategies, execute trades, and manage risks. The system uses Claude AI with structured prompts and workflows to orchestrate complex trading decisions with built-in safety constraints.

## System Architecture

### Core Agent Loop

The system follows a structured approval chain:

```
Strategist (market analysis) 
  ↓
Trader (entry/exit signals) 
  ↓
Risk (constraint checking)
  ↓
Execution (order placement)
  ↓
Reviewer (performance analysis)
```

Each agent:
- Receives a system prompt from `prompts/system/*.md` defining its role and decision framework
- Takes input from previous agents or workflow context
- Returns structured output (markdown or JSON)
- Must respect hard constraints from the Risk agent before execution

### Prompt Architecture

**System Prompts** (`prompts/system/`): Define agent roles and decision frameworks
- Each agent has one system prompt loaded at initialization
- Prompts define output format expectations
- Format varies: Strategist uses markdown, Trader/Risk/Execution use structured fields

**User Prompts** (`prompts/user/`): Entry points for workflows with template variables
- `market_scan.md` - Triggers daily analysis workflow
- `open_position.md` - User request to enter a trade
- `close_position.md` - Evaluate existing position for exit
- `emergency.md` - Critical override to close all positions immediately

### Workflow System

Workflows (`workflows/*.yaml`) are orchestration blueprints that:
- Chain agents together with data flow (via `depends_on`)
- Include conditional gates (approval steps, risk checks)
- Define notifications (Slack, alerts)
- Can be scheduled (daily_scan) or triggered by user/signal

Example flow in `workflows/entry.yaml`:
1. Strategist validates opportunity
2. Trader makes decision → generates trade plan
3. Risk assesses constraints → approves/rejects
4. (If high risk) → approval_gate requires human sign-off
5. Execution places order
6. Trade stored in memory for later review

### Skills System

Skills (`skills/`) are reusable capability modules:

**Binance Skills** (`skills/binance/`)
- `futures.ts` - Market data fetching
- `leverage.ts` - Margin management
- `positions.ts` - Position lifecycle
- `account.ts` - Balance/account info

**Market Skills** (`skills/market/`)
- `funding.ts` - Funding rate analysis (identifies leverage extremes)
- `whale.ts` - Liquidation levels and accumulation detection
- `sentiment.ts` - Market regime detection

Skills are stateless utilities—agents call them to gather data before making decisions. Each skill returns structured data (arrays/objects).

### Memory System

Persistent storage organized by trading domain:

- `memory/market/` - Current market conditions, historical patterns
- `memory/strategy/` - Strategy decisions and their rationale
- `memory/trades/` - Executed trades, P&L, journals

Workflow steps can `store_memory` to persist decisions for later review or cross-session context.

### Risk Management (Critical Safety Layer)

Risk decisions are **blocking**—agents upstream cannot override them.

**Configuration** (`risk/`)
- `config.yaml` - Hard limits: max positions (5), max position size ($10k), max leverage (10), risk per trade (2%)
- `blacklist.json` - Forbidden symbols (new tokens, meme coins)
- `limits.json` - Per-symbol overrides (BTC max $5k with 3x leverage; ALTCOINS max $1k with 2x)

**Enforcement Points**
- Risk agent must approve all trades before Execution
- Position size and leverage checked against `limits.json`
- Circuit breakers: halt trading if daily loss exceeds threshold
- Emergency stop (`workflows/emergency_stop.yaml`) bypasses all gates and force-closes positions in 30s

**Adding New Limits**
1. Edit `risk/config.yaml` (global rules)
2. Or `risk/limits.json` (per-symbol overrides)
3. Risk agent checks both files; explicit symbol limits override defaults

## Development Workflow

### Setup

```bash
# Install dependencies
npm install

# Copy environment template and fill in API keys
cp .env.example .env  # Or create new with ANTHROPIC_API_KEY, BINANCE_API_KEY, BINANCE_API_SECRET

# Start infrastructure (Redis, PostgreSQL)
docker-compose up -d

# Verify services
docker-compose ps
```

### Common Commands

```bash
# Development server (watches for changes, runs agents)
npm run dev

# Run all tests
npm test

# Run tests for a single agent or skill
npm test -- agents/trader
npm test -- skills/market/funding

# Linting
npm run lint

# Linting with auto-fix
npm run lint --fix

# Build for production
npm run build

# Start production (requires build)
npm start

# View logs from a specific agent
npm run logs -- strategist

# Emergency: stop all trading immediately
npm run emergency-stop

# Clean up (stop Docker, clear logs)
npm run clean
```

### Adding a New Agent

1. Create `agents/myagent/agent.ts` with class extending base Agent
2. Add system prompt at `prompts/system/myagent.md`
3. Define input/output interface
4. Add to workflow YAML (reference as `agent: myagent`)
5. Test with `npm test -- agents/myagent`

### Adding a New Skill

1. Create `skills/domain/capability.ts` as stateless utility class
2. Export methods that return structured data (arrays/objects)
3. Agents call skill methods during processing
4. Test independently; skills must not depend on agent state

### Adding a Workflow

1. Create `workflows/myworkflow.yaml`
2. Define steps with `agent:` references and `depends_on:` chains
3. Use `{{variable}}` syntax for templating
4. Include `notifications:` for important events
5. Deploy by referencing in agent initialization or scheduling

## Code Patterns

### TypeScript & Async
- Use `async/await` throughout; no callback chains
- Import Anthropic client: `import Anthropic from "@anthropic-ai/sdk"`
- All API calls must have error handling (try/catch or .catch())

### Agent Implementation
- Accept structured input object (or workflow context)
- Call Claude API with system prompt + user message
- Parse response into expected output format
- Return JSON or markdown as defined by system prompt

### Skill Implementation
- Stateless (no side effects, no stored state)
- Accept parameters, return structured data
- Mock in tests with hardcoded responses

### Workflow Variables
- Input params use `{{ param }}` syntax
- Agent outputs referenced as `{{ agent_name.output }}`
- Conditionals evaluate field values: `{{ risk_assessment.risk_level >= 'HIGH' }}`

## Testing

- **Unit tests**: Individual agent/skill behavior with mocked APIs
- **Integration tests**: Full workflows with mock Binance responses
- Mock responses in `tests/fixtures/` directory
- All external API calls must be mocked (no live trading in tests)

## Safety & Guardrails

### Before Merging Code
- All tests pass (`npm test`)
- No hardcoded API keys (use .env)
- Risk agent changes reviewed (changes to approval logic)
- Emergency stop tested in staging

### Blacklist & Symbol Restrictions
- Edit `risk/blacklist.json` to forbid symbols
- Traders cannot override—Risk agent checks on every trade
- Emergency override only via `workflows/emergency_stop.yaml`

### Observability
- All agent decisions logged with reasoning
- Workflow execution traced in `logs/`
- Memory stores decisions for audit trail
- P&L tracked per trade in reviewer journal
