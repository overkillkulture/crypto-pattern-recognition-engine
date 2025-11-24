"""Backtesting engine for strategy validation."""

from typing import List, Dict, Any, Optional
from datetime import datetime
import numpy as np
from loguru import logger

from src.core.types import OHLCV, PatternResult, SignalType
from src.backtest.strategy import BaseStrategy
from src.backtest.metrics import BacktestMetrics


class Trade:
    """Represents a single trade in the backtest."""

    def __init__(
        self,
        entry_time: datetime,
        entry_price: float,
        position_size: float,
        direction: str,  # 'long' or 'short'
        pattern: Optional[PatternResult] = None,
    ):
        self.entry_time = entry_time
        self.entry_price = entry_price
        self.position_size = position_size
        self.direction = direction
        self.pattern = pattern

        self.exit_time: Optional[datetime] = None
        self.exit_price: Optional[float] = None
        self.pnl: float = 0.0
        self.pnl_pct: float = 0.0
        self.fees: float = 0.0

    def close(self, exit_time: datetime, exit_price: float, fee_rate: float = 0.001):
        """Close the trade."""
        self.exit_time = exit_time
        self.exit_price = exit_price

        # Calculate P&L
        if self.direction == 'long':
            self.pnl_pct = (exit_price - self.entry_price) / self.entry_price
        else:  # short
            self.pnl_pct = (self.entry_price - exit_price) / self.entry_price

        # Account for fees (entry + exit)
        self.fees = self.position_size * fee_rate * 2
        self.pnl = (self.position_size * self.pnl_pct) - self.fees

    def is_open(self) -> bool:
        """Check if trade is still open."""
        return self.exit_time is None


class BacktestEngine:
    """
    Backtesting engine for pattern-based strategies.

    Simulates trading based on pattern detection signals and calculates
    performance metrics.
    """

    def __init__(
        self,
        initial_capital: float = 10000.0,
        position_size_pct: float = 0.10,  # 10% of capital per trade
        fee_rate: float = 0.001,  # 0.1% fees
        slippage: float = 0.0005,  # 0.05% slippage
    ):
        """
        Initialize backtest engine.

        Args:
            initial_capital: Starting capital
            position_size_pct: Percentage of capital to use per trade
            fee_rate: Trading fee rate
            slippage: Slippage rate
        """
        self.initial_capital = initial_capital
        self.position_size_pct = position_size_pct
        self.fee_rate = fee_rate
        self.slippage = slippage

        self.capital = initial_capital
        self.trades: List[Trade] = []
        self.equity_curve: List[float] = [initial_capital]
        self.timestamps: List[datetime] = []

    async def run(
        self,
        strategy: BaseStrategy,
        data: OHLCV,
        patterns: List[PatternResult],
    ) -> Dict[str, Any]:
        """
        Run backtest on historical data.

        Args:
            strategy: Trading strategy to test
            data: Historical OHLCV data
            patterns: Detected patterns for each candle

        Returns:
            Backtest results including trades and metrics
        """
        logger.info(f"Starting backtest: {len(data)} candles, {len(patterns)} patterns")

        # Reset state
        self.capital = self.initial_capital
        self.trades = []
        self.equity_curve = [self.initial_capital]
        self.timestamps = []

        open_trade: Optional[Trade] = None

        # Iterate through data
        for i in range(len(data.close)):
            current_time = datetime.fromtimestamp(data.timestamps[i])
            current_price = data.close[i]

            # Get patterns for this candle
            candle_patterns = [
                p for p in patterns
                if abs(p.timestamp.timestamp() - data.timestamps[i]) < 60
            ]

            # Check if we should close open trade
            if open_trade:
                should_close, reason = strategy.should_exit(
                    open_trade,
                    current_time,
                    current_price,
                    data,
                    i,
                )

                if should_close:
                    exit_price = current_price * (1 + self.slippage if open_trade.direction == 'long' else 1 - self.slippage)
                    open_trade.close(current_time, exit_price, self.fee_rate)

                    # Update capital
                    self.capital += open_trade.pnl

                    logger.debug(f"Closed trade: {reason}, P&L: {open_trade.pnl:.2f}")
                    self.trades.append(open_trade)
                    open_trade = None

            # Check if we should enter new trade (only if no open position)
            if not open_trade and candle_patterns:
                should_enter, direction = strategy.should_enter(
                    candle_patterns,
                    current_time,
                    current_price,
                    data,
                    i,
                )

                if should_enter:
                    position_size = self.capital * self.position_size_pct
                    entry_price = current_price * (1 + self.slippage if direction == 'long' else 1 - self.slippage)

                    open_trade = Trade(
                        entry_time=current_time,
                        entry_price=entry_price,
                        position_size=position_size,
                        direction=direction,
                        pattern=candle_patterns[0] if candle_patterns else None,
                    )

                    logger.debug(f"Opened {direction} trade at {entry_price:.2f}")

            # Track equity
            current_equity = self.capital
            if open_trade:
                # Mark-to-market
                if open_trade.direction == 'long':
                    unrealized_pnl = open_trade.position_size * (current_price - open_trade.entry_price) / open_trade.entry_price
                else:
                    unrealized_pnl = open_trade.position_size * (open_trade.entry_price - current_price) / open_trade.entry_price

                current_equity += unrealized_pnl

            self.equity_curve.append(current_equity)
            self.timestamps.append(current_time)

        # Close any remaining open trade
        if open_trade:
            final_price = data.close[-1]
            open_trade.close(datetime.fromtimestamp(data.timestamps[-1]), final_price, self.fee_rate)
            self.capital += open_trade.pnl
            self.trades.append(open_trade)

        # Calculate metrics
        metrics = BacktestMetrics.calculate(self)

        logger.info(f"Backtest complete: {len(self.trades)} trades, "
                   f"Final capital: ${self.capital:.2f}")

        return {
            'trades': self.trades,
            'metrics': metrics,
            'equity_curve': np.array(self.equity_curve),
            'timestamps': self.timestamps,
            'initial_capital': self.initial_capital,
            'final_capital': self.capital,
        }
