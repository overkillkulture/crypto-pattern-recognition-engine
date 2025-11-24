"""Market analysis implementation."""

from typing import List
import numpy as np
from datetime import datetime
from loguru import logger

from src.core.interfaces import Analyzer
from src.core.types import (
    OHLCV,
    PatternResult,
    AnalysisResult,
    Timeframe,
    SignalType,
)


class MarketAnalyzer(Analyzer):
    """
    Comprehensive market analyzer.

    Combines multiple patterns and indicators to generate overall market analysis.
    """

    def __init__(self):
        logger.info("Market Analyzer initialized")

    async def analyze(
        self,
        symbol: str,
        timeframe: Timeframe,
        data: OHLCV,
        patterns: List[PatternResult],
    ) -> AnalysisResult:
        """
        Perform comprehensive market analysis.

        Args:
            symbol: Trading pair
            timeframe: Analysis timeframe
            data: OHLCV data
            patterns: Detected patterns

        Returns:
            Analysis result with signals and insights
        """
        logger.debug(f"Analyzing {symbol} with {len(patterns)} patterns")

        # Calculate overall signal
        overall_signal, confidence = self._calculate_overall_signal(patterns)

        # Determine trend
        trend = self._determine_trend(data)

        # Calculate volatility
        volatility = self._calculate_volatility(data)

        # Assess volume profile
        volume_profile = self._assess_volume_profile(data)

        # Calculate support and resistance
        support_levels = self._find_support_levels(data)
        resistance_levels = self._find_resistance_levels(data)

        # Calculate risk score
        risk_score = self._calculate_risk_score(volatility, patterns)

        # Generate insights
        insights = self._generate_insights(
            trend, volatility, volume_profile, patterns
        )

        return AnalysisResult(
            symbol=symbol,
            timeframe=timeframe,
            timestamp=datetime.fromtimestamp(data.timestamps[-1]),
            patterns=patterns,
            overall_signal=overall_signal,
            confidence=confidence,
            trend=trend,
            volatility=volatility,
            volume_profile=volume_profile,
            support_levels=support_levels,
            resistance_levels=resistance_levels,
            risk_score=risk_score,
            insights=insights,
            metadata={
                'num_patterns': len(patterns),
                'price': float(data.close[-1]),
            }
        )

    def _calculate_overall_signal(
        self,
        patterns: List[PatternResult]
    ) -> tuple[SignalType, float]:
        """Calculate overall signal from all patterns."""
        if not patterns:
            return SignalType.HOLD, 0.0

        # Weight signals by confidence
        buy_score = sum(
            p.confidence for p in patterns
            if p.signal in [SignalType.BUY, SignalType.STRONG_BUY]
        )

        sell_score = sum(
            p.confidence for p in patterns
            if p.signal in [SignalType.SELL, SignalType.STRONG_SELL]
        )

        total_confidence = buy_score + sell_score

        if total_confidence == 0:
            return SignalType.HOLD, 0.0

        if buy_score > sell_score * 1.5:
            return SignalType.STRONG_BUY, buy_score / total_confidence
        elif buy_score > sell_score:
            return SignalType.BUY, buy_score / total_confidence
        elif sell_score > buy_score * 1.5:
            return SignalType.STRONG_SELL, sell_score / total_confidence
        elif sell_score > buy_score:
            return SignalType.SELL, sell_score / total_confidence
        else:
            return SignalType.HOLD, 0.5

    def _determine_trend(self, data: OHLCV) -> str:
        """Determine market trend."""
        if len(data.close) < 20:
            return "neutral"

        # Simple trend detection using price movement
        recent_prices = data.close[-20:]
        sma = np.mean(recent_prices)
        current_price = data.close[-1]

        if current_price > sma * 1.02:
            return "bullish"
        elif current_price < sma * 0.98:
            return "bearish"
        else:
            return "neutral"

    def _calculate_volatility(self, data: OHLCV) -> float:
        """Calculate market volatility."""
        if len(data.close) < 2:
            return 0.0

        returns = np.diff(data.close) / data.close[:-1]
        return float(np.std(returns))

    def _assess_volume_profile(self, data: OHLCV) -> str:
        """Assess volume profile."""
        if len(data.volume) < 20:
            return "normal"

        avg_volume = np.mean(data.volume[-20:])
        current_volume = data.volume[-1]

        if current_volume > avg_volume * 1.5:
            return "high"
        elif current_volume < avg_volume * 0.5:
            return "low"
        else:
            return "normal"

    def _find_support_levels(self, data: OHLCV, num_levels: int = 3) -> List[float]:
        """Find support levels."""
        if len(data.low) < 50:
            return []

        # Use recent lows as support levels
        recent_lows = data.low[-50:]
        sorted_lows = np.sort(recent_lows)

        # Take the lowest unique values
        support_levels = []
        for low in sorted_lows[:num_levels * 2]:
            if not support_levels or abs(low - support_levels[-1]) / low > 0.01:
                support_levels.append(float(low))
            if len(support_levels) >= num_levels:
                break

        return support_levels

    def _find_resistance_levels(self, data: OHLCV, num_levels: int = 3) -> List[float]:
        """Find resistance levels."""
        if len(data.high) < 50:
            return []

        # Use recent highs as resistance levels
        recent_highs = data.high[-50:]
        sorted_highs = np.sort(recent_highs)[::-1]

        # Take the highest unique values
        resistance_levels = []
        for high in sorted_highs[:num_levels * 2]:
            if not resistance_levels or abs(high - resistance_levels[-1]) / high > 0.01:
                resistance_levels.append(float(high))
            if len(resistance_levels) >= num_levels:
                break

        return resistance_levels

    def _calculate_risk_score(
        self,
        volatility: float,
        patterns: List[PatternResult]
    ) -> float:
        """Calculate risk score (0-1, higher = more risky)."""
        # Base risk on volatility
        risk = min(volatility * 100, 1.0)

        # Adjust for pattern uncertainty
        if patterns:
            avg_confidence = sum(p.confidence for p in patterns) / len(patterns)
            risk += (1 - avg_confidence) * 0.3

        return min(risk, 1.0)

    def _generate_insights(
        self,
        trend: str,
        volatility: float,
        volume_profile: str,
        patterns: List[PatternResult]
    ) -> List[str]:
        """Generate human-readable insights."""
        insights = []

        # Trend insight
        insights.append(f"Market trend is {trend}")

        # Volatility insight
        if volatility > 0.03:
            insights.append("High volatility detected - caution advised")
        elif volatility < 0.01:
            insights.append("Low volatility - market consolidating")

        # Volume insight
        if volume_profile == "high":
            insights.append("Above-average volume indicates strong momentum")
        elif volume_profile == "low":
            insights.append("Low volume - weak conviction")

        # Pattern insights
        if patterns:
            high_conf_patterns = [p for p in patterns if p.confidence > 0.85]
            if high_conf_patterns:
                insights.append(
                    f"{len(high_conf_patterns)} high-confidence patterns detected"
                )

        return insights
