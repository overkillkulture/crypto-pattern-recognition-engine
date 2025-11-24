"""Chart pattern detection - comprehensive implementation."""

from typing import List, Tuple, Optional
from datetime import datetime
import uuid
import numpy as np
from loguru import logger
from scipy.signal import argrelextrema

from src.core.interfaces import Pattern
from src.core.types import (
    OHLCV,
    PatternResult,
    PatternType,
    SignalType,
)


class ChartPattern(Pattern):
    """Base class for chart patterns."""

    def __init__(self):
        super().__init__()

    def find_peaks_valleys(self, prices: np.ndarray, order: int = 5) -> Tuple[np.ndarray, np.ndarray]:
        """Find peaks and valleys in price data."""
        peaks = argrelextrema(prices, np.greater, order=order)[0]
        valleys = argrelextrema(prices, np.less, order=order)[0]
        return peaks, valleys


class HeadAndShouldersPattern(ChartPattern):
    """Head and Shoulders / Inverse Head and Shoulders pattern detection."""

    def __init__(self):
        super().__init__()
        self.name = "Head and Shoulders"
        self.description = "Head and Shoulders chart pattern"

    def detect(self, data: OHLCV) -> List[PatternResult]:
        """Detect Head and Shoulders patterns."""
        results = []

        if len(data.close) < 50:
            return results

        peaks, valleys = self.find_peaks_valleys(data.close, order=10)

        # Need at least 3 peaks for H&S
        if len(peaks) < 3:
            return results

        # Check last 3 peaks for H&S pattern
        for i in range(len(peaks) - 2):
            left_shoulder = peaks[i]
            head = peaks[i + 1]
            right_shoulder = peaks[i + 2]

            # Head should be higher than both shoulders
            if (data.close[head] > data.close[left_shoulder] and
                data.close[head] > data.close[right_shoulder] and
                abs(data.close[left_shoulder] - data.close[right_shoulder]) / data.close[head] < 0.05):

                # Calculate neckline
                neckline = min(data.close[left_shoulder], data.close[right_shoulder])

                # If price recently broke neckline, it's a confirmed pattern
                current_price = data.close[-1]
                if current_price < neckline * 0.98:
                    results.append(PatternResult(
                        pattern_id=str(uuid.uuid4()),
                        pattern_name="Head and Shoulders",
                        pattern_type=PatternType.CHART_PATTERN,
                        symbol="",
                        timeframe=None,
                        timestamp=datetime.fromtimestamp(data.timestamps[-1]),
                        confidence=0.85,
                        signal=SignalType.STRONG_SELL,
                        metadata={
                            'pattern': 'head_and_shoulders',
                            'neckline': float(neckline),
                            'head_price': float(data.close[head]),
                        },
                        description="Head and Shoulders pattern - bearish reversal",
                        target_price=float(neckline - (data.close[head] - neckline)),
                    ))

        # Check for Inverse Head and Shoulders
        if len(valleys) < 3:
            return results

        for i in range(len(valleys) - 2):
            left_shoulder = valleys[i]
            head = valleys[i + 1]
            right_shoulder = valleys[i + 2]

            # Head should be lower than both shoulders
            if (data.close[head] < data.close[left_shoulder] and
                data.close[head] < data.close[right_shoulder] and
                abs(data.close[left_shoulder] - data.close[right_shoulder]) / data.close[head] < 0.05):

                neckline = max(data.close[left_shoulder], data.close[right_shoulder])
                current_price = data.close[-1]

                if current_price > neckline * 1.02:
                    results.append(PatternResult(
                        pattern_id=str(uuid.uuid4()),
                        pattern_name="Inverse Head and Shoulders",
                        pattern_type=PatternType.CHART_PATTERN,
                        symbol="",
                        timeframe=None,
                        timestamp=datetime.fromtimestamp(data.timestamps[-1]),
                        confidence=0.85,
                        signal=SignalType.STRONG_BUY,
                        metadata={
                            'pattern': 'inverse_head_and_shoulders',
                            'neckline': float(neckline),
                            'head_price': float(data.close[head]),
                        },
                        description="Inverse Head and Shoulders - bullish reversal",
                        target_price=float(neckline + (neckline - data.close[head])),
                    ))

        return results

    def validate(self, result: PatternResult) -> bool:
        """Validate Head and Shoulders result."""
        return result.pattern_type == PatternType.CHART_PATTERN


class TrianglePattern(ChartPattern):
    """Triangle pattern detection (Ascending, Descending, Symmetrical)."""

    def __init__(self):
        super().__init__()
        self.name = "Triangle"
        self.description = "Triangle consolidation pattern"

    def detect(self, data: OHLCV) -> List[PatternResult]:
        """Detect Triangle patterns."""
        results = []

        if len(data.close) < 30:
            return results

        # Get recent highs and lows
        recent_data = data.close[-30:]
        highs = data.high[-30:]
        lows = data.low[-30:]

        # Find trend of highs and lows
        high_trend = np.polyfit(range(len(highs)), highs, 1)[0]
        low_trend = np.polyfit(range(len(lows)), lows, 1)[0]

        current_price = data.close[-1]

        # Ascending Triangle: flat resistance, rising support
        if abs(high_trend) < 0.001 and low_trend > 0.001:
            resistance = np.max(highs)

            if current_price >= resistance * 0.99:
                results.append(PatternResult(
                    pattern_id=str(uuid.uuid4()),
                    pattern_name="Ascending Triangle Breakout",
                    pattern_type=PatternType.CHART_PATTERN,
                    symbol="",
                    timeframe=None,
                    timestamp=datetime.fromtimestamp(data.timestamps[-1]),
                    confidence=0.78,
                    signal=SignalType.BUY,
                    metadata={'pattern': 'ascending_triangle'},
                    description="Ascending Triangle breakout - bullish continuation",
                ))

        # Descending Triangle: falling resistance, flat support
        elif high_trend < -0.001 and abs(low_trend) < 0.001:
            support = np.min(lows)

            if current_price <= support * 1.01:
                results.append(PatternResult(
                    pattern_id=str(uuid.uuid4()),
                    pattern_name="Descending Triangle Breakdown",
                    pattern_type=PatternType.CHART_PATTERN,
                    symbol="",
                    timeframe=None,
                    timestamp=datetime.fromtimestamp(data.timestamps[-1]),
                    confidence=0.78,
                    signal=SignalType.SELL,
                    metadata={'pattern': 'descending_triangle'},
                    description="Descending Triangle breakdown - bearish continuation",
                ))

        # Symmetrical Triangle: converging lines
        elif high_trend < -0.001 and low_trend > 0.001:
            results.append(PatternResult(
                pattern_id=str(uuid.uuid4()),
                pattern_name="Symmetrical Triangle",
                pattern_type=PatternType.CHART_PATTERN,
                symbol="",
                timeframe=None,
                timestamp=datetime.fromtimestamp(data.timestamps[-1]),
                confidence=0.70,
                signal=SignalType.HOLD,
                metadata={'pattern': 'symmetrical_triangle'},
                description="Symmetrical Triangle - consolidation, breakout pending",
            ))

        return results

    def validate(self, result: PatternResult) -> bool:
        """Validate Triangle result."""
        return result.pattern_type == PatternType.CHART_PATTERN


class DoubleTopBottomPattern(ChartPattern):
    """Double Top and Double Bottom pattern detection."""

    def __init__(self):
        super().__init__()
        self.name = "Double Top/Bottom"
        self.description = "Double Top/Bottom reversal pattern"

    def detect(self, data: OHLCV) -> List[PatternResult]:
        """Detect Double Top/Bottom patterns."""
        results = []

        if len(data.close) < 40:
            return results

        peaks, valleys = self.find_peaks_valleys(data.close, order=8)

        # Double Top
        if len(peaks) >= 2:
            for i in range(len(peaks) - 1):
                peak1 = peaks[i]
                peak2 = peaks[i + 1]

                # Peaks should be at similar levels
                price_diff = abs(data.close[peak1] - data.close[peak2]) / data.close[peak1]

                if price_diff < 0.03:  # Within 3%
                    # Find valley between peaks
                    valleys_between = [v for v in valleys if peak1 < v < peak2]

                    if valleys_between:
                        valley = valleys_between[0]
                        neckline = data.close[valley]
                        current_price = data.close[-1]

                        # Confirm breakdown below neckline
                        if current_price < neckline * 0.98:
                            results.append(PatternResult(
                                pattern_id=str(uuid.uuid4()),
                                pattern_name="Double Top",
                                pattern_type=PatternType.CHART_PATTERN,
                                symbol="",
                                timeframe=None,
                                timestamp=datetime.fromtimestamp(data.timestamps[-1]),
                                confidence=0.82,
                                signal=SignalType.SELL,
                                metadata={
                                    'pattern': 'double_top',
                                    'neckline': float(neckline),
                                    'peak_price': float(data.close[peak1]),
                                },
                                description="Double Top - bearish reversal",
                                target_price=float(neckline - (data.close[peak1] - neckline)),
                            ))

        # Double Bottom
        if len(valleys) >= 2:
            for i in range(len(valleys) - 1):
                valley1 = valleys[i]
                valley2 = valleys[i + 1]

                price_diff = abs(data.close[valley1] - data.close[valley2]) / data.close[valley1]

                if price_diff < 0.03:
                    peaks_between = [p for p in peaks if valley1 < p < valley2]

                    if peaks_between:
                        peak = peaks_between[0]
                        neckline = data.close[peak]
                        current_price = data.close[-1]

                        if current_price > neckline * 1.02:
                            results.append(PatternResult(
                                pattern_id=str(uuid.uuid4()),
                                pattern_name="Double Bottom",
                                pattern_type=PatternType.CHART_PATTERN,
                                symbol="",
                                timeframe=None,
                                timestamp=datetime.fromtimestamp(data.timestamps[-1]),
                                confidence=0.82,
                                signal=SignalType.BUY,
                                metadata={
                                    'pattern': 'double_bottom',
                                    'neckline': float(neckline),
                                    'bottom_price': float(data.close[valley1]),
                                },
                                description="Double Bottom - bullish reversal",
                                target_price=float(neckline + (neckline - data.close[valley1])),
                            ))

        return results

    def validate(self, result: PatternResult) -> bool:
        """Validate Double Top/Bottom result."""
        return result.pattern_type == PatternType.CHART_PATTERN


class FlagPattern(ChartPattern):
    """Bull Flag and Bear Flag pattern detection."""

    def __init__(self):
        super().__init__()
        self.name = "Flag"
        self.description = "Bull/Bear Flag continuation pattern"

    def detect(self, data: OHLCV) -> List[PatternResult]:
        """Detect Flag patterns."""
        results = []

        if len(data.close) < 30:
            return results

        # Look for strong trend followed by consolidation
        pole_start = -30
        pole_end = -10
        flag_start = -10

        pole_move = data.close[pole_end] - data.close[pole_start]
        pole_pct = pole_move / data.close[pole_start]

        # Bull Flag: strong uptrend (pole) + slight downward consolidation (flag)
        if pole_pct > 0.10:  # At least 10% uptrend
            flag_data = data.close[flag_start:]
            flag_trend = np.polyfit(range(len(flag_data)), flag_data, 1)[0]

            # Flag should be slightly declining or flat
            if -0.002 < flag_trend < 0.001:
                current_price = data.close[-1]
                breakout_level = data.close[pole_end]

                if current_price >= breakout_level * 0.99:
                    results.append(PatternResult(
                        pattern_id=str(uuid.uuid4()),
                        pattern_name="Bull Flag Breakout",
                        pattern_type=PatternType.CHART_PATTERN,
                        symbol="",
                        timeframe=None,
                        timestamp=datetime.fromtimestamp(data.timestamps[-1]),
                        confidence=0.80,
                        signal=SignalType.BUY,
                        metadata={'pattern': 'bull_flag'},
                        description="Bull Flag breakout - bullish continuation",
                        target_price=float(current_price + abs(pole_move)),
                    ))

        # Bear Flag: strong downtrend (pole) + slight upward consolidation (flag)
        elif pole_pct < -0.10:  # At least 10% downtrend
            flag_data = data.close[flag_start:]
            flag_trend = np.polyfit(range(len(flag_data)), flag_data, 1)[0]

            if -0.001 < flag_trend < 0.002:
                current_price = data.close[-1]
                breakdown_level = data.close[pole_end]

                if current_price <= breakdown_level * 1.01:
                    results.append(PatternResult(
                        pattern_id=str(uuid.uuid4()),
                        pattern_name="Bear Flag Breakdown",
                        pattern_type=PatternType.CHART_PATTERN,
                        symbol="",
                        timeframe=None,
                        timestamp=datetime.fromtimestamp(data.timestamps[-1]),
                        confidence=0.80,
                        signal=SignalType.SELL,
                        metadata={'pattern': 'bear_flag'},
                        description="Bear Flag breakdown - bearish continuation",
                        target_price=float(current_price - abs(pole_move)),
                    ))

        return results

    def validate(self, result: PatternResult) -> bool:
        """Validate Flag result."""
        return result.pattern_type == PatternType.CHART_PATTERN


class WedgePattern(ChartPattern):
    """Rising and Falling Wedge pattern detection."""

    def __init__(self):
        super().__init__()
        self.name = "Wedge"
        self.description = "Rising/Falling Wedge reversal pattern"

    def detect(self, data: OHLCV) -> List[PatternResult]:
        """Detect Wedge patterns."""
        results = []

        if len(data.close) < 30:
            return results

        recent_highs = data.high[-30:]
        recent_lows = data.low[-30:]

        high_trend = np.polyfit(range(len(recent_highs)), recent_highs, 1)[0]
        low_trend = np.polyfit(range(len(recent_lows)), recent_lows, 1)[0]

        current_price = data.close[-1]

        # Rising Wedge: both lines rising, bearish reversal
        if high_trend > 0.001 and low_trend > 0.001 and low_trend > high_trend * 0.7:
            # Price near upper boundary
            upper_line = recent_highs[-1]

            if current_price < upper_line * 0.95:
                results.append(PatternResult(
                    pattern_id=str(uuid.uuid4()),
                    pattern_name="Rising Wedge Breakdown",
                    pattern_type=PatternType.CHART_PATTERN,
                    symbol="",
                    timeframe=None,
                    timestamp=datetime.fromtimestamp(data.timestamps[-1]),
                    confidence=0.75,
                    signal=SignalType.SELL,
                    metadata={'pattern': 'rising_wedge'},
                    description="Rising Wedge breakdown - bearish reversal",
                ))

        # Falling Wedge: both lines falling, bullish reversal
        elif high_trend < -0.001 and low_trend < -0.001 and abs(low_trend) > abs(high_trend) * 0.7:
            lower_line = recent_lows[-1]

            if current_price > lower_line * 1.05:
                results.append(PatternResult(
                    pattern_id=str(uuid.uuid4()),
                    pattern_name="Falling Wedge Breakout",
                    pattern_type=PatternType.CHART_PATTERN,
                    symbol="",
                    timeframe=None,
                    timestamp=datetime.fromtimestamp(data.timestamps[-1]),
                    confidence=0.75,
                    signal=SignalType.BUY,
                    metadata={'pattern': 'falling_wedge'},
                    description="Falling Wedge breakout - bullish reversal",
                ))

        return results

    def validate(self, result: PatternResult) -> bool:
        """Validate Wedge result."""
        return result.pattern_type == PatternType.CHART_PATTERN
