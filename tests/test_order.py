"""Tests for Order module."""

import pytest
from wave.core.order import Order, OrderType, OrderStatus


class TestOrder:
    """Test Order class."""

    def test_order_creation(self):
        """Test order creation with all parameters."""
        order = Order(
            order_id="12345",
            symbol="600519.SH",
            order_type=OrderType.BUY,
            status=OrderStatus.SUBMITTED,
            quantity=100,
            price=1500.0,
        )

        assert order.order_id == "12345"
        assert order.symbol == "600519.SH"
        assert order.order_type == OrderType.BUY
        assert order.status == OrderStatus.SUBMITTED
        assert order.quantity == 100
        assert order.price == 1500.0

    def test_order_value_calculation(self):
        """Test order value calculation (quantity * price)."""
        order = Order(
            order_id="12345",
            symbol="600519.SH",
            order_type=OrderType.BUY,
            status=OrderStatus.SUBMITTED,
            quantity=100,
            price=1500.0,
        )

        assert order.value == 150000.0

    def test_order_status_transition(self):
        """Test valid order status transitions."""
        order = Order(
            order_id="12345",
            symbol="600519.SH",
            order_type=OrderType.BUY,
            status=OrderStatus.SUBMITTED,
            quantity=100,
            price=1500.0,
        )

        # Submitted -> Accepted
        order.accept()
        assert order.status == OrderStatus.ACCEPTED

        # Accepted -> PartiallyFilled
        order.partial_fill(filled_quantity=50, filled_price=1500.5)
        assert order.status == OrderStatus.PARTIALLY_FILLED

        # PartiallyFilled -> Filled
        order.partial_fill(filled_quantity=50, filled_price=1501.0)
        assert order.status == OrderStatus.FILLED

    def test_order_cancellation(self):
        """Test order cancellation."""
        order = Order(
            order_id="12345",
            symbol="600519.SH",
            order_type=OrderType.BUY,
            status=OrderStatus.SUBMITTED,
            quantity=100,
            price=1500.0,
        )

        order.cancel()
        assert order.status == OrderStatus.CANCELLED

    def test_order_rejection(self):
        """Test order rejection."""
        order = Order(
            order_id="12345",
            symbol="600519.SH",
            order_type=OrderType.BUY,
            status=OrderStatus.SUBMITTED,
            quantity=100,
            price=1500.0,
        )

        order.reject("Invalid price")
        assert order.status == OrderStatus.REJECTED
        assert order.rejection_reason == "Invalid price"

    def test_fill_progress(self):
        """Test fill progress calculation."""
        order = Order(
            order_id="12345",
            symbol="600519.SH",
            order_type=OrderType.BUY,
            status=OrderStatus.SUBMITTED,
            quantity=100,
            price=1500.0,
        )

        assert order.fill_progress == 0.0

        order.partial_fill(filled_quantity=30, filled_price=1500.0)
        assert order.fill_progress == 0.3

        order.partial_fill(filled_quantity=70, filled_price=1501.0)
        assert order.fill_progress == 1.0

    @pytest.mark.parametrize(
        "order_type, expected_str",
        [
            (OrderType.BUY, "BUY"),
            (OrderType.SELL, "SELL"),
        ],
    )
    def test_order_type_str_representation(self, order_type, expected_str):
        """Test order type string representation."""
        assert str(order_type) == expected_str


class TestOrderType:
    """Test OrderType enum."""

    def test_buy_type(self):
        """Test BUY order type."""
        assert OrderType.BUY.name == "BUY"

    def test_sell_type(self):
        """Test SELL order type."""
        assert OrderType.SELL.name == "SELL"


class TestOrderStatus:
    """Test OrderStatus enum."""

    def test_submitted_status(self):
        """Test SUBMITTED status."""
        assert OrderStatus.SUBMITTED.name == "SUBMITTED"

    def test_accepted_status(self):
        """Test ACCEPTED status."""
        assert OrderStatus.ACCEPTED.name == "ACCEPTED"

    def test_filled_status(self):
        """Test FILLED status."""
        assert OrderStatus.FILLED.name == "FILLED"

    def test_partially_filled_status(self):
        """Test PARTIALLY_FILLED status."""
        assert OrderStatus.PARTIALLY_FILLED.name == "PARTIALLY_FILLED"

    def test_cancelled_status(self):
        """Test CANCELLED status."""
        assert OrderStatus.CANCELLED.name == "CANCELLED"

    def test_rejected_status(self):
        """Test REJECTED status."""
        assert OrderStatus.REJECTED.name == "REJECTED"
