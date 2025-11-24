"""Base strategy class for backtesting."""

from abc import ABC, abstractmethod
from typing import List, Tuple
from datetime import datetime

from src.core.types import OHLCV, PatternResult, SignalType
from src.backtest.engine import Trade


class BaseStrategy(ABC):
    """
    Base class for trading strategies.

    Extend this class to create custom trading strategies based on patterns.
    """

    def __init__(self, name: str = "Base Strategy"):
        """Initialize strategy."""
        self.name = name

    @abstractmethod
    def should_enter(
        self,
        patterns: List[PatternResult],
        current_time: datetime,
        current_price: float,
        data: OHLCV,
        index: int,
    ) -> Tuple[bool, str]:
        """
        Determine if strategy should enter a trade.

        Args:
            patterns: List of patterns detected at current candle
            current_time: Current timestamp
            current_price: Current price
            data: Full OHLCV data
            index: Current index in data

        Returns:
            Tuple of (should_enter, direction) where direction is 'long' or 'short'
        """
        pass

    @abstractmethod
    def should_exit(
        self,
        trade: Trade,
        current_time: datetime,
        current_price: float,
        data: OHLCV,
        index: int,
    ) -> Tuple[bool, str]:
        """
        Determine if strategy should exit current trade.

        Args:
            trade: Current open trade
            current_time: Current timestamp
            current_price: Current price
            data: Full OHLCV data
            index: Current index in data

        Returns:
            Tuple of (should_exit, reason)
        """
        pass


class SimplePatternStrategy(BaseStrategy):
    """
    Simple strategy that trades on pattern signals.

    - Enters long on BUY/STRONG_BUY signals
    - Enters short on SELL/STRONG_SELL signals
    - Exits on opposite signal or stop loss
    """

    def __init__(
        self,
        min_confidence: float = 0.75,
        stop_loss_pct: float = 0.02,  # 2% stop loss
        take_profit_pct: float = 0.05,  # 5% take profit
        max_hold_candles: int = 100,
    ):
        """
        Initialize simple pattern strategy.

        Args:
            min_confidence: Minimum pattern confidence to trade
            stop_loss_pct: Stop loss percentage
            take_profit_pct: Take profit percentage
            max_hold_candles: Maximum candles to hold position
        """
        super().__init__("Simple Pattern Strategy")
        self.min_confidence = min_confidence
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.max_hold_candles = max_hold_candles

    def should_enter(
        self,
        patterns: List[PatternResult],
        current_time: datetime,
        current_price: float,
        data: OHLCV,
        index: int,
    ) -> Tuple[bool, str]:
        """Enter on strong pattern signals."""
        # Filter high-confidence patterns
        strong_patterns = [p for p in patterns if p.confidence >= self.min_confidence]

        if not strong_patterns:
            return False, ''

        # Count buy vs sell signals
        buy_signals = sum(
            1 for p in strong_patterns
            if p.signal in [SignalType.BUY, SignalType.STRONG_BUY]
        )

        sell_signals = sum(
            1 for p in strong_patterns
            if p.signal in [SignalType.SELL, SignalType.STRONG_SELL]
        )

        # Enter long if more buy signals
        if buy_signals > sell_signals:
            return True, 'long'

        # Enter short if more sell signals
        elif sell_signals > buy_signals:
            return True, 'short'

        return False, ''

    def should_exit(
        self,
        trade: Trade,
        current_time: datetime,
        current_price: float,
        data: OHLCV,
        index: int,
    ) -> Tuple[bool, str]:
        """Exit on stop loss, take profit, or time limit."""
        # Calculate P&L percentage
        if trade.direction == 'long':
            pnl_pct = (current_price - trade.entry_price) / trade.entry_price
        else:  # short
            pnl_pct = (trade.entry_price - current_price) / trade.entry_price

        # Stop loss
        if pnl_pct <= -self.stop_loss_pct:
            return True, 'stop_loss'

        # Take profit
        if pnl_pct >= self.take_profit_pct:
            return True, 'take_profit'

        # Time-based exit (prevent holding too long)
        if trade.entry_time and current_time:
            candles_held = index  # Simplified - actual implementation would track entry index
            if candles_held > self.max_hold_candles:
                return True, 'time_limit'

        return False, ''


class TrendFollowingStrategy(BaseStrategy):
    """
    Trend-following strategy using moving averages and pattern confirmation.
    """

    def __init__(
        self,
        fast_ma: int = 20,
        slow_ma: int = 50,
        min_confidence: float = 0.70,
        stop_loss_pct: float = 0.03,
    ):
        """Initialize trend following strategy."""
        super().__init__("Trend Following Strategy")
        self.fast_ma = fast_ma
        self.slow_ma = slow_ma
        self.min_confidence = min_confidence
        self.stop_loss_pct = stop_loss_pct

    def should_enter(
        self,
        patterns: List[PatternResult],
        current_time: datetime,
        current_price: float,
        data: OHLCV,
        index: int,
    ) -> Tuple[bool, str]:
        """Enter when pattern aligns with trend."""
        # Need enough data for MA calculation
        if index < self.slow_ma:
            return False, ''

        # Calculate moving averages
        fast_ma = data.close[index - self.fast_ma:index].mean()
        slow_ma = data.close[index - self.slow_ma:index].mean()

        # Determine trend
        in_uptrend = fast_ma > slow_ma
        in_downtrend = fast_ma < slow_ma

        # Filter patterns
        strong_patterns = [p for p in patterns if p.confidence >= self.min_confidence]

        if not strong_patterns:
            return False, ''

        # Enter long if uptrend and buy signal
        if in_uptrend:
            has_buy = any(
                p.signal in [SignalType.BUY, SignalType.STRONG_BUY]
                for p in strong_patterns
            )
            if has_buy:
                return True, 'long'

        # Enter short if downtrend and sell signal
        elif in_downtrend:
            has_sell = any(
                p.signal in [SignalType.SELL, SignalType.STRONG_SELL]
                for p in strong_patterns
            )
            if has_sell:
                return True, 'short'

        return False, ''

    def should_exit(
        self,
        trade: Trade,
        current_time: datetime,
        current_price: float,
        data: OHLCV,
        index: int,
    ) -> Tuple[bool, str]:
        """Exit on stop loss or trend reversal."""
        # Calculate P&L
        if trade.direction == 'long':
            pnl_pct = (current_price - trade.entry_price) / trade.entry_price
        else:
            pnl_pct = (trade.entry_price - current_price) / trade.entry_price

        # Stop loss
        if pnl_pct <= -self.stop_loss_pct:
            return True, 'stop_loss'

        # Exit on trend reversal
        if index >= self.slow_ma:
            fast_ma = data.close[index - self.fast_ma:index].mean()
            slow_ma = data.close[index - self.slow_ma:index].mean()

            # Exit long on trend reversal
            if trade.direction == 'long' and fast_ma < slow_ma:
                return True, 'trend_reversal'

            # Exit short on trend reversal
            elif trade.direction == 'short' and fast_ma > slow_ma:
                return True, 'trend_reversal'

        return False, ''
