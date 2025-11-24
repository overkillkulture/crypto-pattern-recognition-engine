"""Pattern combination strategies for stronger signals."""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import numpy as np

from src.core.types import PatternResult, SignalType, PatternType


@dataclass
class CombinedSignal:
    """Result of pattern combination analysis."""

    signal: SignalType
    confidence: float
    contributing_patterns: List[PatternResult]
    strategy_name: str
    reasoning: str
    metadata: Dict[str, Any]


class PatternCombinationStrategy:
    """Base class for pattern combination strategies."""

    def __init__(self, name: str):
        self.name = name

    def combine(self, patterns: List[PatternResult]) -> Optional[CombinedSignal]:
        """
        Combine patterns into a single signal.

        Args:
            patterns: List of detected patterns

        Returns:
            Combined signal or None if no signal
        """
        raise NotImplementedError


class ConsensusStrategy(PatternCombinationStrategy):
    """
    Combine patterns using consensus voting.

    Requires a minimum number of patterns to agree on direction.
    """

    def __init__(
        self,
        min_patterns: int = 3,
        min_confidence: float = 0.70,
        consensus_threshold: float = 0.60,
    ):
        """
        Initialize consensus strategy.

        Args:
            min_patterns: Minimum number of patterns required
            min_confidence: Minimum confidence for each pattern
            consensus_threshold: Minimum % of patterns that must agree
        """
        super().__init__("Consensus Strategy")
        self.min_patterns = min_patterns
        self.min_confidence = min_confidence
        self.consensus_threshold = consensus_threshold

    def combine(self, patterns: List[PatternResult]) -> Optional[CombinedSignal]:
        """Combine patterns using consensus voting."""
        if len(patterns) < self.min_patterns:
            return None

        # Filter by confidence
        confident_patterns = [
            p for p in patterns if p.confidence >= self.min_confidence
        ]

        if len(confident_patterns) < self.min_patterns:
            return None

        # Count votes
        buy_votes = [p for p in confident_patterns if p.signal == SignalType.BUY]
        sell_votes = [p for p in confident_patterns if p.signal == SignalType.SELL]
        neutral_votes = [p for p in confident_patterns if p.signal == SignalType.NEUTRAL]

        total_votes = len(confident_patterns)

        # Check consensus
        buy_ratio = len(buy_votes) / total_votes
        sell_ratio = len(sell_votes) / total_votes

        if buy_ratio >= self.consensus_threshold:
            # Calculate combined confidence
            confidence = np.mean([p.confidence for p in buy_votes])

            return CombinedSignal(
                signal=SignalType.BUY,
                confidence=confidence,
                contributing_patterns=buy_votes,
                strategy_name=self.name,
                reasoning=f"{len(buy_votes)}/{total_votes} patterns ({buy_ratio:.1%}) agree on BUY",
                metadata={
                    'buy_votes': len(buy_votes),
                    'sell_votes': len(sell_votes),
                    'neutral_votes': len(neutral_votes),
                    'consensus_ratio': buy_ratio,
                },
            )

        elif sell_ratio >= self.consensus_threshold:
            confidence = np.mean([p.confidence for p in sell_votes])

            return CombinedSignal(
                signal=SignalType.SELL,
                confidence=confidence,
                contributing_patterns=sell_votes,
                strategy_name=self.name,
                reasoning=f"{len(sell_votes)}/{total_votes} patterns ({sell_ratio:.1%}) agree on SELL",
                metadata={
                    'buy_votes': len(buy_votes),
                    'sell_votes': len(sell_votes),
                    'neutral_votes': len(neutral_votes),
                    'consensus_ratio': sell_ratio,
                },
            )

        return None


class WeightedStrategy(PatternCombinationStrategy):
    """
    Combine patterns using weighted scoring.

    Different pattern types have different weights.
    """

    def __init__(
        self,
        weights: Optional[Dict[PatternType, float]] = None,
        min_score: float = 0.70,
    ):
        """
        Initialize weighted strategy.

        Args:
            weights: Weight for each pattern type
            min_score: Minimum weighted score to generate signal
        """
        super().__init__("Weighted Strategy")

        # Default weights
        self.weights = weights or {
            PatternType.CHART_PATTERN: 1.5,  # Chart patterns most reliable
            PatternType.TECHNICAL_INDICATOR: 1.0,
            PatternType.CANDLESTICK_PATTERN: 0.8,
        }
        self.min_score = min_score

    def combine(self, patterns: List[PatternResult]) -> Optional[CombinedSignal]:
        """Combine patterns using weighted scores."""
        if not patterns:
            return None

        buy_score = 0.0
        sell_score = 0.0
        buy_patterns = []
        sell_patterns = []

        # Calculate weighted scores
        for pattern in patterns:
            weight = self.weights.get(pattern.pattern_type, 1.0)
            weighted_confidence = pattern.confidence * weight

            if pattern.signal == SignalType.BUY:
                buy_score += weighted_confidence
                buy_patterns.append(pattern)
            elif pattern.signal == SignalType.SELL:
                sell_score += weighted_confidence
                sell_patterns.append(pattern)

        # Normalize scores
        total_weight = sum(
            self.weights.get(p.pattern_type, 1.0) for p in patterns
        )

        if total_weight > 0:
            buy_score /= total_weight
            sell_score /= total_weight

        # Determine signal
        if buy_score >= self.min_score and buy_score > sell_score:
            return CombinedSignal(
                signal=SignalType.BUY,
                confidence=buy_score,
                contributing_patterns=buy_patterns,
                strategy_name=self.name,
                reasoning=f"Weighted BUY score: {buy_score:.2f} > threshold {self.min_score:.2f}",
                metadata={
                    'buy_score': buy_score,
                    'sell_score': sell_score,
                    'total_patterns': len(patterns),
                },
            )

        elif sell_score >= self.min_score and sell_score > buy_score:
            return CombinedSignal(
                signal=SignalType.SELL,
                confidence=sell_score,
                contributing_patterns=sell_patterns,
                strategy_name=self.name,
                reasoning=f"Weighted SELL score: {sell_score:.2f} > threshold {self.min_score:.2f}",
                metadata={
                    'buy_score': buy_score,
                    'sell_score': sell_score,
                    'total_patterns': len(patterns),
                },
            )

        return None


class ConfirmationStrategy(PatternCombinationStrategy):
    """
    Require specific pattern types to confirm signal.

    Example: Require both technical indicator AND chart pattern.
    """

    def __init__(
        self,
        required_types: List[PatternType],
        min_confidence: float = 0.70,
    ):
        """
        Initialize confirmation strategy.

        Args:
            required_types: Pattern types that must be present
            min_confidence: Minimum confidence for each pattern
        """
        super().__init__("Confirmation Strategy")
        self.required_types = required_types
        self.min_confidence = min_confidence

    def combine(self, patterns: List[PatternResult]) -> Optional[CombinedSignal]:
        """Combine patterns requiring confirmation from specific types."""
        if not patterns:
            return None

        # Group patterns by type
        by_type: Dict[PatternType, List[PatternResult]] = {}
        for pattern in patterns:
            if pattern.confidence >= self.min_confidence:
                if pattern.pattern_type not in by_type:
                    by_type[pattern.pattern_type] = []
                by_type[pattern.pattern_type].append(pattern)

        # Check if all required types are present
        for required_type in self.required_types:
            if required_type not in by_type:
                return None

        # Get signals from each required type
        buy_counts = {ptype: 0 for ptype in self.required_types}
        sell_counts = {ptype: 0 for ptype in self.required_types}

        for ptype in self.required_types:
            for pattern in by_type[ptype]:
                if pattern.signal == SignalType.BUY:
                    buy_counts[ptype] += 1
                elif pattern.signal == SignalType.SELL:
                    sell_counts[ptype] += 1

        # Check if all types agree on BUY
        if all(buy_counts[ptype] > 0 for ptype in self.required_types):
            contributing = []
            for ptype in self.required_types:
                contributing.extend(
                    [p for p in by_type[ptype] if p.signal == SignalType.BUY]
                )

            confidence = np.mean([p.confidence for p in contributing])

            return CombinedSignal(
                signal=SignalType.BUY,
                confidence=confidence,
                contributing_patterns=contributing,
                strategy_name=self.name,
                reasoning=f"All required pattern types confirm BUY: {[t.value for t in self.required_types]}",
                metadata={
                    'required_types': [t.value for t in self.required_types],
                    'patterns_per_type': {t.value: len(by_type[t]) for t in self.required_types},
                },
            )

        # Check if all types agree on SELL
        if all(sell_counts[ptype] > 0 for ptype in self.required_types):
            contributing = []
            for ptype in self.required_types:
                contributing.extend(
                    [p for p in by_type[ptype] if p.signal == SignalType.SELL]
                )

            confidence = np.mean([p.confidence for p in contributing])

            return CombinedSignal(
                signal=SignalType.SELL,
                confidence=confidence,
                contributing_patterns=contributing,
                strategy_name=self.name,
                reasoning=f"All required pattern types confirm SELL: {[t.value for t in self.required_types]}",
                metadata={
                    'required_types': [t.value for t in self.required_types],
                    'patterns_per_type': {t.value: len(by_type[t]) for t in self.required_types},
                },
            )

        return None


class TimeframeConfluenceStrategy(PatternCombinationStrategy):
    """
    Combine patterns across multiple timeframes.

    Stronger signals when multiple timeframes align.
    """

    def __init__(
        self,
        min_timeframes: int = 2,
        min_confidence: float = 0.70,
    ):
        """
        Initialize timeframe confluence strategy.

        Args:
            min_timeframes: Minimum number of timeframes that must align
            min_confidence: Minimum confidence for each pattern
        """
        super().__init__("Timeframe Confluence Strategy")
        self.min_timeframes = min_timeframes
        self.min_confidence = min_confidence

    def combine(self, patterns: List[PatternResult]) -> Optional[CombinedSignal]:
        """Combine patterns checking for timeframe confluence."""
        if not patterns:
            return None

        # Group patterns by timeframe
        by_timeframe: Dict[str, List[PatternResult]] = {}
        for pattern in patterns:
            if pattern.confidence >= self.min_confidence and pattern.timeframe:
                tf = pattern.timeframe.value
                if tf not in by_timeframe:
                    by_timeframe[tf] = []
                by_timeframe[tf].append(pattern)

        if len(by_timeframe) < self.min_timeframes:
            return None

        # Count buy/sell per timeframe
        buy_timeframes = []
        sell_timeframes = []

        for tf, tf_patterns in by_timeframe.items():
            buy_count = sum(1 for p in tf_patterns if p.signal == SignalType.BUY)
            sell_count = sum(1 for p in tf_patterns if p.signal == SignalType.SELL)

            if buy_count > sell_count:
                buy_timeframes.append(tf)
            elif sell_count > buy_count:
                sell_timeframes.append(tf)

        # Check if minimum timeframes align
        if len(buy_timeframes) >= self.min_timeframes:
            contributing = []
            for tf in buy_timeframes:
                contributing.extend(
                    [p for p in by_timeframe[tf] if p.signal == SignalType.BUY]
                )

            confidence = np.mean([p.confidence for p in contributing])

            return CombinedSignal(
                signal=SignalType.BUY,
                confidence=confidence,
                contributing_patterns=contributing,
                strategy_name=self.name,
                reasoning=f"BUY signal confirmed across {len(buy_timeframes)} timeframes: {buy_timeframes}",
                metadata={
                    'aligned_timeframes': buy_timeframes,
                    'total_timeframes': len(by_timeframe),
                },
            )

        elif len(sell_timeframes) >= self.min_timeframes:
            contributing = []
            for tf in sell_timeframes:
                contributing.extend(
                    [p for p in by_timeframe[tf] if p.signal == SignalType.SELL]
                )

            confidence = np.mean([p.confidence for p in contributing])

            return CombinedSignal(
                signal=SignalType.SELL,
                confidence=confidence,
                contributing_patterns=contributing,
                strategy_name=self.name,
                reasoning=f"SELL signal confirmed across {len(sell_timeframes)} timeframes: {sell_timeframes}",
                metadata={
                    'aligned_timeframes': sell_timeframes,
                    'total_timeframes': len(by_timeframe),
                },
            )

        return None


class PatternCombiner:
    """
    Main class for combining patterns using multiple strategies.

    Example:
        combiner = PatternCombiner()
        combiner.add_strategy(ConsensusStrategy())
        combiner.add_strategy(WeightedStrategy())

        signals = combiner.combine_patterns(patterns)
    """

    def __init__(self):
        self.strategies: List[PatternCombinationStrategy] = []

    def add_strategy(self, strategy: PatternCombinationStrategy):
        """Add a combination strategy."""
        self.strategies.append(strategy)

    def combine_patterns(
        self,
        patterns: List[PatternResult],
    ) -> List[CombinedSignal]:
        """
        Combine patterns using all registered strategies.

        Args:
            patterns: List of detected patterns

        Returns:
            List of combined signals from each strategy
        """
        signals = []

        for strategy in self.strategies:
            try:
                signal = strategy.combine(patterns)
                if signal:
                    signals.append(signal)
            except Exception as e:
                # Log but don't fail entire combination
                import logging
                logging.error(f"Strategy {strategy.name} failed: {e}")

        return signals

    def get_strongest_signal(
        self,
        patterns: List[PatternResult],
    ) -> Optional[CombinedSignal]:
        """
        Get the strongest signal from all strategies.

        Returns signal with highest confidence.
        """
        signals = self.combine_patterns(patterns)

        if not signals:
            return None

        return max(signals, key=lambda s: s.confidence)

    def get_consensus_signal(
        self,
        patterns: List[PatternResult],
    ) -> Optional[CombinedSignal]:
        """
        Get consensus signal when multiple strategies agree.

        Returns signal only if majority of strategies agree on direction.
        """
        signals = self.combine_patterns(patterns)

        if len(signals) < 2:
            return signals[0] if signals else None

        # Count votes
        buy_signals = [s for s in signals if s.signal == SignalType.BUY]
        sell_signals = [s for s in signals if s.signal == SignalType.SELL]

        # Majority vote
        if len(buy_signals) > len(sell_signals):
            # Average confidence
            avg_confidence = np.mean([s.confidence for s in buy_signals])

            # Merge contributing patterns
            all_patterns = []
            for signal in buy_signals:
                all_patterns.extend(signal.contributing_patterns)

            return CombinedSignal(
                signal=SignalType.BUY,
                confidence=avg_confidence,
                contributing_patterns=list(set(all_patterns)),  # Remove duplicates
                strategy_name="Meta Consensus",
                reasoning=f"{len(buy_signals)}/{len(signals)} strategies agree on BUY",
                metadata={
                    'agreeing_strategies': [s.strategy_name for s in buy_signals],
                    'total_strategies': len(signals),
                },
            )

        elif len(sell_signals) > len(buy_signals):
            avg_confidence = np.mean([s.confidence for s in sell_signals])

            all_patterns = []
            for signal in sell_signals:
                all_patterns.extend(signal.contributing_patterns)

            return CombinedSignal(
                signal=SignalType.SELL,
                confidence=avg_confidence,
                contributing_patterns=list(set(all_patterns)),
                strategy_name="Meta Consensus",
                reasoning=f"{len(sell_signals)}/{len(signals)} strategies agree on SELL",
                metadata={
                    'agreeing_strategies': [s.strategy_name for s in sell_signals],
                    'total_strategies': len(signals),
                },
            )

        return None
