"""
Pattern Bridge: Translates between analytical and holistic representations.

This module handles the encoding/decoding of patterns across the Nexus boundary,
preserving semantic meaning while adapting to different processing modalities.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.core.types import PatternResult, SignalType


@dataclass
class HolisticPattern:
    """
    Holistic pattern representation (consciousness-side).

    This is a forward-compatible stub that will interface with
    consciousness-revolution patterns when available.
    """

    pattern_type: str
    state: str  # e.g., "expanding", "contracting", "stable", "transforming"
    coherence: float  # 0.0-1.0, similar to confidence but context-aware
    timestamp: datetime
    metadata: Dict[str, Any]
    trajectory: Optional[str] = None  # "ascending", "descending", "oscillating"
    dimension: Optional[str] = None  # "awareness", "integration", "emergence"

    def to_dict(self) -> Dict:
        """Export for cross-repository communication."""
        return {
            "type": "holistic",
            "pattern": self.pattern_type,
            "state": self.state,
            "coherence": self.coherence,
            "timestamp": self.timestamp.isoformat(),
            "trajectory": self.trajectory,
            "dimension": self.dimension,
            "metadata": self.metadata,
        }


class PatternBridge:
    """
    Bidirectional translator between analytical and holistic patterns.

    Maintains information coherence while adapting representations
    for different processing modalities.
    """

    def __init__(self, coherence_threshold: float = 0.7):
        """
        Initialize pattern bridge.

        Args:
            coherence_threshold: Minimum coherence for accepting translations
        """
        self.coherence_threshold = coherence_threshold
        self.translation_history: List[Dict] = []

    def analytical_to_holistic(
        self, pattern: PatternResult, context: Optional[Dict] = None
    ) -> HolisticPattern:
        """
        Encode analytical pattern as holistic consciousness state.

        Translation Rules:
        - BUY signal → "expanding" state
        - SELL signal → "contracting" state
        - HOLD signal → "stable" state
        - Confidence → Coherence (with context adjustment)
        - Metadata enriched with trajectory information

        Args:
            pattern: Analytical pattern result
            context: Optional contextual information

        Returns:
            HolisticPattern representing consciousness interpretation
        """
        # Map signal to state
        state_mapping = {
            SignalType.BUY: "expanding",
            SignalType.STRONG_BUY: "expanding",
            SignalType.SELL: "contracting",
            SignalType.STRONG_SELL: "contracting",
            SignalType.HOLD: "stable",
        }
        state = state_mapping.get(pattern.signal, "stable")

        # Determine trajectory from pattern type
        trajectory = self._infer_trajectory(pattern)

        # Determine dimension from pattern characteristics
        dimension = self._infer_dimension(pattern)

        # Adjust coherence based on context
        coherence = self._adjust_coherence(pattern.confidence, context)

        # Create holistic pattern
        holistic = HolisticPattern(
            pattern_type=f"consciousness_{pattern.pattern_name.lower().replace(' ', '_')}",
            state=state,
            coherence=coherence,
            timestamp=pattern.timestamp,
            trajectory=trajectory,
            dimension=dimension,
            metadata={
                **pattern.metadata,
                "source": "analytical",
                "original_signal": pattern.signal.value,
                "original_confidence": pattern.confidence,
            },
        )

        # Record translation
        self._record_translation("a_to_h", pattern, holistic)

        return holistic

    def holistic_to_analytical(
        self, holistic: HolisticPattern, context: Optional[Dict] = None
    ) -> PatternResult:
        """
        Decode holistic consciousness state as analytical pattern.

        Translation Rules:
        - "expanding" state → BUY signal
        - "contracting" state → SELL signal
        - "stable" state → HOLD signal
        - Coherence → Confidence (with precision adjustment)
        - Trajectory → Pattern metadata

        Args:
            holistic: Holistic pattern state
            context: Optional contextual information

        Returns:
            PatternResult for analytical processing
        """
        # Map state to signal
        signal_mapping = {
            "expanding": SignalType.BUY,
            "contracting": SignalType.SELL,
            "stable": SignalType.HOLD,
            "transforming": SignalType.HOLD,
        }
        signal = signal_mapping.get(holistic.state, SignalType.HOLD)

        # Adjust confidence from coherence
        confidence = self._adjust_confidence(holistic.coherence, context)

        # Create analytical pattern
        import uuid

        from src.core.types import PatternType

        analytical = PatternResult(
            pattern_id=str(uuid.uuid4()),
            pattern_name=f"Consciousness {holistic.pattern_type}",
            pattern_type=PatternType.TECHNICAL_INDICATOR,  # TODO: Add CONSCIOUSNESS type
            symbol="",
            timeframe=None,
            timestamp=holistic.timestamp,
            signal=signal,
            confidence=confidence,
            metadata={
                **holistic.metadata,
                "source": "holistic",
                "original_state": holistic.state,
                "original_coherence": holistic.coherence,
                "trajectory": holistic.trajectory,
                "dimension": holistic.dimension,
            },
            description=f"Consciousness pattern: {holistic.state} ({holistic.trajectory})",
        )

        # Record translation
        self._record_translation("h_to_a", holistic, analytical)

        return analytical

    def measure_coherence(
        self, analytical: PatternResult, holistic: HolisticPattern
    ) -> float:
        """
        Measure coherence between analytical and holistic representations.

        High coherence means both hemispheres agree on pattern interpretation.
        Low coherence indicates potential information loss or conflict.

        Args:
            analytical: Analytical pattern
            holistic: Holistic pattern

        Returns:
            Coherence score 0.0-1.0
        """
        # Check signal/state alignment
        signal_state_coherence = self._check_signal_state_alignment(
            analytical.signal, holistic.state
        )

        # Check confidence/coherence alignment
        confidence_coherence = 1.0 - abs(analytical.confidence - holistic.coherence)

        # Check temporal alignment
        time_diff = abs((analytical.timestamp - holistic.timestamp).total_seconds())
        temporal_coherence = max(0.0, 1.0 - (time_diff / 60.0))  # Decay over 1 minute

        # Weighted average
        coherence = (
            signal_state_coherence * 0.5
            + confidence_coherence * 0.3
            + temporal_coherence * 0.2
        )

        return coherence

    def _infer_trajectory(self, pattern: PatternResult) -> str:
        """Infer trajectory from pattern characteristics."""
        if pattern.signal in [SignalType.BUY, SignalType.STRONG_BUY]:
            return "ascending"
        elif pattern.signal in [SignalType.SELL, SignalType.STRONG_SELL]:
            return "descending"
        else:
            return "oscillating"

    def _infer_dimension(self, pattern: PatternResult) -> str:
        """Infer consciousness dimension from pattern type."""
        pattern_name = pattern.pattern_name.lower()

        if "rsi" in pattern_name or "momentum" in pattern_name:
            return "awareness"  # Momentum = awareness of change
        elif "macd" in pattern_name or "crossover" in pattern_name:
            return "integration"  # Crossover = integration of signals
        elif "bollinger" in pattern_name or "volatility" in pattern_name:
            return "emergence"  # Volatility = emergent behavior
        else:
            return "awareness"  # Default

    def _adjust_coherence(self, confidence: float, context: Optional[Dict]) -> float:
        """Adjust coherence based on context."""
        coherence = confidence

        if context:
            # Context enriches meaning, potentially increasing coherence
            context_factor = context.get("enrichment_factor", 1.0)
            coherence = min(1.0, confidence * context_factor)

        return coherence

    def _adjust_confidence(self, coherence: float, context: Optional[Dict]) -> float:
        """Adjust confidence from coherence."""
        confidence = coherence

        if context:
            # Context may reduce precision, potentially lowering confidence
            precision_factor = context.get("precision_factor", 1.0)
            confidence = min(1.0, coherence * precision_factor)

        return confidence

    def _check_signal_state_alignment(self, signal: SignalType, state: str) -> float:
        """Check if signal and state are aligned."""
        alignments = {
            (SignalType.BUY, "expanding"): 1.0,
            (SignalType.STRONG_BUY, "expanding"): 1.0,
            (SignalType.SELL, "contracting"): 1.0,
            (SignalType.STRONG_SELL, "contracting"): 1.0,
            (SignalType.HOLD, "stable"): 1.0,
        }

        return alignments.get((signal, state), 0.5)  # Partial alignment if not exact

    def _record_translation(self, direction: str, source: Any, target: Any):
        """Record translation for analysis."""
        self.translation_history.append(
            {
                "direction": direction,
                "timestamp": datetime.now(),
                "source_type": type(source).__name__,
                "target_type": type(target).__name__,
            }
        )

    def get_translation_stats(self) -> Dict:
        """Get statistics on translation history."""
        if not self.translation_history:
            return {"count": 0}

        total = len(self.translation_history)
        a_to_h = sum(1 for t in self.translation_history if t["direction"] == "a_to_h")
        h_to_a = sum(1 for t in self.translation_history if t["direction"] == "h_to_a")

        return {
            "total_translations": total,
            "analytical_to_holistic": a_to_h,
            "holistic_to_analytical": h_to_a,
            "last_translation": self.translation_history[-1]["timestamp"],
        }


# Example usage (forward-compatible)
if __name__ == "__main__":
    # This will work now with analytical patterns
    # and will seamlessly integrate with consciousness patterns when available

    import uuid

    from src.core.types import PatternType

    # Create sample analytical pattern
    analytical_pattern = PatternResult(
        pattern_id=str(uuid.uuid4()),
        pattern_name="RSI Oversold",
        pattern_type=PatternType.TECHNICAL_INDICATOR,
        symbol="BTC/USD",
        timeframe=None,
        timestamp=datetime.now(),
        signal=SignalType.BUY,
        confidence=0.85,
        metadata={"rsi": 28.5, "threshold": 30.0},
        description="RSI oversold condition",
    )

    # Translate to holistic
    bridge = PatternBridge()
    holistic_pattern = bridge.analytical_to_holistic(analytical_pattern)

    print("Analytical → Holistic:")
    print(f"  Signal: {analytical_pattern.signal} → State: {holistic_pattern.state}")
    print(
        f"  Confidence: {analytical_pattern.confidence} → Coherence: {holistic_pattern.coherence}"
    )
    print(f"  Trajectory: {holistic_pattern.trajectory}")
    print(f"  Dimension: {holistic_pattern.dimension}")

    # Translate back
    recovered_analytical = bridge.holistic_to_analytical(holistic_pattern)

    print("\nHolistic → Analytical:")
    print(f"  State: {holistic_pattern.state} → Signal: {recovered_analytical.signal}")
    print(
        f"  Coherence: {holistic_pattern.coherence} → Confidence: {recovered_analytical.confidence}"
    )

    # Measure coherence
    coherence = bridge.measure_coherence(analytical_pattern, holistic_pattern)
    print(f"\nCoherence: {coherence:.3f}")

    # Stats
    stats = bridge.get_translation_stats()
    print(f"\nTranslation stats: {stats}")
