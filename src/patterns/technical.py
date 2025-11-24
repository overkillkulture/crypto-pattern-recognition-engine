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
from src.utils.metrics import calculate_rsi, calculate_macd


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


# Placeholder for additional technical patterns to be implemented in Phase 4
class BollingerBandsPattern(Pattern):
    """Bollinger Bands pattern detection. TODO: Implement in Phase 4."""

    def __init__(self):
        super().__init__()
        self.name = "Bollinger Bands"
        self.description = "Bollinger Bands pattern (placeholder)"

    def detect(self, data: OHLCV) -> List[PatternResult]:
        # TODO: Implement in Phase 4
        return []

    def validate(self, result: PatternResult) -> bool:
        return True
