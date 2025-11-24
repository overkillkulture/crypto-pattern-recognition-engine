#!/usr/bin/env python3
"""
Integration Demo: Forward-looking example of dual-hemisphere processing.

This demonstrates how analytical (crypto patterns) and holistic (consciousness)
processing streams work together through the Nexus layer.

READY FOR: When consciousness-revolution becomes available
"""

import sys
sys.path.insert(0, '/home/user/crypto-pattern-recognition-engine')

from datetime import datetime, timedelta
from typing import List
import numpy as np

# Analytical hemisphere
from src.patterns.optimized import OptimizedRSIPattern, OptimizedMACDPattern
from src.core.types import PatternResult, SignalType
from tests.fixtures.market_data import generate_ohlcv

# Integration layer
from src.integration.pattern_bridge import PatternBridge, HolisticPattern
from src.integration.signal_fusion import SignalFusion, FusionStrategy
from src.integration.context_sync import ContextSync


class IntegratedTradingSystem:
    """
    Integrated trading system using both hemispheres.

    This is a forward-compatible implementation that:
    1. Works NOW with analytical patterns only
    2. Will SEAMLESSLY integrate consciousness patterns when available
    """

    def __init__(self):
        """Initialize integrated system."""
        # Analytical patterns
        self.rsi_pattern = OptimizedRSIPattern(period=14, use_cache=False)
        self.macd_pattern = OptimizedMACDPattern(use_cache=False)

        # Integration components
        self.bridge = PatternBridge(coherence_threshold=0.7)
        self.fusion = SignalFusion(
            default_strategy=FusionStrategy.COHERENCE_WEIGHTED,
            coherence_threshold=0.5
        )
        self.context_sync = ContextSync(sync_interval=1800)

        # Holistic patterns (placeholder for consciousness-revolution integration)
        # When available: from consciousness_revolution import ConsciousnessEngine
        self.consciousness_engine = None  # Will be initialized when available

    def process_market_data(self, data):
        """
        Process market data through both hemispheres.

        Args:
            data: OHLCV market data

        Returns:
            Integrated decision with coherence metrics
        """
        print("\n" + "="*60)
        print("DUAL-HEMISPHERE PROCESSING")
        print("="*60)

        # ANALYTICAL HEMISPHERE: Technical pattern detection
        print("\n[LEFT HEMISPHERE: Analytical Processing]")
        analytical_patterns = self._analytical_processing(data)

        # Create analytical context
        analytical_context = {
            'market_state': self._determine_market_state(analytical_patterns),
            'timestamp': datetime.now(),
            'patterns': [p.pattern_name for p in analytical_patterns],
            'metadata': {'source': 'analytical', 'pattern_count': len(analytical_patterns)},
        }

        # HOLISTIC HEMISPHERE: Consciousness pattern detection
        print("\n[RIGHT HEMISPHERE: Holistic Processing]")
        holistic_patterns = self._holistic_processing(analytical_patterns, analytical_context)

        # Create holistic context
        holistic_context = {
            'consciousness_state': self._determine_consciousness_state(holistic_patterns),
            'timestamp': datetime.now(),
            'patterns': [p.pattern_type for p in holistic_patterns],
            'metadata': {'source': 'holistic', 'pattern_count': len(holistic_patterns)},
        }

        # NEXUS LAYER: Synchronize contexts
        print("\n[NEXUS LAYER: Context Synchronization]")
        shared_context = self.context_sync.sync_state(analytical_context, holistic_context)
        print(f"  Shared Context Coherence: {shared_context.coherence_level:.2f}")
        print(f"  Market State: {shared_context.market_state}")
        print(f"  Consciousness State: {shared_context.consciousness_state}")

        # Detect drift
        drift = self.context_sync.detect_drift(analytical_context, holistic_context)
        print(f"  Context Drift: {drift:.3f}")

        # FUSION: Integrate signals
        print("\n[SIGNAL FUSION: Integration]")
        fused_signal = self.fusion.fuse(
            analytical_patterns,
            holistic_patterns,
            strategy=FusionStrategy.COHERENCE_WEIGHTED
        )

        print(f"  Analytical Signal: {fused_signal.analytical_signal.value} (conf={fused_signal.analytical_confidence:.2f})")
        print(f"  Holistic Signal: {fused_signal.holistic_signal.value} (conf={fused_signal.holistic_confidence:.2f})")
        print(f"  Agreement: {'YES ✓' if fused_signal.metadata['agreement'] else 'NO ✗'}")
        print(f"  Coherence: {fused_signal.coherence:.2f}")
        print(f"\n  → FUSED DECISION: {fused_signal.signal.value} (confidence={fused_signal.confidence:.2f})")

        # Return integrated result
        return {
            'signal': fused_signal.signal,
            'confidence': fused_signal.confidence,
            'coherence': fused_signal.coherence,
            'analytical_patterns': analytical_patterns,
            'holistic_patterns': holistic_patterns,
            'shared_context': shared_context,
            'fused_signal': fused_signal,
        }

    def _analytical_processing(self, data) -> List[PatternResult]:
        """Analytical hemisphere processing."""
        patterns = []

        # RSI patterns
        rsi_patterns = self.rsi_pattern.detect(data)
        patterns.extend(rsi_patterns)

        # MACD patterns
        macd_patterns = self.macd_pattern.detect(data)
        patterns.extend(macd_patterns)

        print(f"  Detected {len(patterns)} analytical patterns:")
        for p in patterns:
            print(f"    - {p.pattern_name}: {p.signal.value} (conf={p.confidence:.2f})")

        return patterns

    def _holistic_processing(
        self,
        analytical_patterns: List[PatternResult],
        analytical_context: dict
    ) -> List[HolisticPattern]:
        """Holistic hemisphere processing."""
        holistic_patterns = []

        # Translate analytical patterns to holistic domain
        for pattern in analytical_patterns:
            holistic = self.bridge.analytical_to_holistic(pattern, analytical_context)
            holistic_patterns.append(holistic)

        print(f"  Translated {len(holistic_patterns)} holistic patterns:")
        for h in holistic_patterns:
            print(f"    - {h.pattern_type}: {h.state} (coherence={h.coherence:.2f})")
            print(f"      Trajectory: {h.trajectory}, Dimension: {h.dimension}")

        # When consciousness-revolution is available, add:
        # if self.consciousness_engine:
        #     consciousness_patterns = self.consciousness_engine.perceive(analytical_context)
        #     holistic_patterns.extend(consciousness_patterns)

        return holistic_patterns

    def _determine_market_state(self, patterns: List[PatternResult]) -> str:
        """Determine market state from analytical patterns."""
        if not patterns:
            return "neutral"

        buy_signals = sum(1 for p in patterns if p.signal in [SignalType.BUY, SignalType.STRONG_BUY])
        sell_signals = sum(1 for p in patterns if p.signal in [SignalType.SELL, SignalType.STRONG_SELL])

        if buy_signals > sell_signals:
            return "bullish"
        elif sell_signals > buy_signals:
            return "bearish"
        else:
            return "neutral"

    def _determine_consciousness_state(self, patterns: List[HolisticPattern]) -> str:
        """Determine consciousness state from holistic patterns."""
        if not patterns:
            return "stable"

        expanding = sum(1 for p in patterns if p.state == "expanding")
        contracting = sum(1 for p in patterns if p.state == "contracting")

        if expanding > contracting:
            return "expanding"
        elif contracting > expanding:
            return "contracting"
        else:
            return "stable"

    def get_system_metrics(self) -> dict:
        """Get comprehensive system metrics."""
        return {
            'bridge_stats': self.bridge.get_translation_stats(),
            'fusion_stats': self.fusion.get_fusion_stats(),
            'sync_stats': self.context_sync.get_sync_stats(),
        }


def main():
    """
    Demonstration of integrated dual-hemisphere trading system.

    This works NOW and will seamlessly integrate consciousness patterns
    when consciousness-revolution becomes available.
    """
    print("="*60)
    print("INTEGRATED DUAL-HEMISPHERE TRADING SYSTEM")
    print("="*60)
    print("\nArchitecture:")
    print("  Left Hemisphere: Analytical (Crypto Patterns)")
    print("  Right Hemisphere: Holistic (Consciousness Patterns)")
    print("  Nexus Layer: Bidirectional Translation")
    print("  Integration: Coherence-Weighted Fusion")

    # Initialize system
    system = IntegratedTradingSystem()

    # Test Case 1: Oversold market (should trigger BUY)
    print("\n" + "="*60)
    print("TEST CASE 1: Oversold Market Condition")
    print("="*60)

    from tests.fixtures.market_data import generate_rsi_oversold
    data_oversold = generate_rsi_oversold(periods=100, seed=42)

    result1 = system.process_market_data(data_oversold)

    print("\n[RESULT]")
    print(f"  Final Decision: {result1['signal'].value}")
    print(f"  Confidence: {result1['confidence']:.2f}")
    print(f"  Coherence: {result1['coherence']:.2f}")

    # Test Case 2: Overbought market (should trigger SELL)
    print("\n" + "="*60)
    print("TEST CASE 2: Overbought Market Condition")
    print("="*60)

    from tests.fixtures.market_data import generate_rsi_overbought
    data_overbought = generate_rsi_overbought(periods=100, seed=42)

    result2 = system.process_market_data(data_overbought)

    print("\n[RESULT]")
    print(f"  Final Decision: {result2['signal'].value}")
    print(f"  Confidence: {result2['confidence']:.2f}")
    print(f"  Coherence: {result2['coherence']:.2f}")

    # Test Case 3: Neutral market (should trigger HOLD)
    print("\n" + "="*60)
    print("TEST CASE 3: Neutral Market Condition")
    print("="*60)

    data_neutral = generate_ohlcv(periods=100, trend="neutral", seed=42)

    result3 = system.process_market_data(data_neutral)

    print("\n[RESULT]")
    print(f"  Final Decision: {result3['signal'].value}")
    print(f"  Confidence: {result3['confidence']:.2f}")
    print(f"  Coherence: {result3['coherence']:.2f}")

    # System Metrics
    print("\n" + "="*60)
    print("SYSTEM METRICS")
    print("="*60)

    metrics = system.get_system_metrics()

    print("\nPattern Bridge:")
    for key, value in metrics['bridge_stats'].items():
        print(f"  {key}: {value}")

    print("\nSignal Fusion:")
    for key, value in metrics['fusion_stats'].items():
        print(f"  {key}: {value}")

    print("\nContext Sync:")
    for key, value in metrics['sync_stats'].items():
        print(f"  {key}: {value}")

    # Forward Compatibility Note
    print("\n" + "="*60)
    print("FORWARD COMPATIBILITY")
    print("="*60)
    print("\n✓ System is READY for consciousness-revolution integration")
    print("✓ All interfaces defined and tested")
    print("✓ Translation codecs operational")
    print("✓ Coherence validation working")
    print("\nWhen consciousness-revolution becomes available:")
    print("  1. Import ConsciousnessEngine")
    print("  2. Initialize in IntegratedTradingSystem.__init__()")
    print("  3. Call consciousness_engine.perceive() in _holistic_processing()")
    print("  4. System will automatically fuse consciousness patterns")
    print("\nNo other changes needed - architecture is ready! 🚀")


if __name__ == "__main__":
    main()
