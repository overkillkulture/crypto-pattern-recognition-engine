"""Trading simulator for paper trading and strategy testing."""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class OrderType(str, Enum):
    """Order types."""

    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"


class OrderSide(str, Enum):
    """Order side (buy/sell)."""

    BUY = "buy"
    SELL = "sell"


class OrderStatus(str, Enum):
    """Order status."""

    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


@dataclass
class Order:
    """Trading order."""

    order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: Optional[float] = None  # None for market orders
    stop_price: Optional[float] = None  # For stop orders
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: float = 0.0
    filled_price: Optional[float] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    filled_at: Optional[datetime] = None
    fees: float = 0.0

    @property
    def is_filled(self) -> bool:
        """Check if order is fully filled."""
        return self.status == OrderStatus.FILLED

    @property
    def is_active(self) -> bool:
        """Check if order is still active."""
        return self.status in (OrderStatus.PENDING, OrderStatus.PARTIALLY_FILLED)

    @property
    def remaining_quantity(self) -> float:
        """Get remaining quantity to fill."""
        return self.quantity - self.filled_quantity


@dataclass
class Position:
    """Trading position."""

    position_id: str
    symbol: str
    side: OrderSide  # LONG (bought) or SHORT (sold)
    quantity: float
    entry_price: float
    entry_time: datetime
    current_price: float
    unrealized_pnl: float = 0.0
    unrealized_pnl_pct: float = 0.0
    fees_paid: float = 0.0

    def update_price(self, current_price: float):
        """Update position with current market price."""
        self.current_price = current_price

        if self.side == OrderSide.BUY:  # Long position
            self.unrealized_pnl = (
                current_price - self.entry_price
            ) * self.quantity - self.fees_paid
            self.unrealized_pnl_pct = (
                (current_price - self.entry_price) / self.entry_price * 100
            )
        else:  # Short position
            self.unrealized_pnl = (
                self.entry_price - current_price
            ) * self.quantity - self.fees_paid
            self.unrealized_pnl_pct = (
                (self.entry_price - current_price) / self.entry_price * 100
            )


class TradingSimulator:
    """
    Paper trading simulator.

    Simulates order execution, position tracking, and P&L calculation
    without using real money.

    Example:
        simulator = TradingSimulator(initial_capital=10000, fee_rate=0.001)

        # Place market order
        order = simulator.market_order("BTC/USDT", OrderSide.BUY, 0.1, current_price=50000)

        # Update with new price
        simulator.update_prices({"BTC/USDT": 51000})

        # Check position
        position = simulator.get_position("BTC/USDT")
        print(f"P&L: ${position.unrealized_pnl:.2f}")
    """

    def __init__(
        self,
        initial_capital: float = 10000.0,
        fee_rate: float = 0.001,  # 0.1% fee
        slippage_pct: float = 0.05,  # 0.05% slippage
        enable_margin: bool = False,
        margin_multiplier: float = 1.0,
    ):
        """
        Initialize trading simulator.

        Args:
            initial_capital: Starting capital in USD
            fee_rate: Trading fee rate (e.g., 0.001 = 0.1%)
            slippage_pct: Price slippage percentage
            enable_margin: Whether to enable margin trading
            margin_multiplier: Margin multiplier (e.g., 2x, 5x, 10x)
        """
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.fee_rate = fee_rate
        self.slippage_pct = slippage_pct
        self.enable_margin = enable_margin
        self.margin_multiplier = margin_multiplier if enable_margin else 1.0

        # Tracking
        self.positions: Dict[str, Position] = {}
        self.open_orders: Dict[str, Order] = {}
        self.order_history: List[Order] = []
        self.closed_positions: List[Position] = []

        # Statistics
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_fees_paid = 0.0
        self.total_realized_pnl = 0.0

    def get_buying_power(self) -> float:
        """Get available buying power (cash * margin multiplier)."""
        return self.cash * self.margin_multiplier

    def get_equity(self) -> float:
        """Get total equity (cash + unrealized P&L)."""
        unrealized_pnl = sum(pos.unrealized_pnl for pos in self.positions.values())
        return self.cash + unrealized_pnl

    def get_total_position_value(self) -> float:
        """Get total value of all positions."""
        return sum(pos.quantity * pos.current_price for pos in self.positions.values())

    def market_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        current_price: float,
    ) -> Optional[Order]:
        """
        Place a market order (executes immediately).

        Args:
            symbol: Trading symbol
            side: BUY or SELL
            quantity: Quantity to trade
            current_price: Current market price

        Returns:
            Order object if successful, None if rejected
        """
        # Apply slippage
        execution_price = current_price * (1 + self.slippage_pct / 100)
        if side == OrderSide.SELL:
            execution_price = current_price * (1 - self.slippage_pct / 100)

        # Calculate fees
        order_value = quantity * execution_price
        fees = order_value * self.fee_rate

        # Check if we have enough capital
        if side == OrderSide.BUY:
            required_capital = order_value + fees
            available = self.get_buying_power()

            if required_capital > available:
                logger.warning(
                    f"Insufficient capital: need ${required_capital:.2f}, have ${available:.2f}"
                )
                return None

        # Check if we have position to sell
        if side == OrderSide.SELL:
            if symbol not in self.positions:
                logger.warning(f"No position in {symbol} to sell")
                return None
            if self.positions[symbol].quantity < quantity:
                logger.warning(
                    f"Insufficient quantity: have {self.positions[symbol].quantity}, need {quantity}"
                )
                return None

        # Create and fill order
        order = Order(
            order_id=str(uuid.uuid4()),
            symbol=symbol,
            side=side,
            order_type=OrderType.MARKET,
            quantity=quantity,
            status=OrderStatus.FILLED,
            filled_quantity=quantity,
            filled_price=execution_price,
            filled_at=datetime.utcnow(),
            fees=fees,
        )

        # Update positions and cash
        if side == OrderSide.BUY:
            self._open_position(order)
        else:
            self._close_position(order)

        # Update tracking
        self.order_history.append(order)
        self.total_trades += 1
        self.total_fees_paid += fees

        logger.info(
            f"{side.value.upper()} {quantity} {symbol} @ ${execution_price:.2f} (fees: ${fees:.2f})"
        )

        return order

    def limit_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        limit_price: float,
    ) -> Order:
        """
        Place a limit order (executes when price reaches limit).

        Args:
            symbol: Trading symbol
            side: BUY or SELL
            quantity: Quantity to trade
            limit_price: Limit price

        Returns:
            Order object (pending until filled)
        """
        order = Order(
            order_id=str(uuid.uuid4()),
            symbol=symbol,
            side=side,
            order_type=OrderType.LIMIT,
            quantity=quantity,
            price=limit_price,
            status=OrderStatus.PENDING,
        )

        self.open_orders[order.order_id] = order
        logger.info(
            f"Limit order placed: {side.value.upper()} {quantity} {symbol} @ ${limit_price:.2f}"
        )

        return order

    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an open order.

        Args:
            order_id: Order ID to cancel

        Returns:
            True if cancelled, False if not found
        """
        if order_id in self.open_orders:
            order = self.open_orders[order_id]
            order.status = OrderStatus.CANCELLED
            del self.open_orders[order_id]
            self.order_history.append(order)
            logger.info(f"Order {order_id} cancelled")
            return True
        return False

    def update_prices(self, prices: Dict[str, float]):
        """
        Update current prices for all symbols.

        This will:
        - Update unrealized P&L for open positions
        - Check and fill limit orders if price reached

        Args:
            prices: Dictionary of symbol -> current price
        """
        # Update positions
        for symbol, position in self.positions.items():
            if symbol in prices:
                position.update_price(prices[symbol])

        # Check limit orders
        filled_orders = []
        for order_id, order in list(self.open_orders.items()):
            if order.symbol not in prices:
                continue

            current_price = prices[order.symbol]

            # Check if limit order should fill
            should_fill = False
            if order.order_type == OrderType.LIMIT:
                if order.side == OrderSide.BUY and current_price <= order.price:
                    should_fill = True
                elif order.side == OrderSide.SELL and current_price >= order.price:
                    should_fill = True

            if should_fill:
                # Fill the order
                execution_price = order.price
                fees = order.quantity * execution_price * self.fee_rate

                order.status = OrderStatus.FILLED
                order.filled_quantity = order.quantity
                order.filled_price = execution_price
                order.filled_at = datetime.utcnow()
                order.fees = fees

                # Update positions
                if order.side == OrderSide.BUY:
                    self._open_position(order)
                else:
                    self._close_position(order)

                filled_orders.append(order_id)
                self.order_history.append(order)
                self.total_trades += 1
                self.total_fees_paid += fees

                logger.info(
                    f"Limit order filled: {order.side.value.upper()} {order.quantity} {order.symbol} @ ${execution_price:.2f}"
                )

        # Remove filled orders
        for order_id in filled_orders:
            del self.open_orders[order_id]

    def get_position(self, symbol: str) -> Optional[Position]:
        """Get current position for a symbol."""
        return self.positions.get(symbol)

    def get_all_positions(self) -> List[Position]:
        """Get all open positions."""
        return list(self.positions.values())

    def get_open_orders(self) -> List[Order]:
        """Get all open orders."""
        return list(self.open_orders.values())

    def _open_position(self, order: Order):
        """Open a new position or add to existing position."""
        symbol = order.symbol

        if symbol in self.positions:
            # Add to existing position (average entry price)
            existing = self.positions[symbol]
            total_quantity = existing.quantity + order.filled_quantity
            avg_entry_price = (
                (existing.entry_price * existing.quantity)
                + (order.filled_price * order.filled_quantity)
            ) / total_quantity

            existing.quantity = total_quantity
            existing.entry_price = avg_entry_price
            existing.fees_paid += order.fees
            existing.update_price(order.filled_price)

        else:
            # Create new position
            self.positions[symbol] = Position(
                position_id=str(uuid.uuid4()),
                symbol=symbol,
                side=order.side,
                quantity=order.filled_quantity,
                entry_price=order.filled_price,
                entry_time=order.filled_at,
                current_price=order.filled_price,
                fees_paid=order.fees,
            )

        # Deduct cash
        cost = order.filled_quantity * order.filled_price + order.fees
        self.cash -= cost

    def _close_position(self, order: Order):
        """Close or reduce a position."""
        symbol = order.symbol

        if symbol not in self.positions:
            logger.error(f"Cannot close position: {symbol} not found")
            return

        position = self.positions[symbol]

        # Calculate realized P&L
        if position.side == OrderSide.BUY:  # Closing long
            realized_pnl = (
                order.filled_price - position.entry_price
            ) * order.filled_quantity
        else:  # Closing short
            realized_pnl = (
                position.entry_price - order.filled_price
            ) * order.filled_quantity

        realized_pnl -= order.fees

        # Update statistics
        self.total_realized_pnl += realized_pnl
        if realized_pnl > 0:
            self.winning_trades += 1
        else:
            self.losing_trades += 1

        # Add cash from sale
        proceeds = order.filled_quantity * order.filled_price - order.fees
        self.cash += proceeds

        # Reduce or close position
        if order.filled_quantity >= position.quantity:
            # Close entire position
            self.closed_positions.append(position)
            del self.positions[symbol]
            logger.info(f"Position closed: {symbol}, realized P&L: ${realized_pnl:.2f}")
        else:
            # Partial close
            position.quantity -= order.filled_quantity
            position.update_price(order.filled_price)
            logger.info(
                f"Position reduced: {symbol}, realized P&L: ${realized_pnl:.2f}"
            )

    def close_all_positions(self, current_prices: Dict[str, float]):
        """
        Close all open positions at current market prices.

        Args:
            current_prices: Dictionary of symbol -> current price
        """
        for symbol in list(self.positions.keys()):
            if symbol in current_prices:
                position = self.positions[symbol]
                self.market_order(
                    symbol, OrderSide.SELL, position.quantity, current_prices[symbol]
                )

    def get_statistics(self) -> Dict[str, any]:
        """Get trading statistics."""
        equity = self.get_equity()
        return_pct = ((equity - self.initial_capital) / self.initial_capital) * 100

        win_rate = 0.0
        if self.total_trades > 0:
            win_rate = (self.winning_trades / self.total_trades) * 100

        return {
            "initial_capital": self.initial_capital,
            "current_cash": self.cash,
            "equity": equity,
            "unrealized_pnl": equity - self.cash,
            "realized_pnl": self.total_realized_pnl,
            "total_return_pct": return_pct,
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "win_rate": win_rate,
            "total_fees": self.total_fees_paid,
            "open_positions": len(self.positions),
            "open_orders": len(self.open_orders),
        }

    def reset(self):
        """Reset simulator to initial state."""
        self.cash = self.initial_capital
        self.positions.clear()
        self.open_orders.clear()
        self.order_history.clear()
        self.closed_positions.clear()

        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_fees_paid = 0.0
        self.total_realized_pnl = 0.0

        logger.info("Simulator reset to initial state")
