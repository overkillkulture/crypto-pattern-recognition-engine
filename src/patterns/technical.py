"""Technical indicator pattern implementations."""

from typing import List
from datetime import datetime
import uuid

from src.core.interfaces import Pattern
from src.core.types import (
    PatternResult,
    PatternType,
    SignalType,
    OHLCV,
)
from src.utils.metrics import (
    calculate_rsi,
    calculate_macd,
    calculate_bollinger_bands,
    calculate_ema,
    calculate_sma,
    calculate_atr,
    calculate_vwap,
    calculate_obv,
)
import numpy as np


class RSIPattern(Pattern):
    """RSI-based pattern detection."""

    def __init__(self, period: int = 14, overbought: float = 70, oversold: float = 30):
        super().__init__()
        self.name = "RSI"
        self.description = "Relative Strength Index pattern"
        self.period = period
        self.overbought = overbought
        self.oversold = oversold

    def detect(self, data: OHLCV) -> List[PatternResult]:
        """Detect RSI patterns."""
        results = []

        if len(data.close) < self.period + 1:
            return results

        rsi_values = calculate_rsi(data.close, self.period)
        current_rsi = rsi_values[-1]

        if np.isnan(current_rsi):
            return results

        # Overbought condition
        if current_rsi > self.overbought:
            results.append(PatternResult(
                pattern_id=str(uuid.uuid4()),
                pattern_name="RSI Overbought",
                pattern_type=PatternType.TECHNICAL_INDICATOR,
                symbol="",  # Will be filled by detector
                timeframe=None,  # Will be filled by detector
                timestamp=datetime.fromtimestamp(data.timestamps[-1]),
                confidence=min((current_rsi - self.overbought) / (100 - self.overbought), 0.99),
                signal=SignalType.SELL,
                metadata={
                    'rsi': current_rsi,
                    'threshold': self.overbought,
                },
                description=f"RSI overbought at {current_rsi:.2f}",
            ))

        # Oversold condition
        elif current_rsi < self.oversold:
            results.append(PatternResult(
                pattern_id=str(uuid.uuid4()),
                pattern_name="RSI Oversold",
                pattern_type=PatternType.TECHNICAL_INDICATOR,
                symbol="",
                timeframe=None,
                timestamp=datetime.fromtimestamp(data.timestamps[-1]),
                confidence=min((self.oversold - current_rsi) / self.oversold, 0.99),
                signal=SignalType.BUY,
                metadata={
                    'rsi': current_rsi,
                    'threshold': self.oversold,
                },
                description=f"RSI oversold at {current_rsi:.2f}",
            ))

        # RSI Divergence detection
        if len(rsi_values) >= 20 and len(data.close) >= 20:
            # Bullish divergence: price makes lower low but RSI makes higher low
            price_window = data.close[-20:]
            rsi_window = rsi_values[-20:]

            price_min_idx = np.argmin(price_window)
            rsi_min_idx = np.argmin(rsi_window)

            if price_min_idx > 10 and rsi_min_idx < price_min_idx:
                results.append(PatternResult(
                    pattern_id=str(uuid.uuid4()),
                    pattern_name="RSI Bullish Divergence",
                    pattern_type=PatternType.TECHNICAL_INDICATOR,
                    symbol="",
                    timeframe=None,
                    timestamp=datetime.fromtimestamp(data.timestamps[-1]),
                    confidence=0.75,
                    signal=SignalType.BUY,
                    metadata={'rsi': float(current_rsi), 'type': 'bullish_divergence'},
                    description="RSI showing bullish divergence",
                ))

        return results

    def validate(self, result: PatternResult) -> bool:
        """Validate RSI pattern result."""
        return (
            result.pattern_type == PatternType.TECHNICAL_INDICATOR and
            'rsi' in result.metadata and
            0 <= result.metadata['rsi'] <= 100
        )


class MACDPattern(Pattern):
    """MACD-based pattern detection."""

    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9):
        super().__init__()
        self.name = "MACD"
        self.description = "Moving Average Convergence Divergence pattern"
        self.fast = fast
        self.slow = slow
        self.signal = signal

    def detect(self, data: OHLCV) -> List[PatternResult]:
        """Detect MACD patterns."""
        results = []

        if len(data.close) < self.slow + self.signal:
            return results

        macd_line, signal_line, histogram = calculate_macd(
            data.close, self.fast, self.slow, self.signal
        )

        # Check for crossovers
        if len(histogram) < 2:
            return results

        current_hist = histogram[-1]
        prev_hist = histogram[-2]

        # Bullish crossover (MACD crosses above signal)
        if prev_hist < 0 and current_hist > 0:
            confidence = min(abs(current_hist) / (abs(prev_hist) + abs(current_hist)), 0.95)

            results.append(PatternResult(
                pattern_id=str(uuid.uuid4()),
                pattern_name="MACD Bullish Crossover",
                pattern_type=PatternType.TECHNICAL_INDICATOR,
                symbol="",
                timeframe=None,
                timestamp=datetime.fromtimestamp(data.timestamps[-1]),
                confidence=confidence,
                signal=SignalType.BUY,
                metadata={
                    'macd': float(macd_line[-1]),
                    'signal': float(signal_line[-1]),
                    'histogram': float(current_hist),
                },
                description="MACD bullish crossover detected",
            ))

        # Bearish crossover (MACD crosses below signal)
        elif prev_hist > 0 and current_hist < 0:
            confidence = min(abs(current_hist) / (abs(prev_hist) + abs(current_hist)), 0.95)

            results.append(PatternResult(
                pattern_id=str(uuid.uuid4()),
                pattern_name="MACD Bearish Crossover",
                pattern_type=PatternType.TECHNICAL_INDICATOR,
                symbol="",
                timeframe=None,
                timestamp=datetime.fromtimestamp(data.timestamps[-1]),
                confidence=confidence,
                signal=SignalType.SELL,
                metadata={
                    'macd': float(macd_line[-1]),
                    'signal': float(signal_line[-1]),
                    'histogram': float(current_hist),
                },
                description="MACD bearish crossover detected",
            ))

        return results

    def validate(self, result: PatternResult) -> bool:
        """Validate MACD pattern result."""
        return (
            result.pattern_type == PatternType.TECHNICAL_INDICATOR and
            'macd' in result.metadata and
            'signal' in result.metadata and
            'histogram' in result.metadata
        )


class BollingerBandsPattern(Pattern):
    """Bollinger Bands pattern detection."""

    def __init__(self, period: int = 20, std_dev: float = 2.0):
        super().__init__()
        self.name = "Bollinger Bands"
        self.description = "Bollinger Bands squeeze and breakout patterns"
        self.period = period
        self.std_dev = std_dev

    def detect(self, data: OHLCV) -> List[PatternResult]:
        """Detect Bollinger Bands patterns."""
        results = []

        if len(data.close) < self.period:
            return results

        upper, middle, lower = calculate_bollinger_bands(data.close, self.period, self.std_dev)

        current_price = data.close[-1]
        current_upper = upper[-1]
        current_lower = lower[-1]
        current_middle = middle[-1]

        if np.isnan(current_upper) or np.isnan(current_lower):
            return results

        # Price touching or breaking upper band (overbought)
        if current_price >= current_upper * 0.99:
            results.append(PatternResult(
                pattern_id=str(uuid.uuid4()),
                pattern_name="Bollinger Band Upper Break",
                pattern_type=PatternType.TECHNICAL_INDICATOR,
                symbol="",
                timeframe=None,
                timestamp=datetime.fromtimestamp(data.timestamps[-1]),
                confidence=0.80,
                signal=SignalType.SELL,
                metadata={
                    'price': float(current_price),
                    'upper_band': float(current_upper),
                    'middle_band': float(current_middle),
                    'lower_band': float(current_lower),
                },
                description="Price at upper Bollinger Band",
            ))

        # Price touching or breaking lower band (oversold)
        elif current_price <= current_lower * 1.01:
            results.append(PatternResult(
                pattern_id=str(uuid.uuid4()),
                pattern_name="Bollinger Band Lower Break",
                pattern_type=PatternType.TECHNICAL_INDICATOR,
                symbol="",
                timeframe=None,
                timestamp=datetime.fromtimestamp(data.timestamps[-1]),
                confidence=0.80,
                signal=SignalType.BUY,
                metadata={
                    'price': float(current_price),
                    'upper_band': float(current_upper),
                    'middle_band': float(current_middle),
                    'lower_band': float(current_lower),
                },
                description="Price at lower Bollinger Band",
            ))

        # Bollinger Squeeze (bands narrowing)
        if len(upper) >= 20:
            band_width = upper[-1] - lower[-1]
            avg_band_width = np.mean(upper[-20:] - lower[-20:])

            if band_width < avg_band_width * 0.75:
                results.append(PatternResult(
                    pattern_id=str(uuid.uuid4()),
                    pattern_name="Bollinger Squeeze",
                    pattern_type=PatternType.TECHNICAL_INDICATOR,
                    symbol="",
                    timeframe=None,
                    timestamp=datetime.fromtimestamp(data.timestamps[-1]),
                    confidence=0.70,
                    signal=SignalType.HOLD,
                    metadata={
                        'band_width': float(band_width),
                        'avg_band_width': float(avg_band_width),
                    },
                    description="Bollinger Bands squeezing - expect breakout",
                ))

        return results

    def validate(self, result: PatternResult) -> bool:
        """Validate Bollinger Bands result."""
        return result.pattern_type == PatternType.TECHNICAL_INDICATOR


class StochasticPattern(Pattern):
    """Stochastic Oscillator pattern detection."""

    def __init__(self, k_period: int = 14, d_period: int = 3):
        super().__init__()
        self.name = "Stochastic"
        self.description = "Stochastic Oscillator pattern"
        self.k_period = k_period
        self.d_period = d_period

    def detect(self, data: OHLCV) -> List[PatternResult]:
        """Detect Stochastic patterns."""
        results = []

        if len(data.close) < self.k_period:
            return results

        # Calculate %K
        k_values = []
        for i in range(self.k_period - 1, len(data.close)):
            window_high = np.max(data.high[i - self.k_period + 1:i + 1])
            window_low = np.min(data.low[i - self.k_period + 1:i + 1])

            if window_high == window_low:
                k_values.append(50.0)
            else:
                k = 100 * (data.close[i] - window_low) / (window_high - window_low)
                k_values.append(k)

        if len(k_values) < self.d_period:
            return results

        # Calculate %D (SMA of %K)
        k_array = np.array(k_values)
        d_values = calculate_sma(k_array, self.d_period)

        current_k = k_values[-1]

        # Overbought
        if current_k > 80:
            results.append(PatternResult(
                pattern_id=str(uuid.uuid4()),
                pattern_name="Stochastic Overbought",
                pattern_type=PatternType.TECHNICAL_INDICATOR,
                symbol="",
                timeframe=None,
                timestamp=datetime.fromtimestamp(data.timestamps[-1]),
                confidence=min((current_k - 80) / 20, 0.95),
                signal=SignalType.SELL,
                metadata={'k': float(current_k)},
                description=f"Stochastic overbought at {current_k:.2f}",
            ))

        # Oversold
        elif current_k < 20:
            results.append(PatternResult(
                pattern_id=str(uuid.uuid4()),
                pattern_name="Stochastic Oversold",
                pattern_type=PatternType.TECHNICAL_INDICATOR,
                symbol="",
                timeframe=None,
                timestamp=datetime.fromtimestamp(data.timestamps[-1]),
                confidence=min((20 - current_k) / 20, 0.95),
                signal=SignalType.BUY,
                metadata={'k': float(current_k)},
                description=f"Stochastic oversold at {current_k:.2f}",
            ))

        # Crossovers
        if len(k_values) >= 2 and len(d_values) >= 2:
            prev_k = k_values[-2]
            current_d = d_values[-1]
            prev_d = d_values[-2]

            # Bullish crossover
            if prev_k < prev_d and current_k > current_d:
                results.append(PatternResult(
                    pattern_id=str(uuid.uuid4()),
                    pattern_name="Stochastic Bullish Crossover",
                    pattern_type=PatternType.TECHNICAL_INDICATOR,
                    symbol="",
                    timeframe=None,
                    timestamp=datetime.fromtimestamp(data.timestamps[-1]),
                    confidence=0.75,
                    signal=SignalType.BUY,
                    metadata={'k': float(current_k), 'd': float(current_d)},
                    description="Stochastic %K crossed above %D",
                ))

        return results

    def validate(self, result: PatternResult) -> bool:
        """Validate Stochastic result."""
        return result.pattern_type == PatternType.TECHNICAL_INDICATOR


class VWAPPattern(Pattern):
    """VWAP (Volume Weighted Average Price) pattern detection."""

    def __init__(self):
        super().__init__()
        self.name = "VWAP"
        self.description = "Volume Weighted Average Price pattern"

    def detect(self, data: OHLCV) -> List[PatternResult]:
        """Detect VWAP patterns."""
        results = []

        if len(data.close) < 2:
            return results

        vwap = calculate_vwap(data.high, data.low, data.close, data.volume)
        current_price = data.close[-1]
        current_vwap = vwap[-1]

        if np.isnan(current_vwap):
            return results

        # Price crosses above VWAP (bullish)
        if len(data.close) >= 2 and len(vwap) >= 2:
            prev_price = data.close[-2]
            prev_vwap = vwap[-2]

            if prev_price < prev_vwap and current_price > current_vwap:
                results.append(PatternResult(
                    pattern_id=str(uuid.uuid4()),
                    pattern_name="VWAP Bullish Cross",
                    pattern_type=PatternType.TECHNICAL_INDICATOR,
                    symbol="",
                    timeframe=None,
                    timestamp=datetime.fromtimestamp(data.timestamps[-1]),
                    confidence=0.78,
                    signal=SignalType.BUY,
                    metadata={
                        'price': float(current_price),
                        'vwap': float(current_vwap),
                    },
                    description="Price crossed above VWAP",
                ))

            # Price crosses below VWAP (bearish)
            elif prev_price > prev_vwap and current_price < current_vwap:
                results.append(PatternResult(
                    pattern_id=str(uuid.uuid4()),
                    pattern_name="VWAP Bearish Cross",
                    pattern_type=PatternType.TECHNICAL_INDICATOR,
                    symbol="",
                    timeframe=None,
                    timestamp=datetime.fromtimestamp(data.timestamps[-1]),
                    confidence=0.78,
                    signal=SignalType.SELL,
                    metadata={
                        'price': float(current_price),
                        'vwap': float(current_vwap),
                    },
                    description="Price crossed below VWAP",
                ))

        return results

    def validate(self, result: PatternResult) -> bool:
        """Validate VWAP result."""
        return result.pattern_type == PatternType.TECHNICAL_INDICATOR


class MovingAverageCrossPattern(Pattern):
    """Moving Average crossover pattern detection."""

    def __init__(self, fast_period: int = 50, slow_period: int = 200):
        super().__init__()
        self.name = "MA Cross"
        self.description = f"Moving Average Crossover ({fast_period}/{slow_period})"
        self.fast_period = fast_period
        self.slow_period = slow_period

    def detect(self, data: OHLCV) -> List[PatternResult]:
        """Detect MA crossover patterns."""
        results = []

        if len(data.close) < self.slow_period:
            return results

        fast_ma = calculate_sma(data.close, self.fast_period)
        slow_ma = calculate_sma(data.close, self.slow_period)

        if len(fast_ma) < 2 or len(slow_ma) < 2:
            return results

        # Get current and previous values
        current_fast = fast_ma[-1]
        current_slow = slow_ma[-1]
        prev_fast = fast_ma[-2]
        prev_slow = slow_ma[-2]

        # Golden Cross (bullish)
        if prev_fast < prev_slow and current_fast > current_slow:
            results.append(PatternResult(
                pattern_id=str(uuid.uuid4()),
                pattern_name=f"Golden Cross ({self.fast_period}/{self.slow_period})",
                pattern_type=PatternType.TECHNICAL_INDICATOR,
                symbol="",
                timeframe=None,
                timestamp=datetime.fromtimestamp(data.timestamps[-1]),
                confidence=0.85,
                signal=SignalType.STRONG_BUY,
                metadata={
                    'fast_ma': float(current_fast),
                    'slow_ma': float(current_slow),
                },
                description=f"Golden Cross: {self.fast_period} MA crossed above {self.slow_period} MA",
            ))

        # Death Cross (bearish)
        elif prev_fast > prev_slow and current_fast < current_slow:
            results.append(PatternResult(
                pattern_id=str(uuid.uuid4()),
                pattern_name=f"Death Cross ({self.fast_period}/{self.slow_period})",
                pattern_type=PatternType.TECHNICAL_INDICATOR,
                symbol="",
                timeframe=None,
                timestamp=datetime.fromtimestamp(data.timestamps[-1]),
                confidence=0.85,
                signal=SignalType.STRONG_SELL,
                metadata={
                    'fast_ma': float(current_fast),
                    'slow_ma': float(current_slow),
                },
                description=f"Death Cross: {self.fast_period} MA crossed below {self.slow_period} MA",
            ))

        return results

    def validate(self, result: PatternResult) -> bool:
        """Validate MA cross result."""
        return result.pattern_type == PatternType.TECHNICAL_INDICATOR


class ATRPattern(Pattern):
    """Average True Range volatility pattern."""

    def __init__(self, period: int = 14):
        super().__init__()
        self.name = "ATR"
        self.description = "Average True Range volatility pattern"
        self.period = period

    def detect(self, data: OHLCV) -> List[PatternResult]:
        """Detect ATR-based volatility patterns."""
        results = []

        if len(data.close) < self.period + 20:
            return results

        atr = calculate_atr(data.high, data.low, data.close, self.period)
        current_atr = atr[-1]

        # Calculate average ATR over last 20 periods
        avg_atr = np.mean(atr[-20:])

        # High volatility
        if current_atr > avg_atr * 1.5:
            results.append(PatternResult(
                pattern_id=str(uuid.uuid4()),
                pattern_name="High Volatility",
                pattern_type=PatternType.TECHNICAL_INDICATOR,
                symbol="",
                timeframe=None,
                timestamp=datetime.fromtimestamp(data.timestamps[-1]),
                confidence=0.75,
                signal=SignalType.HOLD,
                metadata={
                    'atr': float(current_atr),
                    'avg_atr': float(avg_atr),
                },
                description="ATR indicates high volatility - caution advised",
            ))

        # Low volatility (potential breakout setup)
        elif current_atr < avg_atr * 0.6:
            results.append(PatternResult(
                pattern_id=str(uuid.uuid4()),
                pattern_name="Low Volatility",
                pattern_type=PatternType.TECHNICAL_INDICATOR,
                symbol="",
                timeframe=None,
                timestamp=datetime.fromtimestamp(data.timestamps[-1]),
                confidence=0.70,
                signal=SignalType.HOLD,
                metadata={
                    'atr': float(current_atr),
                    'avg_atr': float(avg_atr),
                },
                description="Low volatility - potential breakout setup",
            ))

        return results

    def validate(self, result: PatternResult) -> bool:
        """Validate ATR result."""
        return result.pattern_type == PatternType.TECHNICAL_INDICATOR


class OBVPattern(Pattern):
    """On-Balance Volume pattern detection."""

    def __init__(self):
        super().__init__()
        self.name = "OBV"
        self.description = "On-Balance Volume divergence pattern"

    def detect(self, data: OHLCV) -> List[PatternResult]:
        """Detect OBV patterns."""
        results = []

        if len(data.close) < 20:
            return results

        obv = calculate_obv(data.close, data.volume)

        # Detect divergences
        price_trend = data.close[-1] - data.close[-20]
        obv_trend = obv[-1] - obv[-20]

        # Bullish divergence: price down but OBV up
        if price_trend < 0 and obv_trend > 0:
            results.append(PatternResult(
                pattern_id=str(uuid.uuid4()),
                pattern_name="OBV Bullish Divergence",
                pattern_type=PatternType.TECHNICAL_INDICATOR,
                symbol="",
                timeframe=None,
                timestamp=datetime.fromtimestamp(data.timestamps[-1]),
                confidence=0.72,
                signal=SignalType.BUY,
                metadata={'obv': float(obv[-1])},
                description="OBV showing bullish divergence",
            ))

        # Bearish divergence: price up but OBV down
        elif price_trend > 0 and obv_trend < 0:
            results.append(PatternResult(
                pattern_id=str(uuid.uuid4()),
                pattern_name="OBV Bearish Divergence",
                pattern_type=PatternType.TECHNICAL_INDICATOR,
                symbol="",
                timeframe=None,
                timestamp=datetime.fromtimestamp(data.timestamps[-1]),
                confidence=0.72,
                signal=SignalType.SELL,
                metadata={'obv': float(obv[-1])},
                description="OBV showing bearish divergence",
            ))

        return results

    def validate(self, result: PatternResult) -> bool:
        """Validate OBV result."""
        return result.pattern_type == PatternType.TECHNICAL_INDICATOR
