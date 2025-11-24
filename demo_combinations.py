"""
Pattern Combination Strategies Demo

Shows how multiple patterns are combined for stronger, more reliable signals.
"""

import asyncio
import sys
import numpy as np
from datetime import datetime

# Add src to path
sys.path.insert(0, '/home/user/crypto-pattern-recognition-engine')

from src.core.types import OHLCV, PatternType
from src.patterns.technical import RSIPattern, MACDPattern, BollingerBandsPattern, StochasticPattern
from src.patterns.candlestick import CandlestickPatternDetector
from src.patterns.combinations import (
    PatternCombiner,
    ConsensusStrategy,
    WeightedStrategy,
    ConfirmationStrategy,
)


def generate_strong_buy_setup(length=200):
    """Generate data with multiple bullish signals."""
    print("📊 Generating strong bullish oversold scenario...")

    timestamps = np.array([datetime.now().timestamp() - (length - i) * 3600 for i in range(length)])

    # Create oversold scenario that triggers RSI, Stochastic, Bollinger
    # Strong decline followed by potential reversal
    part1 = np.linspace(60000, 45000, length - 30)  # Strong decline
    part2 = np.full(30, 45000) + np.random.randn(30) * 100  # Oversold consolidation
    closes = np.concatenate([part1, part2])

    opens = np.roll(closes, 1)
    opens[0] = closes[0]

    highs = np.maximum(opens, closes) * 1.01
    lows = np.minimum(opens, closes) * 0.99

    # Add bullish hammer in recent candles
    idx = -3
    lows[idx] = closes[idx] * 0.96  # Long lower shadow
    opens[idx] = closes[idx-1] * 0.995

    volumes = np.random.lognormal(20, 1, length) * 1000

    print(f"✓ Generated oversold market at ${closes[-1]:.0f}")
    print(f"   (down from ${closes[0]:.0f}, -25%)\n")

    return OHLCV(timestamps=timestamps, open=opens, high=highs, low=lows, close=closes, volume=volumes)


async def demo_consensus_strategy():
    """Demonstrate consensus voting strategy."""
    print("\n" + "="*70)
    print("🗳️  STRATEGY 1: CONSENSUS VOTING")
    print("="*70)
    print("Requires 60% of patterns to agree on direction\n")

    data = generate_strong_buy_setup()

    # Detect patterns
    patterns = []
    for detector in [RSIPattern(), MACDPattern(), BollingerBandsPattern(), StochasticPattern()]:
        patterns.extend(detector.detect(data))

    candlestick_detector = CandlestickPatternDetector()
    patterns.extend(await candlestick_detector.detect_patterns("BTC/USDT", None, data))

    print(f"✓ Detected {len(patterns)} individual patterns\n")

    # Apply consensus strategy
    strategy = ConsensusStrategy(
        min_patterns=3,
        min_confidence=0.70,
        consensus_threshold=0.60,
    )

    signal = strategy.combine(patterns)

    if signal:
        print(f"✅ CONSENSUS ACHIEVED!")
        print(f"   Signal: {signal.signal.value.upper()}")
        print(f"   Confidence: {signal.confidence:.1%}")
        print(f"   Reasoning: {signal.reasoning}")
        print(f"   Contributing patterns: {len(signal.contributing_patterns)}")
        print(f"\n   Voting breakdown:")
        print(f"   • BUY votes: {signal.metadata['buy_votes']}")
        print(f"   • SELL votes: {signal.metadata['sell_votes']}")
        print(f"   • Consensus ratio: {signal.metadata['consensus_ratio']:.1%}")
    else:
        print("❌ No consensus reached - patterns disagree")

    return patterns


async def demo_weighted_strategy(patterns):
    """Demonstrate weighted scoring strategy."""
    print("\n" + "="*70)
    print("⚖️  STRATEGY 2: WEIGHTED SCORING")
    print("="*70)
    print("Different pattern types have different weights:\n")
    print("  • Chart Patterns: 1.5x weight (most reliable)")
    print("  • Technical Indicators: 1.0x weight")
    print("  • Candlestick Patterns: 0.8x weight\n")

    strategy = WeightedStrategy(
        weights={
            PatternType.CHART_PATTERN: 1.5,
            PatternType.TECHNICAL_INDICATOR: 1.0,
            PatternType.CANDLESTICK_PATTERN: 0.8,
        },
        min_score=0.60,
    )

    signal = strategy.combine(patterns)

    if signal:
        print(f"✅ WEIGHTED SIGNAL GENERATED!")
        print(f"   Signal: {signal.signal.value.upper()}")
        print(f"   Confidence: {signal.confidence:.1%}")
        print(f"   Reasoning: {signal.reasoning}")
        print(f"\n   Scores:")
        print(f"   • BUY score: {signal.metadata['buy_score']:.2f}")
        print(f"   • SELL score: {signal.metadata['sell_score']:.2f}")
        print(f"   • Total patterns: {signal.metadata['total_patterns']}")
    else:
        print("❌ Scores below threshold")


async def demo_confirmation_strategy(patterns):
    """Demonstrate confirmation strategy."""
    print("\n" + "="*70)
    print("✔️  STRATEGY 3: CONFIRMATION REQUIRED")
    print("="*70)
    print("Requires BOTH technical indicators AND candlestick patterns\n")

    strategy = ConfirmationStrategy(
        required_types=[
            PatternType.TECHNICAL_INDICATOR,
            PatternType.CANDLESTICK_PATTERN,
        ],
        min_confidence=0.70,
    )

    signal = strategy.combine(patterns)

    if signal:
        print(f"✅ CONFIRMATION ACHIEVED!")
        print(f"   Signal: {signal.signal.value.upper()}")
        print(f"   Confidence: {signal.confidence:.1%}")
        print(f"   Reasoning: {signal.reasoning}")
        print(f"\n   Pattern types confirmed:")
        for ptype, count in signal.metadata['patterns_per_type'].items():
            print(f"   • {ptype}: {count} patterns")
    else:
        print("❌ Missing required pattern types")
        print("   Both technical AND candlestick patterns needed")


async def demo_meta_consensus():
    """Demonstrate meta consensus across strategies."""
    print("\n" + "="*70)
    print("🎯 STRATEGY 4: META CONSENSUS")
    print("="*70)
    print("Combines signals from all strategies - highest confidence wins\n")

    data = generate_strong_buy_setup()

    # Detect patterns
    patterns = []
    for detector in [RSIPattern(), MACDPattern(), BollingerBandsPattern(), StochasticPattern()]:
        patterns.extend(detector.detect(data))

    candlestick_detector = CandlestickPatternDetector()
    patterns.extend(await candlestick_detector.detect_patterns("BTC/USDT", None, data))

    # Create combiner with multiple strategies
    combiner = PatternCombiner()
    combiner.add_strategy(ConsensusStrategy(min_patterns=2, consensus_threshold=0.60))
    combiner.add_strategy(WeightedStrategy(min_score=0.60))
    combiner.add_strategy(ConfirmationStrategy(
        required_types=[PatternType.TECHNICAL_INDICATOR, PatternType.CANDLESTICK_PATTERN],
        min_confidence=0.60
    ))

    # Get all signals
    all_signals = combiner.combine_patterns(patterns)

    print(f"✓ {len(all_signals)} strategies generated signals\n")

    for i, signal in enumerate(all_signals, 1):
        print(f"{i}. {signal.strategy_name}")
        print(f"   Signal: {signal.signal.value.upper()}")
        print(f"   Confidence: {signal.confidence:.1%}\n")

    # Get strongest signal
    strongest = combiner.get_strongest_signal(patterns)
    if strongest:
        print(f"🏆 STRONGEST SIGNAL (Highest Confidence):")
        print(f"   Strategy: {strongest.strategy_name}")
        print(f"   Signal: {strongest.signal.value.upper()}")
        print(f"   Confidence: {strongest.confidence:.1%}\n")

    # Get meta consensus
    meta = combiner.get_consensus_signal(patterns)
    if meta:
        print(f"✅ META CONSENSUS (Strategies Agree):")
        print(f"   Signal: {meta.signal.value.upper()}")
        print(f"   Confidence: {meta.confidence:.1%}")
        print(f"   Reasoning: {meta.reasoning}")
        if 'agreeing_strategies' in meta.metadata:
            print(f"\n   Agreeing strategies:")
            for strategy_name in meta.metadata['agreeing_strategies']:
                print(f"   • {strategy_name}")
    else:
        print("❌ No meta consensus - strategies disagree")


async def main():
    """Run combination strategy demonstrations."""
    print("\n" + "="*70)
    print("🎯 ADVANCED PATTERN COMBINATION STRATEGIES")
    print("="*70)
    print("\n💡 These strategies combine multiple patterns for stronger signals")
    print("   reducing false positives and increasing reliability.\n")

    try:
        # Demo each strategy
        patterns = await demo_consensus_strategy()

        input("\n⏸️  Press Enter to continue...")

        await demo_weighted_strategy(patterns)

        input("\n⏸️  Press Enter to continue...")

        await demo_confirmation_strategy(patterns)

        input("\n⏸️  Press Enter to continue...")

        await demo_meta_consensus()

        print("\n" + "="*70)
        print("✅ ALL COMBINATION STRATEGIES DEMONSTRATED!")
        print("="*70)
        print("\n🎯 Summary:")
        print("  • Consensus: Democratic voting across patterns")
        print("  • Weighted: Prioritizes more reliable pattern types")
        print("  • Confirmation: Requires multiple pattern types")
        print("  • Meta Consensus: Combines all strategies for final signal")
        print("\n🚀 These strategies dramatically improve trading accuracy!")
        print()

    except KeyboardInterrupt:
        print("\n\n⏹️  Demo stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
