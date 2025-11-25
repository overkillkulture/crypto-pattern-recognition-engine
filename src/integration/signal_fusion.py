"""
Signal Fusion: Combines signals from analytical and holistic streams.

This module implements ensemble decision-making that preserves both
perspectives while producing unified actionable outputs.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple

import numpy as np

from src.core.types import PatternResult, SignalType


class FusionStrategy(Enum):
    """Strategy for fusing signals from both hemispheres."""

    WEIGHTED_VOTE = "weighted_vote"  # Weight by confidence/coherence
    UNANIMOUS = "unanimous"  # Require agreement
    ANALYTICAL_PRIORITY = "analytical_priority"  # Analytical wins ties
    HOLISTIC_PRIORITY = "holistic_priority"  # Holistic wins ties
    HIGHEST_CONFIDENCE = "highest_confidence"  # Take most confident signal
    COHERENCE_WEIGHTED = "coherence_weighted"  # Weight by cross-hemisphere coherence


@dataclass
class FusedSignal:
    """Result of signal fusion from both hemispheres."""

    signal: SignalType
    confidence: float
    analytical_signal: SignalType
    holistic_signal: SignalType
    analytical_confidence: float
    holistic_confidence: float
    coherence: float
    strategy_used: FusionStrategy
    metadata: Dict

    def __str__(self) -> str:
        return (
            f"FusedSignal({self.signal.value}, "
            f"conf={self.confidence:.2f}, "
            f"coherence={self.coherence:.2f})"
        )


class SignalFusion:
    """
    Fuses signals from analytical and holistic processing streams.

    Implements multiple fusion strategies to handle:
    - Agreement (both hemispheres aligned)
    - Disagreement (conflict resolution)
    - Uncertainty (low confidence handling)
    - Partial information (one hemisphere missing)
    """

    def __init__(
        self,
        default_strategy: FusionStrategy = FusionStrategy.COHERENCE_WEIGHTED,
        coherence_threshold: float = 0.5,
    ):
        """
        Initialize signal fusion engine.

        Args:
            default_strategy: Default fusion strategy to use
            coherence_threshold: Minimum coherence to accept fusion
        """
        self.default_strategy = default_strategy
        self.coherence_threshold = coherence_threshold
        self.fusion_history: List[FusedSignal] = []

    def fuse(
        self,
        analytical_signals: List[PatternResult],
        holistic_signals: List,  # List[HolisticPattern] when available
        strategy: Optional[FusionStrategy] = None,
        coherence_scores: Optional[List[float]] = None,
    ) -> FusedSignal:
        """
        Fuse signals from both hemispheres.

        Args:
            analytical_signals: List of analytical pattern results
            holistic_signals: List of holistic pattern states
            strategy: Fusion strategy (uses default if None)
            coherence_scores: Pre-computed coherence scores

        Returns:
            FusedSignal combining both perspectives
        """
        strategy = strategy or self.default_strategy

        # Extract primary signals (highest confidence from each hemisphere)
        analytical_primary = self._get_primary_signal(analytical_signals)
        holistic_primary = self._get_primary_holistic_signal(holistic_signals)

        # Convert holistic signal to analytical format for fusion
        from .pattern_bridge import PatternBridge

        bridge = PatternBridge()

        if holistic_primary:
            holistic_as_analytical = bridge.holistic_to_analytical(holistic_primary)
            holistic_signal = holistic_as_analytical.signal
            holistic_confidence = holistic_as_analytical.confidence
        else:
            holistic_signal = SignalType.HOLD
            holistic_confidence = 0.0

        analytical_signal = (
            analytical_primary.signal if analytical_primary else SignalType.HOLD
        )
        analytical_confidence = (
            analytical_primary.confidence if analytical_primary else 0.0
        )

        # Measure coherence if not provided
        if coherence_scores:
            coherence = np.mean(coherence_scores)
        elif analytical_primary and holistic_primary:
            coherence = bridge.measure_coherence(analytical_primary, holistic_primary)
        else:
            coherence = 0.0

        # Apply fusion strategy
        if strategy == FusionStrategy.WEIGHTED_VOTE:
            fused = self._weighted_vote(
                analytical_signal,
                analytical_confidence,
                holistic_signal,
                holistic_confidence,
                coherence,
            )
        elif strategy == FusionStrategy.UNANIMOUS:
            fused = self._unanimous(
                analytical_signal,
                analytical_confidence,
                holistic_signal,
                holistic_confidence,
                coherence,
            )
        elif strategy == FusionStrategy.ANALYTICAL_PRIORITY:
            fused = self._analytical_priority(
                analytical_signal,
                analytical_confidence,
                holistic_signal,
                holistic_confidence,
                coherence,
            )
        elif strategy == FusionStrategy.HOLISTIC_PRIORITY:
            fused = self._holistic_priority(
                analytical_signal,
                analytical_confidence,
                holistic_signal,
                holistic_confidence,
                coherence,
            )
        elif strategy == FusionStrategy.HIGHEST_CONFIDENCE:
            fused = self._highest_confidence(
                analytical_signal,
                analytical_confidence,
                holistic_signal,
                holistic_confidence,
                coherence,
            )
        elif strategy == FusionStrategy.COHERENCE_WEIGHTED:
            fused = self._coherence_weighted(
                analytical_signal,
                analytical_confidence,
                holistic_signal,
                holistic_confidence,
                coherence,
            )
        else:
            raise ValueError(f"Unknown fusion strategy: {strategy}")

        # Create fused signal
        fused_signal = FusedSignal(
            signal=fused["signal"],
            confidence=fused["confidence"],
            analytical_signal=analytical_signal,
            holistic_signal=holistic_signal,
            analytical_confidence=analytical_confidence,
            holistic_confidence=holistic_confidence,
            coherence=coherence,
            strategy_used=strategy,
            metadata={
                "analytical_count": len(analytical_signals),
                "holistic_count": len(holistic_signals),
                "agreement": analytical_signal == holistic_signal,
            },
        )

        # Record fusion
        self.fusion_history.append(fused_signal)

        return fused_signal

    def _weighted_vote(
        self,
        sig_a: SignalType,
        conf_a: float,
        sig_h: SignalType,
        conf_h: float,
        coherence: float,
    ) -> Dict:
        """Weight signals by confidence."""
        if sig_a == sig_h:
            # Agreement - boost confidence
            return {
                "signal": sig_a,
                "confidence": min(1.0, (conf_a + conf_h) / 2 * 1.2),
            }
        else:
            # Disagreement - take higher confidence
            if conf_a > conf_h:
                return {
                    "signal": sig_a,
                    "confidence": conf_a * 0.8,
                }  # Reduce due to disagreement
            else:
                return {"signal": sig_h, "confidence": conf_h * 0.8}

    def _unanimous(
        self,
        sig_a: SignalType,
        conf_a: float,
        sig_h: SignalType,
        conf_h: float,
        coherence: float,
    ) -> Dict:
        """Require unanimous agreement."""
        if sig_a == sig_h:
            return {"signal": sig_a, "confidence": min(conf_a, conf_h)}  # Conservative
        else:
            # No agreement - default to HOLD
            return {"signal": SignalType.HOLD, "confidence": 0.5}

    def _analytical_priority(
        self,
        sig_a: SignalType,
        conf_a: float,
        sig_h: SignalType,
        conf_h: float,
        coherence: float,
    ) -> Dict:
        """Analytical hemisphere wins ties."""
        if coherence > self.coherence_threshold and sig_h == sig_a:
            # High coherence agreement - boost
            return {"signal": sig_a, "confidence": (conf_a + conf_h) / 2 * 1.1}
        else:
            # Use analytical
            return {"signal": sig_a, "confidence": conf_a}

    def _holistic_priority(
        self,
        sig_a: SignalType,
        conf_a: float,
        sig_h: SignalType,
        conf_h: float,
        coherence: float,
    ) -> Dict:
        """Holistic hemisphere wins ties."""
        if coherence > self.coherence_threshold and sig_h == sig_a:
            # High coherence agreement - boost
            return {"signal": sig_h, "confidence": (conf_a + conf_h) / 2 * 1.1}
        else:
            # Use holistic
            return {"signal": sig_h, "confidence": conf_h}

    def _highest_confidence(
        self,
        sig_a: SignalType,
        conf_a: float,
        sig_h: SignalType,
        conf_h: float,
        coherence: float,
    ) -> Dict:
        """Take signal with highest confidence."""
        if conf_a >= conf_h:
            return {"signal": sig_a, "confidence": conf_a}
        else:
            return {"signal": sig_h, "confidence": conf_h}

    def _coherence_weighted(
        self,
        sig_a: SignalType,
        conf_a: float,
        sig_h: SignalType,
        conf_h: float,
        coherence: float,
    ) -> Dict:
        """Weight by cross-hemisphere coherence."""
        if sig_a == sig_h:
            # Agreement - coherence boosts confidence
            boosted_conf = (conf_a + conf_h) / 2 * (1.0 + coherence * 0.3)
            return {"signal": sig_a, "confidence": min(1.0, boosted_conf)}
        else:
            # Disagreement - coherence determines blend
            if coherence > 0.7:
                # High coherence but different signals - reduce both
                avg_conf = (conf_a + conf_h) / 2 * 0.7
                # Take higher original confidence
                signal = sig_a if conf_a > conf_h else sig_h
                return {"signal": signal, "confidence": avg_conf}
            else:
                # Low coherence - weighted by individual confidence
                total_weight = conf_a + conf_h
                if total_weight > 0:
                    weight_a = conf_a / total_weight
                    signal = sig_a if weight_a > 0.5 else sig_h
                    confidence = max(conf_a, conf_h) * 0.8
                else:
                    signal = SignalType.HOLD
                    confidence = 0.5
                return {"signal": signal, "confidence": confidence}

    def _get_primary_signal(
        self, signals: List[PatternResult]
    ) -> Optional[PatternResult]:
        """Get highest confidence signal from list."""
        if not signals:
            return None
        return max(signals, key=lambda x: x.confidence)

    def _get_primary_holistic_signal(self, signals: List) -> Optional:
        """Get highest coherence holistic signal."""
        if not signals:
            return None
        # For now, just take first signal (will implement proper selection when available)
        # In future: return max(signals, key=lambda x: x.coherence)
        return signals[0] if signals else None

    def resolve_conflict(
        self,
        analytical: PatternResult,
        holistic,  # HolisticPattern when available
    ) -> Tuple[SignalType, str]:
        """
        Resolve conflict between hemispheres.

        Returns:
            (resolved_signal, explanation)
        """
        from .pattern_bridge import PatternBridge

        bridge = PatternBridge()

        # Convert holistic to analytical for comparison
        if holistic:
            holistic_as_analytical = bridge.holistic_to_analytical(holistic)
            coherence = bridge.measure_coherence(analytical, holistic)

            if coherence < 0.3:
                # Very low coherence - major conflict
                return (
                    SignalType.HOLD,
                    f"Major conflict: coherence={coherence:.2f}, defaulting to HOLD",
                )
            elif coherence < 0.5:
                # Moderate conflict - use higher confidence
                if analytical.confidence > holistic_as_analytical.confidence:
                    return (
                        analytical.signal,
                        f"Moderate conflict resolved by analytical (conf={analytical.confidence:.2f})",
                    )
                else:
                    return (
                        holistic_as_analytical.signal,
                        f"Moderate conflict resolved by holistic (conf={holistic_as_analytical.confidence:.2f})",
                    )
            else:
                # Minor conflict - average
                avg_conf = (
                    analytical.confidence + holistic_as_analytical.confidence
                ) / 2
                signal = analytical.signal if avg_conf > 0.5 else SignalType.HOLD
                return (signal, f"Minor conflict resolved: avg_conf={avg_conf:.2f}")
        else:
            # No holistic signal - use analytical
            return (analytical.signal, "No holistic signal available")

    def get_fusion_stats(self) -> Dict:
        """Get statistics on fusion history."""
        if not self.fusion_history:
            return {"count": 0}

        total = len(self.fusion_history)
        agreements = sum(
            1 for f in self.fusion_history if f.analytical_signal == f.holistic_signal
        )
        avg_coherence = np.mean([f.coherence for f in self.fusion_history])
        avg_confidence = np.mean([f.confidence for f in self.fusion_history])

        return {
            "total_fusions": total,
            "agreements": agreements,
            "agreement_rate": agreements / total if total > 0 else 0.0,
            "avg_coherence": avg_coherence,
            "avg_confidence": avg_confidence,
            "last_fusion": str(self.fusion_history[-1]),
        }


# Example usage
if __name__ == "__main__":
    import uuid
    from datetime import datetime

    from src.core.types import PatternType

    # Create sample analytical signal
    analytical = PatternResult(
        pattern_id=str(uuid.uuid4()),
        pattern_name="RSI Oversold",
        pattern_type=PatternType.TECHNICAL_INDICATOR,
        symbol="BTC/USD",
        timeframe=None,
        timestamp=datetime.now(),
        signal=SignalType.BUY,
        confidence=0.85,
        metadata={"rsi": 28.5},
        description="RSI oversold",
    )

    # Create holistic signal (simulated)
    from .pattern_bridge import HolisticPattern

    holistic = HolisticPattern(
        pattern_type="consciousness_expansion",
        state="expanding",
        coherence=0.80,
        timestamp=datetime.now(),
        metadata={},
        trajectory="ascending",
        dimension="awareness",
    )

    # Fuse signals
    fusion = SignalFusion()
    fused = fusion.fuse([analytical], [holistic])

    print(f"Analytical: {analytical.signal.value} (conf={analytical.confidence:.2f})")
    print(f"Holistic: expanding → BUY (coherence={holistic.coherence:.2f})")
    print(f"\nFused: {fused}")
    print(f"Agreement: {fused.metadata['agreement']}")

    # Test conflict resolution
    print("\n--- Conflict Test ---")
    analytical_sell = PatternResult(
        pattern_id=str(uuid.uuid4()),
        pattern_name="MACD Bearish",
        pattern_type=PatternType.TECHNICAL_INDICATOR,
        symbol="BTC/USD",
        timeframe=None,
        timestamp=datetime.now(),
        signal=SignalType.SELL,
        confidence=0.75,
        metadata={},
        description="MACD bearish",
    )

    fused_conflict = fusion.fuse([analytical_sell], [holistic])
    print(f"Analytical: SELL (0.75), Holistic: BUY (0.80)")
    print(f"Fused: {fused_conflict}")

    # Stats
    stats = fusion.get_fusion_stats()
    print(f"\nFusion stats: {stats}")
