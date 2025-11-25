"""
Advanced technical indicator patterns - ADX, Parabolic SAR, Stochastic.

These patterns provide additional signal confirmation and trend strength analysis
for the analytical hemisphere of the dual-hemisphere trading system.
"""

import numpy as np
from typing import List, Optional, Tuple
from datetime import datetime
import uuid

from src.core.types import OHLCV, PatternResult, SignalType, PatternType
from src.patterns.detector import Pattern
from src.utils.optimization import VectorizedIndicators


class ADXPattern(Pattern):
    """
    Average Directional Index (ADX) pattern detector.

    ADX measures trend strength regardless of direction.
    High ADX (>25) indicates strong trend, low ADX (<20) indicates weak trend.
    Used with +DI and -DI to determine trend direction.
    """

    def __init__(
        self,
        period: int = 14,
        strong_trend_threshold: float = 25.0,
        weak_trend_threshold: float = 20.0,
    ):
        super().__init__()
        self.name = "ADX Trend Strength"
        self.period = period
        self.strong_trend_threshold = strong_trend_threshold
        self.weak_trend_threshold = weak_trend_threshold

    def validate(self, result: PatternResult) -> bool:
        """Validate ADX result."""
        required = ['adx', 'plus_di', 'minus_di']
        return all(key in result.metadata for key in required)

    def detect(self, data: OHLCV) -> List[PatternResult]:
        """Detect ADX trend strength patterns."""
        if len(data.close) < self.period * 2:
            return []

        # Calculate ADX, +DI, -DI
        adx, plus_di, minus_di = self._calculate_adx(
            data.high, data.low, data.close, self.period
        )

        if len(adx) == 0:
            return []

        current_adx = adx[-1]
        current_plus_di = plus_di[-1]
        current_minus_di = minus_di[-1]

        patterns = []

        # Strong uptrend: ADX > threshold and +DI > -DI
        if current_adx > self.strong_trend_threshold and current_plus_di > current_minus_di:
            confidence = min(
                0.7 + (current_adx - self.strong_trend_threshold) / 100,
                0.95
            )
            patterns.append(PatternResult(
                pattern_id=str(uuid.uuid4()),
                pattern_name="ADX Strong Uptrend",
                pattern_type=PatternType.TECHNICAL_INDICATOR,
                symbol="",
                timeframe=None,
                timestamp=datetime.fromtimestamp(data.timestamps[-1]),
                signal=SignalType.BUY,
                confidence=confidence,
                metadata={
                    'adx': float(current_adx),
                    'plus_di': float(current_plus_di),
                    'minus_di': float(current_minus_di),
                    'trend_strength': 'strong',
                },
                description=f"Strong uptrend: ADX={current_adx:.1f}, +DI={current_plus_di:.1f}"
            ))

        # Strong downtrend: ADX > threshold and -DI > +DI
        elif current_adx > self.strong_trend_threshold and current_minus_di > current_plus_di:
            confidence = min(
                0.7 + (current_adx - self.strong_trend_threshold) / 100,
                0.95
            )
            patterns.append(PatternResult(
                pattern_id=str(uuid.uuid4()),
                pattern_name="ADX Strong Downtrend",
                pattern_type=PatternType.TECHNICAL_INDICATOR,
                symbol="",
                timeframe=None,
                timestamp=datetime.fromtimestamp(data.timestamps[-1]),
                signal=SignalType.SELL,
                confidence=confidence,
                metadata={
                    'adx': float(current_adx),
                    'plus_di': float(current_plus_di),
                    'minus_di': float(current_minus_di),
                    'trend_strength': 'strong',
                },
                description=f"Strong downtrend: ADX={current_adx:.1f}, -DI={current_minus_di:.1f}"
            ))

        # Weak trend / ranging market
        elif current_adx < self.weak_trend_threshold:
            patterns.append(PatternResult(
                pattern_id=str(uuid.uuid4()),
                pattern_name="ADX Weak Trend",
                pattern_type=PatternType.TECHNICAL_INDICATOR,
                symbol="",
                timeframe=None,
                timestamp=datetime.fromtimestamp(data.timestamps[-1]),
                signal=SignalType.HOLD,
                confidence=0.6,
                metadata={
                    'adx': float(current_adx),
                    'plus_di': float(current_plus_di),
                    'minus_di': float(current_minus_di),
                    'trend_strength': 'weak',
                },
                description=f"Weak trend/ranging: ADX={current_adx:.1f}"
            ))

        return patterns

    def _calculate_adx(
        self,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        period: int
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Calculate ADX, +DI, and -DI."""
        # True Range
        high_low = high[1:] - low[1:]
        high_close = np.abs(high[1:] - close[:-1])
        low_close = np.abs(low[1:] - close[:-1])
        tr = np.maximum(high_low, np.maximum(high_close, low_close))

        # Directional Movement
        high_diff = high[1:] - high[:-1]
        low_diff = low[:-1] - low[1:]

        plus_dm = np.where((high_diff > low_diff) & (high_diff > 0), high_diff, 0)
        minus_dm = np.where((low_diff > high_diff) & (low_diff > 0), low_diff, 0)

        # Smoothed TR and DM
        atr = self._wilder_smooth(tr, period)
        plus_dm_smooth = self._wilder_smooth(plus_dm, period)
        minus_dm_smooth = self._wilder_smooth(minus_dm, period)

        # Directional Indicators
        plus_di = 100 * plus_dm_smooth / atr
        minus_di = 100 * minus_dm_smooth / atr

        # ADX
        dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di + 1e-10)
        adx = self._wilder_smooth(dx, period)

        return adx, plus_di, minus_di

    def _wilder_smooth(self, data: np.ndarray, period: int) -> np.ndarray:
        """Wilder's smoothing method."""
        if len(data) < period:
            return np.array([])

        smoothed = np.zeros(len(data))
        smoothed[period-1] = np.mean(data[:period])

        for i in range(period, len(data)):
            smoothed[i] = (smoothed[i-1] * (period - 1) + data[i]) / period

        return smoothed[period-1:]


class ParabolicSARPattern(Pattern):
    """
    Parabolic SAR (Stop and Reverse) pattern detector.

    SAR provides stop-loss levels and trend reversal signals.
    When price crosses SAR, it signals potential trend reversal.
    """

    def __init__(
        self,
        acceleration: float = 0.02,
        maximum: float = 0.20,
    ):
        super().__init__()
        self.name = "Parabolic SAR"
        self.acceleration = acceleration
        self.maximum = maximum

    def validate(self, result: PatternResult) -> bool:
        """Validate SAR result."""
        return 'sar' in result.metadata and 'trend' in result.metadata

    def detect(self, data: OHLCV) -> List[PatternResult]:
        """Detect Parabolic SAR patterns."""
        if len(data.close) < 5:
            return []

        sar_values, trend = self._calculate_sar(
            data.high, data.low, data.close,
            self.acceleration, self.maximum
        )

        if len(sar_values) < 2:
            return []

        current_sar = sar_values[-1]
        prev_sar = sar_values[-2]
        current_trend = trend[-1]
        prev_trend = trend[-2]
        current_price = data.close[-1]

        patterns = []

        # Bullish reversal: SAR flipped from above to below price
        if prev_trend == -1 and current_trend == 1:
            patterns.append(PatternResult(
                pattern_id=str(uuid.uuid4()),
                pattern_name="SAR Bullish Reversal",
                pattern_type=PatternType.TECHNICAL_INDICATOR,
                symbol="",
                timeframe=None,
                timestamp=datetime.fromtimestamp(data.timestamps[-1]),
                signal=SignalType.BUY,
                confidence=0.75,
                metadata={
                    'sar': float(current_sar),
                    'price': float(current_price),
                    'trend': 'up',
                    'reversal': True,
                },
                description=f"Bullish SAR reversal: SAR={current_sar:.2f}, Price={current_price:.2f}"
            ))

        # Bearish reversal: SAR flipped from below to above price
        elif prev_trend == 1 and current_trend == -1:
            patterns.append(PatternResult(
                pattern_id=str(uuid.uuid4()),
                pattern_name="SAR Bearish Reversal",
                pattern_type=PatternType.TECHNICAL_INDICATOR,
                symbol="",
                timeframe=None,
                timestamp=datetime.fromtimestamp(data.timestamps[-1]),
                signal=SignalType.SELL,
                confidence=0.75,
                metadata={
                    'sar': float(current_sar),
                    'price': float(current_price),
                    'trend': 'down',
                    'reversal': True,
                },
                description=f"Bearish SAR reversal: SAR={current_sar:.2f}, Price={current_price:.2f}"
            ))

        # Continuing uptrend
        elif current_trend == 1 and prev_trend == 1:
            distance = (current_price - current_sar) / current_price
            confidence = min(0.6 + distance * 5, 0.85)

            patterns.append(PatternResult(
                pattern_id=str(uuid.uuid4()),
                pattern_name="SAR Uptrend",
                pattern_type=PatternType.TECHNICAL_INDICATOR,
                symbol="",
                timeframe=None,
                timestamp=datetime.fromtimestamp(data.timestamps[-1]),
                signal=SignalType.BUY,
                confidence=confidence,
                metadata={
                    'sar': float(current_sar),
                    'price': float(current_price),
                    'trend': 'up',
                    'reversal': False,
                },
                description=f"SAR uptrend: SAR={current_sar:.2f}, Price={current_price:.2f}"
            ))

        # Continuing downtrend
        elif current_trend == -1 and prev_trend == -1:
            distance = (current_sar - current_price) / current_price
            confidence = min(0.6 + distance * 5, 0.85)

            patterns.append(PatternResult(
                pattern_id=str(uuid.uuid4()),
                pattern_name="SAR Downtrend",
                pattern_type=PatternType.TECHNICAL_INDICATOR,
                symbol="",
                timeframe=None,
                timestamp=datetime.fromtimestamp(data.timestamps[-1]),
                signal=SignalType.SELL,
                confidence=confidence,
                metadata={
                    'sar': float(current_sar),
                    'price': float(current_price),
                    'trend': 'down',
                    'reversal': False,
                },
                description=f"SAR downtrend: SAR={current_sar:.2f}, Price={current_price:.2f}"
            ))

        return patterns

    def _calculate_sar(
        self,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        af_start: float,
        af_max: float
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Calculate Parabolic SAR."""
        n = len(close)
        sar = np.zeros(n)
        trend = np.zeros(n)
        af = af_start
        ep = 0.0

        # Initialize
        trend[0] = 1 if close[1] > close[0] else -1
        sar[0] = low[0] if trend[0] == 1 else high[0]
        ep = high[0] if trend[0] == 1 else low[0]

        for i in range(1, n):
            # Calculate SAR
            sar[i] = sar[i-1] + af * (ep - sar[i-1])

            # Check for reversal
            if trend[i-1] == 1:  # Uptrend
                if low[i] < sar[i]:
                    # Reverse to downtrend
                    trend[i] = -1
                    sar[i] = ep
                    ep = low[i]
                    af = af_start
                else:
                    trend[i] = 1
                    if high[i] > ep:
                        ep = high[i]
                        af = min(af + af_start, af_max)
            else:  # Downtrend
                if high[i] > sar[i]:
                    # Reverse to uptrend
                    trend[i] = 1
                    sar[i] = ep
                    ep = high[i]
                    af = af_start
                else:
                    trend[i] = -1
                    if low[i] < ep:
                        ep = low[i]
                        af = min(af + af_start, af_max)

        return sar, trend


class StochasticPattern(Pattern):
    """
    Stochastic Oscillator pattern detector.

    Stochastic compares closing price to price range over a period.
    Overbought (>80), Oversold (<20), and divergences provide signals.
    """

    def __init__(
        self,
        k_period: int = 14,
        d_period: int = 3,
        overbought: float = 80.0,
        oversold: float = 20.0,
    ):
        super().__init__()
        self.name = "Stochastic Oscillator"
        self.k_period = k_period
        self.d_period = d_period
        self.overbought = overbought
        self.oversold = oversold

    def validate(self, result: PatternResult) -> bool:
        """Validate Stochastic result."""
        required = ['k', 'd']
        return all(key in result.metadata for key in required)

    def detect(self, data: OHLCV) -> List[PatternResult]:
        """Detect Stochastic patterns."""
        if len(data.close) < self.k_period + self.d_period:
            return []

        k_values, d_values = self._calculate_stochastic(
            data.high, data.low, data.close,
            self.k_period, self.d_period
        )

        if len(k_values) < 2 or len(d_values) < 2:
            return []

        current_k = k_values[-1]
        current_d = d_values[-1]
        prev_k = k_values[-2]
        prev_d = d_values[-2]

        patterns = []

        # Oversold with bullish crossover
        if current_k < self.oversold and prev_k < prev_d and current_k > current_d:
            patterns.append(PatternResult(
                pattern_id=str(uuid.uuid4()),
                pattern_name="Stochastic Oversold Bullish Cross",
                pattern_type=PatternType.TECHNICAL_INDICATOR,
                symbol="",
                timeframe=None,
                timestamp=datetime.fromtimestamp(data.timestamps[-1]),
                signal=SignalType.BUY,
                confidence=0.80,
                metadata={
                    'k': float(current_k),
                    'd': float(current_d),
                    'zone': 'oversold',
                    'crossover': 'bullish',
                },
                description=f"Stochastic oversold bullish cross: K={current_k:.1f}, D={current_d:.1f}"
            ))

        # Overbought with bearish crossover
        elif current_k > self.overbought and prev_k > prev_d and current_k < current_d:
            patterns.append(PatternResult(
                pattern_id=str(uuid.uuid4()),
                pattern_name="Stochastic Overbought Bearish Cross",
                pattern_type=PatternType.TECHNICAL_INDICATOR,
                symbol="",
                timeframe=None,
                timestamp=datetime.fromtimestamp(data.timestamps[-1]),
                signal=SignalType.SELL,
                confidence=0.80,
                metadata={
                    'k': float(current_k),
                    'd': float(current_d),
                    'zone': 'overbought',
                    'crossover': 'bearish',
                },
                description=f"Stochastic overbought bearish cross: K={current_k:.1f}, D={current_d:.1f}"
            ))

        # Oversold (no crossover yet)
        elif current_k < self.oversold:
            patterns.append(PatternResult(
                pattern_id=str(uuid.uuid4()),
                pattern_name="Stochastic Oversold",
                pattern_type=PatternType.TECHNICAL_INDICATOR,
                symbol="",
                timeframe=None,
                timestamp=datetime.fromtimestamp(data.timestamps[-1]),
                signal=SignalType.BUY,
                confidence=0.65,
                metadata={
                    'k': float(current_k),
                    'd': float(current_d),
                    'zone': 'oversold',
                    'crossover': None,
                },
                description=f"Stochastic oversold: K={current_k:.1f}, D={current_d:.1f}"
            ))

        # Overbought (no crossover yet)
        elif current_k > self.overbought:
            patterns.append(PatternResult(
                pattern_id=str(uuid.uuid4()),
                pattern_name="Stochastic Overbought",
                pattern_type=PatternType.TECHNICAL_INDICATOR,
                symbol="",
                timeframe=None,
                timestamp=datetime.fromtimestamp(data.timestamps[-1]),
                signal=SignalType.SELL,
                confidence=0.65,
                metadata={
                    'k': float(current_k),
                    'd': float(current_d),
                    'zone': 'overbought',
                    'crossover': None,
                },
                description=f"Stochastic overbought: K={current_k:.1f}, D={current_d:.1f}"
            ))

        return patterns

    def _calculate_stochastic(
        self,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        k_period: int,
        d_period: int
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Calculate Stochastic %K and %D."""
        k_values = []

        for i in range(k_period - 1, len(close)):
            period_high = np.max(high[i-k_period+1:i+1])
            period_low = np.min(low[i-k_period+1:i+1])

            if period_high == period_low:
                k = 50.0
            else:
                k = 100 * (close[i] - period_low) / (period_high - period_low)

            k_values.append(k)

        k_values = np.array(k_values)

        # %D is SMA of %K
        d_values = VectorizedIndicators.sma(k_values, d_period)

        # Align arrays
        k_values = k_values[d_period-1:]

        return k_values, d_values
