"""Chart pattern detection - comprehensive implementation."""

import uuid
from datetime import datetime
from typing import List, Tuple

import numpy as np
from scipy.signal import argrelextrema

from src.core.interfaces import Pattern
from src.core.types import OHLCV, PatternResult, PatternType, SignalType


class ChartPattern(Pattern):
    """Base class for chart patterns."""

    def __init__(self):
        super().__init__()

    def find_peaks_valleys(
        self, prices: np.ndarray, order: int = 5
    ) -> Tuple[np.ndarray, np.ndarray]:
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
            if (
                data.close[head] > data.close[left_shoulder]
                and data.close[head] > data.close[right_shoulder]
                and abs(data.close[left_shoulder] - data.close[right_shoulder])
                / data.close[head]
                < 0.05
            ):

                # Calculate neckline
                neckline = min(data.close[left_shoulder], data.close[right_shoulder])

                # If price recently broke neckline, it's a confirmed pattern
                current_price = data.close[-1]
                if current_price < neckline * 0.98:
                    results.append(
                        PatternResult(
                            pattern_id=str(uuid.uuid4()),
                            pattern_name="Head and Shoulders",
                            pattern_type=PatternType.CHART_PATTERN,
                            symbol="",
                            timeframe=None,
                            timestamp=datetime.fromtimestamp(data.timestamps[-1]),
                            confidence=0.85,
                            signal=SignalType.STRONG_SELL,
                            metadata={
                                "pattern": "head_and_shoulders",
                                "neckline": float(neckline),
                                "head_price": float(data.close[head]),
                            },
                            description="Head and Shoulders pattern - bearish reversal",
                            target_price=float(
                                neckline - (data.close[head] - neckline)
                            ),
                        )
                    )

        # Check for Inverse Head and Shoulders
        if len(valleys) < 3:
            return results

        for i in range(len(valleys) - 2):
            left_shoulder = valleys[i]
            head = valleys[i + 1]
            right_shoulder = valleys[i + 2]

            # Head should be lower than both shoulders
            if (
                data.close[head] < data.close[left_shoulder]
                and data.close[head] < data.close[right_shoulder]
                and abs(data.close[left_shoulder] - data.close[right_shoulder])
                / data.close[head]
                < 0.05
            ):

                neckline = max(data.close[left_shoulder], data.close[right_shoulder])
                current_price = data.close[-1]

                if current_price > neckline * 1.02:
                    results.append(
                        PatternResult(
                            pattern_id=str(uuid.uuid4()),
                            pattern_name="Inverse Head and Shoulders",
                            pattern_type=PatternType.CHART_PATTERN,
                            symbol="",
                            timeframe=None,
                            timestamp=datetime.fromtimestamp(data.timestamps[-1]),
                            confidence=0.85,
                            signal=SignalType.STRONG_BUY,
                            metadata={
                                "pattern": "inverse_head_and_shoulders",
                                "neckline": float(neckline),
                                "head_price": float(data.close[head]),
                            },
                            description="Inverse Head and Shoulders - bullish reversal",
                            target_price=float(
                                neckline + (neckline - data.close[head])
                            ),
                        )
                    )

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
                results.append(
                    PatternResult(
                        pattern_id=str(uuid.uuid4()),
                        pattern_name="Ascending Triangle Breakout",
                        pattern_type=PatternType.CHART_PATTERN,
                        symbol="",
                        timeframe=None,
                        timestamp=datetime.fromtimestamp(data.timestamps[-1]),
                        confidence=0.78,
                        signal=SignalType.BUY,
                        metadata={"pattern": "ascending_triangle"},
                        description="Ascending Triangle breakout - bullish continuation",
                    )
                )

        # Descending Triangle: falling resistance, flat support
        elif high_trend < -0.001 and abs(low_trend) < 0.001:
            support = np.min(lows)

            if current_price <= support * 1.01:
                results.append(
                    PatternResult(
                        pattern_id=str(uuid.uuid4()),
                        pattern_name="Descending Triangle Breakdown",
                        pattern_type=PatternType.CHART_PATTERN,
                        symbol="",
                        timeframe=None,
                        timestamp=datetime.fromtimestamp(data.timestamps[-1]),
                        confidence=0.78,
                        signal=SignalType.SELL,
                        metadata={"pattern": "descending_triangle"},
                        description="Descending Triangle breakdown - bearish continuation",
                    )
                )

        # Symmetrical Triangle: converging lines
        elif high_trend < -0.001 and low_trend > 0.001:
            results.append(
                PatternResult(
                    pattern_id=str(uuid.uuid4()),
                    pattern_name="Symmetrical Triangle",
                    pattern_type=PatternType.CHART_PATTERN,
                    symbol="",
                    timeframe=None,
                    timestamp=datetime.fromtimestamp(data.timestamps[-1]),
                    confidence=0.70,
                    signal=SignalType.HOLD,
                    metadata={"pattern": "symmetrical_triangle"},
                    description="Symmetrical Triangle - consolidation, breakout pending",
                )
            )

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
                price_diff = (
                    abs(data.close[peak1] - data.close[peak2]) / data.close[peak1]
                )

                if price_diff < 0.03:  # Within 3%
                    # Find valley between peaks
                    valleys_between = [v for v in valleys if peak1 < v < peak2]

                    if valleys_between:
                        valley = valleys_between[0]
                        neckline = data.close[valley]
                        current_price = data.close[-1]

                        # Confirm breakdown below neckline
                        if current_price < neckline * 0.98:
                            results.append(
                                PatternResult(
                                    pattern_id=str(uuid.uuid4()),
                                    pattern_name="Double Top",
                                    pattern_type=PatternType.CHART_PATTERN,
                                    symbol="",
                                    timeframe=None,
                                    timestamp=datetime.fromtimestamp(
                                        data.timestamps[-1]
                                    ),
                                    confidence=0.82,
                                    signal=SignalType.SELL,
                                    metadata={
                                        "pattern": "double_top",
                                        "neckline": float(neckline),
                                        "peak_price": float(data.close[peak1]),
                                    },
                                    description="Double Top - bearish reversal",
                                    target_price=float(
                                        neckline - (data.close[peak1] - neckline)
                                    ),
                                )
                            )

        # Double Bottom
        if len(valleys) >= 2:
            for i in range(len(valleys) - 1):
                valley1 = valleys[i]
                valley2 = valleys[i + 1]

                price_diff = (
                    abs(data.close[valley1] - data.close[valley2]) / data.close[valley1]
                )

                if price_diff < 0.03:
                    peaks_between = [p for p in peaks if valley1 < p < valley2]

                    if peaks_between:
                        peak = peaks_between[0]
                        neckline = data.close[peak]
                        current_price = data.close[-1]

                        if current_price > neckline * 1.02:
                            results.append(
                                PatternResult(
                                    pattern_id=str(uuid.uuid4()),
                                    pattern_name="Double Bottom",
                                    pattern_type=PatternType.CHART_PATTERN,
                                    symbol="",
                                    timeframe=None,
                                    timestamp=datetime.fromtimestamp(
                                        data.timestamps[-1]
                                    ),
                                    confidence=0.82,
                                    signal=SignalType.BUY,
                                    metadata={
                                        "pattern": "double_bottom",
                                        "neckline": float(neckline),
                                        "bottom_price": float(data.close[valley1]),
                                    },
                                    description="Double Bottom - bullish reversal",
                                    target_price=float(
                                        neckline + (neckline - data.close[valley1])
                                    ),
                                )
                            )

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
                    results.append(
                        PatternResult(
                            pattern_id=str(uuid.uuid4()),
                            pattern_name="Bull Flag Breakout",
                            pattern_type=PatternType.CHART_PATTERN,
                            symbol="",
                            timeframe=None,
                            timestamp=datetime.fromtimestamp(data.timestamps[-1]),
                            confidence=0.80,
                            signal=SignalType.BUY,
                            metadata={"pattern": "bull_flag"},
                            description="Bull Flag breakout - bullish continuation",
                            target_price=float(current_price + abs(pole_move)),
                        )
                    )

        # Bear Flag: strong downtrend (pole) + slight upward consolidation (flag)
        elif pole_pct < -0.10:  # At least 10% downtrend
            flag_data = data.close[flag_start:]
            flag_trend = np.polyfit(range(len(flag_data)), flag_data, 1)[0]

            if -0.001 < flag_trend < 0.002:
                current_price = data.close[-1]
                breakdown_level = data.close[pole_end]

                if current_price <= breakdown_level * 1.01:
                    results.append(
                        PatternResult(
                            pattern_id=str(uuid.uuid4()),
                            pattern_name="Bear Flag Breakdown",
                            pattern_type=PatternType.CHART_PATTERN,
                            symbol="",
                            timeframe=None,
                            timestamp=datetime.fromtimestamp(data.timestamps[-1]),
                            confidence=0.80,
                            signal=SignalType.SELL,
                            metadata={"pattern": "bear_flag"},
                            description="Bear Flag breakdown - bearish continuation",
                            target_price=float(current_price - abs(pole_move)),
                        )
                    )

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
                results.append(
                    PatternResult(
                        pattern_id=str(uuid.uuid4()),
                        pattern_name="Rising Wedge Breakdown",
                        pattern_type=PatternType.CHART_PATTERN,
                        symbol="",
                        timeframe=None,
                        timestamp=datetime.fromtimestamp(data.timestamps[-1]),
                        confidence=0.75,
                        signal=SignalType.SELL,
                        metadata={"pattern": "rising_wedge"},
                        description="Rising Wedge breakdown - bearish reversal",
                    )
                )

        # Falling Wedge: both lines falling, bullish reversal
        elif (
            high_trend < -0.001
            and low_trend < -0.001
            and abs(low_trend) > abs(high_trend) * 0.7
        ):
            lower_line = recent_lows[-1]

            if current_price > lower_line * 1.05:
                results.append(
                    PatternResult(
                        pattern_id=str(uuid.uuid4()),
                        pattern_name="Falling Wedge Breakout",
                        pattern_type=PatternType.CHART_PATTERN,
                        symbol="",
                        timeframe=None,
                        timestamp=datetime.fromtimestamp(data.timestamps[-1]),
                        confidence=0.75,
                        signal=SignalType.BUY,
                        metadata={"pattern": "falling_wedge"},
                        description="Falling Wedge breakout - bullish reversal",
                    )
                )

        return results

    def validate(self, result: PatternResult) -> bool:
        """Validate Wedge result."""
        return result.pattern_type == PatternType.CHART_PATTERN


class CupAndHandlePattern(ChartPattern):
    """
    Cup and Handle pattern detection.

    A bullish continuation pattern where price forms a rounded bottom (cup)
    followed by a consolidation (handle) before breaking out.
    """

    def __init__(self, min_length: int = 40):
        super().__init__()
        self.name = "Cup and Handle"
        self.description = "Cup and Handle bullish continuation"
        self.min_length = min_length

    def detect(self, data: OHLCV) -> List[PatternResult]:
        """Detect cup and handle patterns."""
        results = []

        if len(data.close) < self.min_length:
            return results

        closes = data.close
        highs = data.high
        lows = data.low

        # Look for cup and handle in recent data
        window = min(100, len(closes))
        recent_closes = closes[-window:]
        recent_highs = highs[-window:]
        recent_lows = lows[-window:]

        # Find potential cup: U-shaped pattern
        # Need left rim, bottom, right rim
        peaks = argrelextrema(recent_closes, np.greater, order=5)[0]
        valleys = argrelextrema(recent_closes, np.less, order=5)[0]

        if len(peaks) < 2 or len(valleys) < 1:
            return results

        # Check for cup pattern in last 60-80% of window
        cup_start_idx = int(window * 0.2)
        cup_peaks = peaks[peaks >= cup_start_idx]
        cup_valleys = valleys[valleys >= cup_start_idx]

        if len(cup_peaks) < 2 or len(cup_valleys) < 1:
            return results

        # Find a valley between two peaks of similar height
        for i in range(len(cup_peaks) - 1):
            left_peak_idx = cup_peaks[i]
            right_peak_idx = cup_peaks[i + 1]

            # Find valleys between these peaks
            between_valleys = cup_valleys[
                (cup_valleys > left_peak_idx) & (cup_valleys < right_peak_idx)
            ]

            if len(between_valleys) == 0:
                continue

            # Check if peaks are at similar levels (cup rims)
            left_peak = recent_closes[left_peak_idx]
            right_peak = recent_closes[right_peak_idx]
            peak_diff = abs(left_peak - right_peak) / left_peak

            if peak_diff > 0.05:  # Peaks should be within 5%
                continue

            # Check for rounded bottom (multiple valleys)
            valley_idx = between_valleys[len(between_valleys) // 2]
            valley_price = recent_closes[valley_idx]

            # Cup depth should be 12-33% of price
            cup_depth = (left_peak - valley_price) / left_peak
            if cup_depth < 0.12 or cup_depth > 0.33:
                continue

            # Look for handle: small consolidation after right rim
            handle_start = right_peak_idx
            handle_end = len(recent_closes) - 1
            handle_length = handle_end - handle_start

            if handle_length < 5 or handle_length > 20:
                continue

            handle_prices = recent_closes[handle_start : handle_end + 1]
            handle_high = np.max(handle_prices)
            handle_low = np.min(handle_prices)
            handle_depth = (handle_high - handle_low) / handle_high

            # Handle should be shallow (< 12% of cup depth)
            if handle_depth > cup_depth * 0.5:
                continue

            # Check if currently breaking out
            current_price = closes[-1]
            breakout_level = right_peak

            confidence = 0.70
            signal = SignalType.HOLD

            # Breaking out above handle
            if current_price >= breakout_level * 1.01:
                signal = SignalType.BUY
                confidence = 0.85
            # In handle, waiting for breakout
            elif current_price >= breakout_level * 0.98:
                signal = SignalType.HOLD
                confidence = 0.75

            results.append(
                PatternResult(
                    pattern_id=str(uuid.uuid4()),
                    pattern_name="Cup and Handle",
                    pattern_type=PatternType.CHART_PATTERN,
                    symbol="",
                    timeframe=None,
                    timestamp=datetime.fromtimestamp(data.timestamps[-1]),
                    confidence=confidence,
                    signal=signal,
                    entry_price=breakout_level * 1.01,
                    target_price=breakout_level + (breakout_level - valley_price),
                    stop_loss=handle_low * 0.98,
                    metadata={
                        "cup_depth": float(cup_depth),
                        "handle_depth": float(handle_depth),
                        "breakout_level": float(breakout_level),
                        "cup_left_rim": float(left_peak),
                        "cup_right_rim": float(right_peak),
                        "cup_bottom": float(valley_price),
                    },
                    description=f"Cup and Handle pattern - breakout at ${breakout_level:.2f}",
                )
            )

        return results

    def validate(self, result: PatternResult) -> bool:
        """Validate Cup and Handle result."""
        return result.pattern_type == PatternType.CHART_PATTERN


class RectanglePattern(ChartPattern):
    """
    Rectangle pattern detection (consolidation range).

    A continuation pattern where price consolidates between support and resistance
    before breaking out in the direction of the prior trend.
    """

    def __init__(self, min_length: int = 20, max_width_pct: float = 0.05):
        super().__init__()
        self.name = "Rectangle"
        self.description = "Rectangle consolidation pattern"
        self.min_length = min_length
        self.max_width_pct = max_width_pct

    def detect(self, data: OHLCV) -> List[PatternResult]:
        """Detect rectangle patterns."""
        results = []

        if len(data.close) < self.min_length:
            return results

        closes = data.close
        highs = data.high
        lows = data.low

        # Look for rectangle in recent data
        for lookback in [30, 40, 50]:
            if len(closes) < lookback:
                continue

            recent_closes = closes[-lookback:]
            recent_highs = highs[-lookback:]
            recent_lows = lows[-lookback:]

            # Find resistance and support levels
            resistance = np.max(recent_highs[-20:])
            support = np.min(recent_lows[-20:])
            range_width = (resistance - support) / support

            # Rectangle should have defined but tight range
            if range_width > self.max_width_pct * 3:  # Up to 15% range
                continue

            # Count touches of support and resistance
            resistance_touches = np.sum(recent_highs >= resistance * 0.99)
            support_touches = np.sum(recent_lows <= support * 1.01)

            # Need at least 2 touches of each level
            if resistance_touches < 2 or support_touches < 2:
                continue

            # Current price position
            current_price = closes[-1]
            price_position = (current_price - support) / (resistance - support)

            # Determine trend before rectangle (for continuation direction)
            pre_rect_closes = (
                closes[-lookback - 20 : -lookback]
                if len(closes) >= lookback + 20
                else closes[: lookback // 2]
            )
            trend_direction = (
                "up" if pre_rect_closes[-1] > pre_rect_closes[0] else "down"
            )

            confidence = 0.70
            signal = SignalType.HOLD

            # Breaking above resistance (bullish breakout)
            if current_price >= resistance * 1.005:
                signal = SignalType.BUY
                confidence = 0.85 if trend_direction == "up" else 0.75
            # Breaking below support (bearish breakout)
            elif current_price <= support * 0.995:
                signal = SignalType.SELL
                confidence = 0.85 if trend_direction == "down" else 0.75
            # Near resistance
            elif price_position > 0.85:
                signal = SignalType.HOLD
                confidence = 0.75
            # Near support
            elif price_position < 0.15:
                signal = SignalType.HOLD
                confidence = 0.75

            # Calculate target based on range height
            range_height = resistance - support
            target_price = (
                resistance + range_height
                if signal == SignalType.BUY
                else support - range_height
            )
            stop_loss = (
                support * 0.98 if signal == SignalType.BUY else resistance * 1.02
            )

            results.append(
                PatternResult(
                    pattern_id=str(uuid.uuid4()),
                    pattern_name="Rectangle Consolidation",
                    pattern_type=PatternType.CHART_PATTERN,
                    symbol="",
                    timeframe=None,
                    timestamp=datetime.fromtimestamp(data.timestamps[-1]),
                    confidence=confidence,
                    signal=signal,
                    entry_price=(
                        resistance * 1.005
                        if trend_direction == "up"
                        else support * 0.995
                    ),
                    target_price=target_price,
                    stop_loss=stop_loss,
                    metadata={
                        "resistance": float(resistance),
                        "support": float(support),
                        "range_width_pct": float(range_width * 100),
                        "resistance_touches": int(resistance_touches),
                        "support_touches": int(support_touches),
                        "prior_trend": trend_direction,
                        "price_position_pct": float(price_position * 100),
                    },
                    description=f"Rectangle pattern: ${support:.2f} - ${resistance:.2f} range",
                )
            )

            break  # Only report one rectangle

        return results

    def validate(self, result: PatternResult) -> bool:
        """Validate Rectangle result."""
        return result.pattern_type == PatternType.CHART_PATTERN


class DiamondPattern(ChartPattern):
    """
    Diamond pattern detection.

    A reversal pattern that forms when price expands and then contracts,
    creating a diamond shape. Often appears at market tops.
    """

    def __init__(self, min_length: int = 30):
        super().__init__()
        self.name = "Diamond"
        self.description = "Diamond reversal pattern"
        self.min_length = min_length

    def detect(self, data: OHLCV) -> List[PatternResult]:
        """Detect diamond patterns."""
        results = []

        if len(data.close) < self.min_length:
            return results

        closes = data.close
        highs = data.high
        lows = data.low

        # Look for diamond in recent data
        window = min(80, len(closes))
        recent_closes = closes[-window:]
        recent_highs = highs[-window:]
        recent_lows = lows[-window:]

        # Find peaks and valleys
        peaks = argrelextrema(recent_closes, np.greater, order=3)[0]
        valleys = argrelextrema(recent_closes, np.less, order=3)[0]

        if len(peaks) < 4 or len(valleys) < 4:
            return results

        # Look for diamond in last 50% of window
        diamond_start = int(window * 0.5)
        recent_peaks = peaks[peaks >= diamond_start]
        recent_valleys = valleys[valleys >= diamond_start]

        if len(recent_peaks) < 3 or len(recent_valleys) < 3:
            return results

        # Check for expanding then contracting pattern
        # First half: expanding (widening peaks and valleys)
        # Second half: contracting (narrowing peaks and valleys)

        for i in range(len(recent_peaks) - 2):
            p1, p2, p3 = recent_peaks[i : i + 3]

            # Find corresponding valleys
            v_between_12 = recent_valleys[(recent_valleys > p1) & (recent_valleys < p2)]
            v_between_23 = recent_valleys[(recent_valleys > p2) & (recent_valleys < p3)]

            if len(v_between_12) == 0 or len(v_between_23) == 0:
                continue

            v1 = v_between_12[0]
            v2 = v_between_23[0]

            # Check if pattern forms diamond shape
            # Peak 2 should be highest, valleys should show expansion then contraction
            peak1_price = recent_closes[p1]
            peak2_price = recent_closes[p2]
            peak3_price = recent_closes[p3]
            valley1_price = recent_closes[v1]
            valley2_price = recent_closes[v2]

            # Peak 2 should be highest (top of diamond)
            if peak2_price <= peak1_price or peak2_price <= peak3_price:
                continue

            # Check for expansion and contraction
            range1 = peak1_price - valley1_price
            range2 = peak2_price - valley2_price

            if range2 <= range1:  # Should expand
                continue

            # Diamond completion (contracting)
            if peak3_price < peak2_price and p3 < len(recent_closes) - 5:
                current_price = closes[-1]

                # Determine trend before diamond
                pre_diamond_trend = "up" if closes[-window] < peak2_price else "down"

                confidence = 0.75
                signal = SignalType.HOLD

                # Breaking down from diamond (bearish)
                if current_price < valley2_price * 0.99:
                    signal = SignalType.SELL
                    confidence = 0.82
                # Breaking up from diamond (bullish, less common)
                elif current_price > peak2_price * 1.01:
                    signal = SignalType.BUY
                    confidence = 0.70

                diamond_height = peak2_price - min(valley1_price, valley2_price)
                target_price = (
                    valley2_price - diamond_height
                    if signal == SignalType.SELL
                    else peak2_price + diamond_height
                )

                results.append(
                    PatternResult(
                        pattern_id=str(uuid.uuid4()),
                        pattern_name="Diamond Pattern",
                        pattern_type=PatternType.CHART_PATTERN,
                        symbol="",
                        timeframe=None,
                        timestamp=datetime.fromtimestamp(data.timestamps[-1]),
                        confidence=confidence,
                        signal=signal,
                        entry_price=(
                            valley2_price * 0.99
                            if signal == SignalType.SELL
                            else peak2_price * 1.01
                        ),
                        target_price=target_price,
                        stop_loss=(
                            peak2_price * 1.02
                            if signal == SignalType.SELL
                            else valley2_price * 0.98
                        ),
                        metadata={
                            "peak1": float(peak1_price),
                            "peak2": float(peak2_price),
                            "peak3": float(peak3_price),
                            "valley1": float(valley1_price),
                            "valley2": float(valley2_price),
                            "diamond_height": float(diamond_height),
                            "prior_trend": pre_diamond_trend,
                        },
                        description=f"Diamond reversal pattern - typical bearish reversal",
                    )
                )

        return results

    def validate(self, result: PatternResult) -> bool:
        """Validate Diamond result."""
        return result.pattern_type == PatternType.CHART_PATTERN
