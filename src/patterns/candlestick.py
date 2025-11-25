"""Candlestick pattern detection - comprehensive implementation."""

import uuid
from datetime import datetime
from typing import List

from loguru import logger

from src.core.interfaces import Pattern, PatternDetector
from src.core.types import (OHLCV, PatternResult, PatternType, SignalType,
                            Timeframe)


class CandlestickPattern(Pattern):
    """Base class for candlestick patterns."""

    def __init__(self):
        super().__init__()

    def is_bullish_candle(self, open_price: float, close_price: float) -> bool:
        """Check if candle is bullish."""
        return close_price > open_price

    def is_bearish_candle(self, open_price: float, close_price: float) -> bool:
        """Check if candle is bearish."""
        return close_price < open_price

    def body_size(self, open_price: float, close_price: float) -> float:
        """Calculate candle body size."""
        return abs(close_price - open_price)

    def upper_shadow(self, high: float, open_price: float, close_price: float) -> float:
        """Calculate upper shadow length."""
        return high - max(open_price, close_price)

    def lower_shadow(self, low: float, open_price: float, close_price: float) -> float:
        """Calculate lower shadow length."""
        return min(open_price, close_price) - low

    def is_doji(
        self, open_price: float, close_price: float, high: float, low: float
    ) -> bool:
        """Check if candle is a doji."""
        body = self.body_size(open_price, close_price)
        full_range = high - low
        return body / full_range < 0.1 if full_range > 0 else False


class DojiPattern(CandlestickPattern):
    """Doji pattern detection."""

    def __init__(self):
        super().__init__()
        self.name = "Doji"
        self.description = "Doji candlestick pattern - indecision"

    def detect(self, data: OHLCV) -> List[PatternResult]:
        """Detect Doji patterns."""
        results = []

        if len(data.close) < 1:
            return results

        # Check last candle
        idx = -1
        o, h, l, c = data.open[idx], data.high[idx], data.low[idx], data.close[idx]

        if self.is_doji(o, c, h, l):
            results.append(
                PatternResult(
                    pattern_id=str(uuid.uuid4()),
                    pattern_name="Doji",
                    pattern_type=PatternType.CANDLESTICK_PATTERN,
                    symbol="",
                    timeframe=None,
                    timestamp=datetime.fromtimestamp(data.timestamps[idx]),
                    confidence=0.70,
                    signal=SignalType.HOLD,
                    metadata={"pattern": "doji"},
                    description="Doji pattern - market indecision",
                )
            )

        return results

    def validate(self, result: PatternResult) -> bool:
        """Validate Doji result."""
        return result.pattern_type == PatternType.CANDLESTICK_PATTERN


class HammerPattern(CandlestickPattern):
    """Hammer and Hanging Man pattern detection."""

    def __init__(self):
        super().__init__()
        self.name = "Hammer"
        self.description = "Hammer/Hanging Man pattern"

    def detect(self, data: OHLCV) -> List[PatternResult]:
        """Detect Hammer/Hanging Man patterns."""
        results = []

        if len(data.close) < 2:
            return results

        idx = -1
        o, h, l, c = data.open[idx], data.high[idx], data.low[idx], data.close[idx]

        body = self.body_size(o, c)
        lower = self.lower_shadow(l, o, c)
        upper = self.upper_shadow(h, o, c)
        full_range = h - l

        if full_range == 0:
            return results

        # Hammer criteria: small body, long lower shadow, small upper shadow
        if lower > body * 2 and upper < body * 0.5 and body / full_range < 0.3:
            # Determine if in downtrend (Hammer - bullish) or uptrend (Hanging Man - bearish)
            prev_close = data.close[-2]

            if c < prev_close:  # After downtrend - Hammer (bullish)
                results.append(
                    PatternResult(
                        pattern_id=str(uuid.uuid4()),
                        pattern_name="Hammer",
                        pattern_type=PatternType.CANDLESTICK_PATTERN,
                        symbol="",
                        timeframe=None,
                        timestamp=datetime.fromtimestamp(data.timestamps[idx]),
                        confidence=0.75,
                        signal=SignalType.BUY,
                        metadata={"pattern": "hammer"},
                        description="Hammer pattern - potential bullish reversal",
                    )
                )
            else:  # After uptrend - Hanging Man (bearish)
                results.append(
                    PatternResult(
                        pattern_id=str(uuid.uuid4()),
                        pattern_name="Hanging Man",
                        pattern_type=PatternType.CANDLESTICK_PATTERN,
                        symbol="",
                        timeframe=None,
                        timestamp=datetime.fromtimestamp(data.timestamps[idx]),
                        confidence=0.72,
                        signal=SignalType.SELL,
                        metadata={"pattern": "hanging_man"},
                        description="Hanging Man pattern - potential bearish reversal",
                    )
                )

        return results

    def validate(self, result: PatternResult) -> bool:
        """Validate Hammer result."""
        return result.pattern_type == PatternType.CANDLESTICK_PATTERN


class EngulfingPattern(CandlestickPattern):
    """Bullish and Bearish Engulfing pattern detection."""

    def __init__(self):
        super().__init__()
        self.name = "Engulfing"
        self.description = "Bullish/Bearish Engulfing pattern"

    def detect(self, data: OHLCV) -> List[PatternResult]:
        """Detect Engulfing patterns."""
        results = []

        if len(data.close) < 2:
            return results

        # Current and previous candle
        o1, c1 = data.open[-2], data.close[-2]
        o2, c2 = data.open[-1], data.close[-1]

        # Bullish Engulfing
        if self.is_bearish_candle(o1, c1) and self.is_bullish_candle(o2, c2):
            if c2 > o1 and o2 < c1:  # Current bullish candle engulfs previous bearish
                results.append(
                    PatternResult(
                        pattern_id=str(uuid.uuid4()),
                        pattern_name="Bullish Engulfing",
                        pattern_type=PatternType.CANDLESTICK_PATTERN,
                        symbol="",
                        timeframe=None,
                        timestamp=datetime.fromtimestamp(data.timestamps[-1]),
                        confidence=0.82,
                        signal=SignalType.BUY,
                        metadata={"pattern": "bullish_engulfing"},
                        description="Bullish Engulfing pattern - strong buy signal",
                    )
                )

        # Bearish Engulfing
        elif self.is_bullish_candle(o1, c1) and self.is_bearish_candle(o2, c2):
            if c2 < o1 and o2 > c1:  # Current bearish candle engulfs previous bullish
                results.append(
                    PatternResult(
                        pattern_id=str(uuid.uuid4()),
                        pattern_name="Bearish Engulfing",
                        pattern_type=PatternType.CANDLESTICK_PATTERN,
                        symbol="",
                        timeframe=None,
                        timestamp=datetime.fromtimestamp(data.timestamps[-1]),
                        confidence=0.82,
                        signal=SignalType.SELL,
                        metadata={"pattern": "bearish_engulfing"},
                        description="Bearish Engulfing pattern - strong sell signal",
                    )
                )

        return results

    def validate(self, result: PatternResult) -> bool:
        """Validate Engulfing result."""
        return result.pattern_type == PatternType.CANDLESTICK_PATTERN


class MorningEveningStarPattern(CandlestickPattern):
    """Morning Star and Evening Star three-candle pattern."""

    def __init__(self):
        super().__init__()
        self.name = "Morning/Evening Star"
        self.description = "Morning/Evening Star three-candle reversal pattern"

    def detect(self, data: OHLCV) -> List[PatternResult]:
        """Detect Morning/Evening Star patterns."""
        results = []

        if len(data.close) < 3:
            return results

        o1, c1 = data.open[-3], data.close[-3]
        o2, h2, l2, c2 = data.open[-2], data.high[-2], data.low[-2], data.close[-2]
        o3, c3 = data.open[-1], data.close[-1]

        # Morning Star (bullish reversal)
        if (
            self.is_bearish_candle(o1, c1)
            and self.is_doji(o2, c2, h2, l2)
            and self.is_bullish_candle(o3, c3)
        ):

            if c3 > (o1 + c1) / 2:  # Third candle closes above midpoint of first
                results.append(
                    PatternResult(
                        pattern_id=str(uuid.uuid4()),
                        pattern_name="Morning Star",
                        pattern_type=PatternType.CANDLESTICK_PATTERN,
                        symbol="",
                        timeframe=None,
                        timestamp=datetime.fromtimestamp(data.timestamps[-1]),
                        confidence=0.85,
                        signal=SignalType.STRONG_BUY,
                        metadata={"pattern": "morning_star"},
                        description="Morning Star pattern - strong bullish reversal",
                    )
                )

        # Evening Star (bearish reversal)
        elif (
            self.is_bullish_candle(o1, c1)
            and self.is_doji(o2, c2, h2, l2)
            and self.is_bearish_candle(o3, c3)
        ):

            if c3 < (o1 + c1) / 2:  # Third candle closes below midpoint of first
                results.append(
                    PatternResult(
                        pattern_id=str(uuid.uuid4()),
                        pattern_name="Evening Star",
                        pattern_type=PatternType.CANDLESTICK_PATTERN,
                        symbol="",
                        timeframe=None,
                        timestamp=datetime.fromtimestamp(data.timestamps[-1]),
                        confidence=0.85,
                        signal=SignalType.STRONG_SELL,
                        metadata={"pattern": "evening_star"},
                        description="Evening Star pattern - strong bearish reversal",
                    )
                )

        return results

    def validate(self, result: PatternResult) -> bool:
        """Validate Star pattern result."""
        return result.pattern_type == PatternType.CANDLESTICK_PATTERN


class ThreeSoldiersPattern(CandlestickPattern):
    """Three White Soldiers and Three Black Crows patterns."""

    def __init__(self):
        super().__init__()
        self.name = "Three Soldiers/Crows"
        self.description = "Three White Soldiers / Three Black Crows pattern"

    def detect(self, data: OHLCV) -> List[PatternResult]:
        """Detect Three Soldiers/Crows patterns."""
        results = []

        if len(data.close) < 3:
            return results

        # Get last three candles
        candles = [(data.open[i], data.close[i]) for i in range(-3, 0)]

        # Three White Soldiers (bullish)
        if all(self.is_bullish_candle(o, c) for o, c in candles):
            # Each candle should close higher and open within previous body
            if (
                candles[1][1] > candles[0][1]
                and candles[2][1] > candles[1][1]
                and candles[1][0] > candles[0][0]
                and candles[2][0] > candles[1][0]
            ):

                results.append(
                    PatternResult(
                        pattern_id=str(uuid.uuid4()),
                        pattern_name="Three White Soldiers",
                        pattern_type=PatternType.CANDLESTICK_PATTERN,
                        symbol="",
                        timeframe=None,
                        timestamp=datetime.fromtimestamp(data.timestamps[-1]),
                        confidence=0.80,
                        signal=SignalType.STRONG_BUY,
                        metadata={"pattern": "three_white_soldiers"},
                        description="Three White Soldiers - strong bullish trend",
                    )
                )

        # Three Black Crows (bearish)
        elif all(self.is_bearish_candle(o, c) for o, c in candles):
            # Each candle should close lower and open within previous body
            if (
                candles[1][1] < candles[0][1]
                and candles[2][1] < candles[1][1]
                and candles[1][0] < candles[0][0]
                and candles[2][0] < candles[1][0]
            ):

                results.append(
                    PatternResult(
                        pattern_id=str(uuid.uuid4()),
                        pattern_name="Three Black Crows",
                        pattern_type=PatternType.CANDLESTICK_PATTERN,
                        symbol="",
                        timeframe=None,
                        timestamp=datetime.fromtimestamp(data.timestamps[-1]),
                        confidence=0.80,
                        signal=SignalType.STRONG_SELL,
                        metadata={"pattern": "three_black_crows"},
                        description="Three Black Crows - strong bearish trend",
                    )
                )

        return results

    def validate(self, result: PatternResult) -> bool:
        """Validate Three Soldiers/Crows result."""
        return result.pattern_type == PatternType.CANDLESTICK_PATTERN


class ShootingStarPattern(CandlestickPattern):
    """Shooting Star and Inverted Hammer pattern detection."""

    def __init__(self):
        super().__init__()
        self.name = "Shooting Star"
        self.description = "Shooting Star / Inverted Hammer pattern"

    def detect(self, data: OHLCV) -> List[PatternResult]:
        """Detect Shooting Star/Inverted Hammer patterns."""
        results = []

        if len(data.close) < 2:
            return results

        idx = -1
        o, h, l, c = data.open[idx], data.high[idx], data.low[idx], data.close[idx]

        body = self.body_size(o, c)
        upper = self.upper_shadow(h, o, c)
        lower = self.lower_shadow(l, o, c)
        full_range = h - l

        if full_range == 0:
            return results

        # Shooting Star/Inverted Hammer: small body, long upper shadow, small lower shadow
        if upper > body * 2 and lower < body * 0.5 and body / full_range < 0.3:
            prev_close = data.close[-2]

            if c > prev_close:  # After uptrend - Shooting Star (bearish)
                results.append(
                    PatternResult(
                        pattern_id=str(uuid.uuid4()),
                        pattern_name="Shooting Star",
                        pattern_type=PatternType.CANDLESTICK_PATTERN,
                        symbol="",
                        timeframe=None,
                        timestamp=datetime.fromtimestamp(data.timestamps[idx]),
                        confidence=0.75,
                        signal=SignalType.SELL,
                        metadata={"pattern": "shooting_star"},
                        description="Shooting Star - potential bearish reversal",
                    )
                )
            else:  # After downtrend - Inverted Hammer (bullish)
                results.append(
                    PatternResult(
                        pattern_id=str(uuid.uuid4()),
                        pattern_name="Inverted Hammer",
                        pattern_type=PatternType.CANDLESTICK_PATTERN,
                        symbol="",
                        timeframe=None,
                        timestamp=datetime.fromtimestamp(data.timestamps[idx]),
                        confidence=0.72,
                        signal=SignalType.BUY,
                        metadata={"pattern": "inverted_hammer"},
                        description="Inverted Hammer - potential bullish reversal",
                    )
                )

        return results

    def validate(self, result: PatternResult) -> bool:
        """Validate Shooting Star result."""
        return result.pattern_type == PatternType.CANDLESTICK_PATTERN


class CandlestickPatternDetector(PatternDetector):
    """
    Comprehensive candlestick pattern detector.

    Implements multiple candlestick patterns with extensible architecture.
    """

    def __init__(self):
        super().__init__()
        self.patterns: List[CandlestickPattern] = []

        # Register default patterns
        self._register_default_patterns()

        logger.info(
            f"Candlestick Pattern Detector initialized with {len(self.patterns)} patterns"
        )

    def _register_default_patterns(self):
        """Register default candlestick patterns."""
        self.patterns.extend(
            [
                DojiPattern(),
                HammerPattern(),
                EngulfingPattern(),
                MorningEveningStarPattern(),
                ThreeSoldiersPattern(),
                ShootingStarPattern(),
            ]
        )

    async def detect_patterns(
        self,
        symbol: str,
        timeframe: Timeframe,
        data: OHLCV,
    ) -> List[PatternResult]:
        """Detect all registered candlestick patterns."""
        all_results = []

        for pattern in self.patterns:
            try:
                results = pattern.detect(data)

                # Add context to results
                for result in results:
                    result.symbol = symbol
                    result.timeframe = timeframe

                all_results.extend(results)
                logger.debug(f"{pattern.name}: {len(results)} patterns detected")

            except Exception as e:
                logger.error(f"Error detecting {pattern.name}: {e}")

        return all_results

    def register_pattern(self, pattern: Pattern) -> None:
        """Register a candlestick pattern."""
        self.patterns.append(pattern)
        logger.info(f"Registered candlestick pattern: {pattern.name}")

    def unregister_pattern(self, pattern_name: str) -> None:
        """Unregister a pattern."""
        self.patterns = [p for p in self.patterns if p.name != pattern_name]
        logger.info(f"Unregistered candlestick pattern: {pattern_name}")

    def list_patterns(self) -> List[str]:
        """List all registered patterns."""
        return [p.name for p in self.patterns]
