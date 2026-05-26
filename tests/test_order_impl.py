"""Test Order module implementation."""

import pytest
from wave.core.order import Order, OrderType, OrderStatus


class TestOrderProperties:
    """Test Order class properties and helper methods."""

    def test_remaining_quantity_filled(self):
        """Test remaining quantity when fully filled."""
        order = Order(
            order_id="1",
            symbol="600519.SH",
            order_type=OrderType.BUY,
            status=OrderStatus.FILLED,
            quantity=100,
            price=1500.0,
            filled_quantity=100,
        )

        assert order.remaining_quantity == 0

    def test_remaining_quantity_partial(self):
        """Test remaining quantity with partial fill."""
        order = Order(
            order_id="1",
            symbol="600519.SH",
            order_type=OrderType.BUY,
            status=OrderStatus.PARTIALLY_FILLED,
            quantity=100,
            price=1500.0,
            filled_quantity=30,
        )

        assert order.remaining_quantity == 70

    def test_can_modify_true(self):
        """Test can_modify returns True for submit states."""
        order = Order(
            order_id="1",
            symbol="600519.SH",
            order_type=OrderType.BUY,
            status=OrderStatus.SUBMITTED,
            quantity=100,
            price=1500.0,
        )

        assert order.can_modify() is True

    def test_can_modify_false_filled(self):
        """Test can_modify returns False for filled orders."""
        order = Order(
            order_id="1",
            symbol="600519.SH",
            order_type=OrderType.BUY,
            status=OrderStatus.FILLED,
            quantity=100,
            price=1500.0,
        )

        assert order.can_modify() is False

    def test_cancel_success(self):
        """Test successful cancellation."""
        order = Order(
            order_id="1",
            symbol="600519.SH",
            order_type=OrderType.BUY,
            status=OrderStatus.SUBMITTED,
            quantity=100,
            price=1500.0,
        )

        result = order.cancel()
        assert result is True
        assert order.status == OrderStatus.CANCELLED

    def test_cancel_failed(self):
        """Test cancellation fails on already filled order."""
        order = Order(
            order_id="1",
            symbol="600519.SH",
            order_type=OrderType.BUY,
            status=OrderStatus.FILLED,
            quantity=100,
            price=1500.0,
        )

        result = order.cancel()
        assert result is False
        assert order.status == OrderStatus.FILLED

    def test_fill_progress_boundary(self):
        """Test fill progress boundary conditions."""
        order = Order(
            order_id="1",
            symbol="600519.SH",
            order_type=OrderType.BUY,
            status=OrderStatus.SUBMITTED,
            quantity=0,
            price=1500.0,
        )

        # Zero quantity should return 0 or 1 based on status
        if order.status != OrderStatus.FILLED:
            assert order.fill_progress == 0.0


class TestMarketOrder:
    """Test market order behavior (price=0)."""

    def test_market_order_value_is_zero(self):
        """Test that market orders have value of 0 until filled."""
        order = Order(
            order_id="1",
            symbol="600519.SH",
            order_type=OrderType.BUY,
            status=OrderStatus.SUBMITTED,
            quantity=100,
            price=0.0,  # Market order
        )

        assert order.value == 0.0

    def test_limit_order_value(self):
        """Test limit order value calculation."""
        order = Order(
            order_id="1",
            symbol="600519.SH",
            order_type=OrderType.SELL,
            status=OrderStatus.SUBMITTED,
            quantity=200,
            price=1600.0,
        )

        assert order.value == 320000.0


class TestAveragePriceCalculation:
    """Test average filled price calculation."""

    def test_single_fill_price(self):
        """Test average price with single fill."""
        order = Order(
            order_id="1",
            symbol="600519.SH",
            order_type=OrderType.BUY,
            status=OrderStatus.ACCEPTED,
            quantity=100,
            price=0.0,
        )

        order.partial_fill(filled_quantity=100, filled_price=1500.0)

        assert order.filled_price == 1500.0

    def test_multiple_fill_average_price(self):
        """Test weighted average price across multiple fills."""
        order = Order(
            order_id="1",
            symbol="600519.SH",
            order_type=OrderType.BUY,
            status=OrderStatus.ACCEPTED,
            quantity=100,
            price=0.0,
        )

        # First fill: 50 shares at $1500
        order.partial_fill(filled_quantity=50, filled_price=1500.0)
        assert order.filled_price == 1500.0

        # Second fill: 50 shares at $1510
        order.partial_fill(filled_quantity=50, filled_price=1510.0)
        # Average = (50*1500 + 50*1510) / 100 = 1505
        assert order.filled_price == 1505.0

    def test_three_fill_average_price(self):
        """Test average price with three fills."""
        order = Order(
            order_id="1",
            symbol="600519.SH",
            order_type=OrderType.BUY,
            status=OrderStatus.ACCEPTED,
            quantity=100,
            price=0.0,
        )

        order.partial_fill(filled_quantity=30, filled_price=100.0)
        order.partial_fill(filled_quantity=30, filled_price=102.0)
        order.partial_fill(filled_quantity=40, filled_price=101.0)

        # Average = (30*100 + 30*102 + 40*101) / 100 = 101.0
        assert order.filled_price == 101.0
