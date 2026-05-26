"""Test Portfolio module."""

import pytest
from wave.core.portfolio import Position, Portfolio


class TestPosition:
    """Test Position class."""

    def test_position_creation_empty(self):
        """Test empty position creation."""
        pos = Position(symbol="600519.SH")

        assert pos.symbol == "600519.SH"
        assert pos.quantity == 0
        assert pos.market_value == 0.0
        assert pos.cost_basis == 0.0
        assert pos.is_empty() is True

    def test_position_long(self):
        """Test long position calculation."""
        pos = Position(
            symbol="600519.SH",
            quantity=100,
            avg_cost=1500.0,
            current_price=1600.0,
        )

        assert pos.market_value == 160000.0
        assert pos.cost_basis == 150000.0
        assert pos.unrealized_pnl == 10000.0

    def test_position_short(self):
        """Test short position calculation."""
        pos = Position(
            symbol="BTC-USD",
            quantity=-10,
            avg_cost=50000.0,
            current_price=48000.0,
        )

        assert pos.market_value == -480000.0
        assert pos.cost_basis == 500000.0
        assert pos.unrealized_pnl == 20000.0

    def test_update_price(self):
        """Test price update affects unrealized PnL."""
        pos = Position(
            symbol="600519.SH",
            quantity=100,
            avg_cost=1500.0,
            current_price=1500.0,
        )

        assert pos.unrealized_pnl == 0.0

        pos.update_price(1600.0)

        assert pos.current_price == 1600.0
        assert pos.unrealized_pnl == 10000.0


class TestPortfolio:
    """Test Portfolio class."""

    def test_portfolio_initialization(self):
        """Test portfolio initialization with default cash."""
        portfolio = Portfolio()

        assert portfolio.initial_cash == 100000.0
        assert portfolio.cash == 100000.0
        assert portfolio.total_equity == 100000.0
        assert portfolio.num_positions == 0

    def test_buy_order_success(self):
        """Test successful buy order."""
        portfolio = Portfolio(initial_cash=200000.0)

        result = portfolio.buy("600519.SH", quantity=100, price=1500.0)

        assert result is True
        assert portfolio.cash == 50000.0  # 200000 - 150000
        assert portfolio.positions["600519.SH"].quantity == 100

    def test_buy_insufficient_funds(self):
        """Test buy fails with insufficient funds."""
        portfolio = Portfolio(initial_cash=10000.0)

        result = portfolio.buy("600519.SH", quantity=100, price=1500.0)

        assert result is False
        assert portfolio.cash == 10000.0

    def test_sell_insufficient_position(self):
        """Test sell fails with insufficient position."""
        portfolio = Portfolio(initial_cash=100000.0)
        portfolio.buy("600519.SH", quantity=100, price=1500.0)

        result = portfolio.sell("600519.SH", quantity=200, price=1600.0)

        assert result is False

    def test_multiple_positions(self):
        """Test portfolio with multiple positions."""
        portfolio = Portfolio(initial_cash=300000.0)

        portfolio.buy("600519.SH", quantity=100, price=1500.0)
        portfolio.buy("601398.SH", quantity=1000, price=5.0)

        assert portfolio.num_positions == 2
        assert len(portfolio.positions) == 2

    def test_update_prices(self):
        """Test batch price updates."""
        portfolio = Portfolio(initial_cash=300000.0)
        portfolio.buy("600519.SH", quantity=100, price=1500.0)
        portfolio.buy("601398.SH", quantity=1000, price=5.0)

        portfolio.update_prices({"600519.SH": 1600.0, "601398.SH": 6.0})

        assert portfolio.positions["600519.SH"].current_price == 1600.0
        assert portfolio.positions["601398.SH"].current_price == 6.0

    def test_day_change_calculation(self):
        """Test day change calculation."""
        portfolio = Portfolio(initial_cash=100000.0)

        # No change when flat
        assert portfolio.day_change == 0.0

        # Add position and update price
        portfolio.buy("600519.SH", quantity=100, price=1500.0)
        portfolio.update_prices({"600519.SH": 1600.0})

        # Equity = 50000 + 100*1600 = 210000 (starting from 200k)
        # But we started with 100k, so equity should be positive
