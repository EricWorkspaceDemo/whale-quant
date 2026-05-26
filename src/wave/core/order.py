"""Order module for trade management."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class OrderType(Enum):
    """Order type enumeration.

    Attributes:
        BUY: Buy order to purchase assets.
        SELL: Sell order to sell assets.
    """

    BUY = "BUY"
    SELL = "SELL"

    def __str__(self) -> str:
        return self.value


class OrderStatus(Enum):
    """Order status enumeration.

    Attributes:
        SUBMITTED: Order submitted but not yet accepted.
        ACCEPTED: Order accepted by broker/system.
        PARTIALLY_FILLED: Partial fill completed.
        FILLED: Order completely filled.
        CANCELLED: Order cancelled by user.
        REJECTED: Order rejected by broker/system.
    """

    SUBMITTED = "SUBMITTED"
    ACCEPTED = "ACCEPTED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"

    def __str__(self) -> str:
        return self.value


@dataclass
class Order:
    """Represent a trading order.

    This class models a single order in the backtesting system,
    tracking its lifecycle from submission to completion.

    Attributes:
        order_id: Unique identifier for the order (e.g., UUID or auto-generated).
        symbol: Trading symbol (e.g., '600519.SH' for stock, 'BTC-USD' for crypto).
        order_type: Type of order - BUY to acquire or SELL to dispose of assets.
        status: Current state of the order in its lifecycle.
        quantity: Number of shares/contracts/unit to trade (must be > 0).
        price: Limit price (0 for market orders, > 0 for limit orders).
        filled_quantity: Cumulative quantity filled (starts at 0, updated on fills).
        filled_price: Average price of filled portion (updated on fills).
        rejection_reason: Human-readable reason if order was rejected (None otherwise).

    Example:
        >>> order = Order(
        ...     order_id="ord_001",
        ...     symbol="600519.SH",
        ...     order_type=OrderType.BUY,
        ...     status=OrderStatus.SUBMITTED,
        ...     quantity=100,
        ...     price=1500.0
        ... )
        >>> order.value
        150000.0
        >>> order.fill_progress
        0.0
    """

    order_id: str
    symbol: str
    order_type: OrderType
    status: OrderStatus
    quantity: int
    price: float = 0.0
    filled_quantity: int = 0
    filled_price: float = 0.0
    rejection_reason: Optional[str] = None

    @property
    def value(self) -> float:
        """Calculate total order value (quantity * price).

        For market orders (price=0), returns 0.0 as the actual fill price
        is only known after execution.

        Returns:
            Total value in base currency, or 0.0 for market orders.
        """
        if self.price > 0:
            return self.quantity * self.price
        return 0.0

    @property
    def fill_progress(self) -> float:
        """Calculate fill progress as ratio of filled to total quantity.

        Returns:
            Float between 0.0 and 1.0 indicating completion percentage.
            Returns 1.0 if fully filled, 0.0 if nothing filled.
        """
        if self.quantity <= 0:
            return 1.0 if self.status == OrderStatus.FILLED else 0.0
        return self.filled_quantity / self.quantity

    @property
    def remaining_quantity(self) -> int:
        """Get remaining unfilled quantity.

        Returns:
            Number of units still to be filled.
        """
        return max(0, self.quantity - self.filled_quantity)

    def is_complete(self) -> bool:
        """Check if order has reached terminal state.

        Terminal states are: FILLED (completed), CANCELLED, or REJECTED.

        Returns:
            True if order will not change further, False otherwise.
        """
        return self.status in [
            OrderStatus.FILLED,
            OrderStatus.CANCELLED,
            OrderStatus.REJECTED,
        ]

    def can_modify(self) -> bool:
        """Check if order can still be modified/cancelled.

        Only orders in SUBMITTED or ACCEPTED state can be modified.

        Returns:
            True if order can be modified, False otherwise.
        """
        return self.status in [OrderStatus.SUBMITTED, OrderStatus.ACCEPTED]

    def accept(self) -> None:
        """Accept the order for processing.

        Transitions order from SUBMITTED to ACCEPTED state.
        No-op if already in terminal state.
        """
        if self.status == OrderStatus.SUBMITTED:
            self.status = OrderStatus.ACCEPTED

    def partial_fill(
        self,
        filled_quantity: int,
        filled_price: float,
    ) -> None:
        """Record a partial fill event.

        Updates filled_quantity and recalculates average filled_price.
        If fill completes the order, status transitions to FILLED.

        Args:
            filled_quantity: Number of units filled in this event.
            filled_price: Price per unit for this fill event.

        Raises:
            ValueError: If filled_quantity exceeds remaining quantity.
        """
        if filled_quantity <= 0:
            return

        remaining = self.remaining_quantity
        actual_fill = min(filled_quantity, remaining)

        old_filled_qty = self.filled_quantity
        self.filled_quantity += actual_fill

        # Calculate new average filled price
        if self.filled_quantity > 0:
            total_cost = (
                self.filled_price * old_filled_qty +
                filled_price * actual_fill
            )
            self.filled_price = total_cost / self.filled_quantity

        if self.filled_quantity >= self.quantity:
            self.status = OrderStatus.FILLED
        elif self.status not in [OrderStatus.FILLED]:
            self.status = OrderStatus.PARTIALLY_FILLED

    def cancel(self) -> bool:
        """Cancel the order if possible.

        Can only cancel orders in SUBMITTED or ACCEPTED state.

        Returns:
            True if cancellation succeeded, False if order cannot be cancelled.
        """
        if self.can_modify():
            self.status = OrderStatus.CANCELLED
            return True
        return False

    def reject(self, reason: str) -> None:
        """Reject the order with a reason.

        Args:
            reason: Human-readable explanation for rejection.
        """
        self.status = OrderStatus.REJECTED
        self.rejection_reason = reason
