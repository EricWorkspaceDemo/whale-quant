"""Portfolio module for position management.

Supports both single-asset and multi-asset portfolio tracking.
"""

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class Position:
    """Represent a position in a single asset.

    Attributes:
        symbol: Trading symbol (e.g., '600519.SH').
        quantity: Number of shares/units held (can be negative for short).
        avg_cost: Average cost per unit.
        current_price: Current market price.
    """

    symbol: str
    quantity: int = 0
    avg_cost: float = 0.0
    current_price: float = 0.0

    @property
    def market_value(self) -> float:
        """Calculate market value of position."""
        return self.quantity * self.current_price

    @property
    def cost_basis(self) -> float:
        """Calculate total cost basis."""
        if self.quantity == 0:
            return 0.0
        return abs(self.quantity) * self.avg_cost

    @property
    def unrealized_pnl(self) -> float:
        """Calculate unrealized profit/loss.

        For long positions: pnl = (current_price - avg_cost) * quantity
        For short positions: pnl = (avg_cost - current_price) * abs(quantity)
        """
        if self.quantity > 0:
            # Long position
            return (self.current_price - self.avg_cost) * self.quantity
        elif self.quantity < 0:
            # Short position
            return (self.avg_cost - self.current_price) * abs(self.quantity)
        return 0.0

    @property
    def unrealized_pnl_pct(self) -> float:
        """Calculate unrealized PnL percentage."""
        if self.cost_basis == 0:
            return 0.0
        return self.unrealized_pnl / self.cost_basis * 100

    def update_price(self, price: float) -> None:
        """Update current market price.

        Args:
            price: New market price.
        """
        self.current_price = price

    def is_empty(self) -> bool:
        """Check if position is flat."""
        return self.quantity == 0


@dataclass
class Portfolio:
    """Manage trading portfolio with multiple positions.

    Supports both single-asset and multi-asset portfolios.
    Tracks cash, positions, and calculates overall portfolio metrics.

    Attributes:
        initial_cash: Starting cash balance.
        cash: Current available cash.
        positions: Dictionary mapping symbols to Position objects.

    Example:
        >>> portfolio = Portfolio(initial_cash=100000)
        >>> portfolio.add_position("600519.SH", quantity=100, price=1500)
        >>> portfolio.get_position("600519.SH").quantity
        100
        >>> portfolio.total_equity
        250000.0  # 100000 cash + 100*1500 stock
    """

    initial_cash: float = 100000.0
    cash: float = field(init=False)
    positions: Dict[str, Position] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Initialize cash from initial_cash after dataclass init."""
        self.cash = self.initial_cash

    def get_position(self, symbol: str) -> Position:
        """Get or create a position for a symbol.

        Args:
            symbol: Trading symbol.

        Returns:
            Position object for the symbol.
        """
        if symbol not in self.positions:
            self.positions[symbol] = Position(symbol=symbol)
        return self.positions[symbol]

    def add_position(
        self,
        symbol: str,
        quantity: int,
        price: float,
    ) -> None:
        """Add to an existing position.

        Updates average cost using weighted average formula.

        Args:
            symbol: Trading symbol.
            quantity: Change in quantity (positive for long addition).
            price: Price per unit.
        """
        pos = self.get_position(symbol)
        old_qty = pos.quantity

        if old_qty > 0:
            # Update average cost for same direction additions
            total_cost = pos.cost_basis + quantity * price
            pos.avg_cost = total_cost / (old_qty + quantity)
        elif old_qty < 0 and quantity > 0:
            # Reducing short position - don't change avg_cost yet
            pass
        else:
            # First position or starting new direction
            pos.avg_cost = price

        pos.quantity += quantity
        pos.current_price = price

    def buy(
        self,
        symbol: str,
        quantity: int,
        price: float,
        commission: float = 0.0,
    ) -> bool:
        """Execute a buy order.

        Args:
            symbol: Trading symbol.
            quantity: Number of shares to buy.
            price: Price per share.
            commission: Transaction commission.

        Returns:
            True if order executed successfully, False if insufficient funds.
        """
        total_cost = quantity * price + commission

        if total_cost > self.cash:
            return False

        self.cash -= total_cost
        self.add_position(symbol, quantity, price)

        return True

    def sell(
        self,
        symbol: str,
        quantity: int,
        price: float,
        commission: float = 0.0,
    ) -> bool:
        """Execute a sell order.

        Args:
            symbol: Trading symbol.
            quantity: Number of shares to sell.
            price: Price per share.
            commission: Transaction commission.

        Returns:
            True if order executed successfully, False if insufficient position.
        """
        pos = self.get_position(symbol)

        if quantity > pos.quantity:
            return False

        proceeds = quantity * price - commission

        self.cash += proceeds
        self.add_position(symbol, -quantity, price)

        return True

    def update_prices(self, prices: Dict[str, float]) -> None:
        """Update current prices for all positions.

        Args:
            prices: Dictionary mapping symbols to current prices.
        """
        for symbol, price in prices.items():
            if symbol in self.positions:
                self.positions[symbol].update_price(price)

    @property
    def total_positions_value(self) -> float:
        """Calculate total value of all positions."""
        return sum(pos.market_value for pos in self.positions.values())

    @property
    def total_equity(self) -> float:
        """Calculate total portfolio equity (cash + positions)."""
        return self.cash + self.total_positions_value

    @property
    def day_change(self) -> float:
        """Calculate absolute day-to-date change.

        Returns difference between current equity and initial equity.
        """
        initial_equity = self.initial_cash
        return self.total_equity - initial_equity

    @property
    def day_change_pct(self) -> float:
        """Calculate percentage day-to-date change."""
        initial_equity = self.initial_cash
        if initial_equity == 0:
            return 0.0
        return self.day_change / initial_equity * 100

    @property
    def num_positions(self) -> int:
        """Count number of non-flat positions."""
        return sum(1 for pos in self.positions.values() if not pos.is_empty())

    def get_total_exposure(self) -> float:
        """Calculate total gross exposure (sum of absolute position values)."""
        return sum(abs(pos.market_value) for pos in self.positions.values())

    def get_leverage(self) -> float:
        """Calculate portfolio leverage (gross exposure / equity)."""
        if self.total_equity == 0:
            return 0.0
        return self.get_total_exposure() / self.total_equity

    def close_position(self, symbol: str, price: float) -> bool:
        """Close all shares of a position at given price.

        Args:
            symbol: Symbol to close.
            price: Close price.

        Returns:
            True if position was closed, False if position didn't exist.
        """
        pos = self.get_position(symbol)
        if pos.is_empty():
            return False

        quantity = pos.quantity
        success = self.sell(symbol, abs(quantity), price)

        # Clear the position if still not empty (shouldn't happen)
        if not pos.is_empty():
            pos.quantity = 0

        return success

    def get_performance_metrics(self) -> Dict:
        """Get comprehensive performance metrics.

        Returns:
            Dictionary with various performance measures.
        """
        metrics = {
            "total_equity": self.total_equity,
            "cash": self.cash,
            "total_positions_value": self.total_positions_value,
            "day_change": self.day_change,
            "day_change_pct": self.day_change_pct,
            "num_positions": self.num_positions,
            "leverage": self.get_leverage(),
            "positions": {},
        }

        for symbol, pos in self.positions.items():
            if not pos.is_empty():
                metrics["positions"][symbol] = {
                    "quantity": pos.quantity,
                    "avg_cost": pos.avg_cost,
                    "current_price": pos.current_price,
                    "market_value": pos.market_value,
                    "unrealized_pnl": pos.unrealized_pnl,
                    "unrealized_pnl_pct": pos.unrealized_pnl_pct,
                }

        return metrics
