"""
Example: Advanced pattern combination strategies.

This example demonstrates:
1. Using multiple combination strategies
2. Consensus voting across patterns
3. Weighted scoring by pattern type
4. Confirmation strategies requiring multiple pattern types
5. Timeframe confluence analysis
"""

import asyncio

from src.core.engine import PatternRecognitionEngine
from src.core.types import Exchange, PatternType, Timeframe
from src.data.provider import CryptoDataProvider
from src.patterns.candlestick import CandlestickPatternDetector
from src.patterns.chart import *
from src.patterns.combinations import (ConfirmationStrategy, ConsensusStrategy,
                                       PatternCombiner,
                                       TimeframeConfluenceStrategy,
                                       WeightedStrategy)
from src.patterns.detector import TechnicalPatternDetector
from src.patterns.technical import *
from src.utils.config import get_default_config
from src.utils.logger import setup_logger


async def analyze_with_combinations(
    engine: PatternRecognitionEngine,
    exchange: Exchange,
    symbol: str,
    timeframe: Timeframe,
):
    """Analyze symbol using pattern combinations."""
    print(f"\n{'='*70}")
    print(f"ANALYZING: {symbol} ({timeframe.value})")
    print(f"{'='*70}\n")

    try:
        # Analyze and get patterns
        result = await engine.analyze_symbol(
            exchange=exchange,
            symbol=symbol,
            timeframe=timeframe,
            limit=500,
        )

        if not result or not result.patterns:
            print("No patterns detected")
            return

        patterns = result.patterns

        print(f"📊 Detected {len(patterns)} patterns")
        print(f"\nPattern breakdown:")
        technical = [
            p for p in patterns if p.pattern_type == PatternType.TECHNICAL_INDICATOR
        ]
        candlestick = [
            p for p in patterns if p.pattern_type == PatternType.CANDLESTICK_PATTERN
        ]
        chart = [p for p in patterns if p.pattern_type == PatternType.CHART_PATTERN]

        print(f"  • Technical Indicators: {len(technical)}")
        print(f"  • Candlestick Patterns: {len(candlestick)}")
        print(f"  • Chart Patterns: {len(chart)}")

        # Initialize pattern combiner
        combiner = PatternCombiner()

        # Add various combination strategies
        print(f"\n{'─'*70}")
        print("COMBINATION STRATEGIES")
        print(f"{'─'*70}\n")

        # 1. Consensus Strategy
        print("1️⃣  Consensus Strategy (60% agreement required)")
        consensus = ConsensusStrategy(
            min_patterns=3,
            min_confidence=0.70,
            consensus_threshold=0.60,
        )
        combiner.add_strategy(consensus)

        consensus_signal = consensus.combine(patterns)
        if consensus_signal:
            print(f"   ✓ Signal: {consensus_signal.signal.value.upper()}")
            print(f"   ✓ Confidence: {consensus_signal.confidence:.2%}")
            print(f"   ✓ Reasoning: {consensus_signal.reasoning}")
            print(
                f"   ✓ Contributing patterns: {len(consensus_signal.contributing_patterns)}"
            )
        else:
            print("   ✗ No consensus signal")

        # 2. Weighted Strategy
        print(f"\n2️⃣  Weighted Strategy (chart patterns weighted higher)")
        weighted = WeightedStrategy(
            weights={
                PatternType.CHART_PATTERN: 1.5,
                PatternType.TECHNICAL_INDICATOR: 1.0,
                PatternType.CANDLESTICK_PATTERN: 0.8,
            },
            min_score=0.70,
        )
        combiner.add_strategy(weighted)

        weighted_signal = weighted.combine(patterns)
        if weighted_signal:
            print(f"   ✓ Signal: {weighted_signal.signal.value.upper()}")
            print(f"   ✓ Confidence: {weighted_signal.confidence:.2%}")
            print(f"   ✓ Reasoning: {weighted_signal.reasoning}")
            print(f"   ✓ Buy score: {weighted_signal.metadata['buy_score']:.2f}")
            print(f"   ✓ Sell score: {weighted_signal.metadata['sell_score']:.2f}")
        else:
            print("   ✗ No weighted signal")

        # 3. Confirmation Strategy (requires both technical AND chart pattern)
        print(f"\n3️⃣  Confirmation Strategy (requires technical + chart patterns)")
        confirmation = ConfirmationStrategy(
            required_types=[
                PatternType.TECHNICAL_INDICATOR,
                PatternType.CHART_PATTERN,
            ],
            min_confidence=0.70,
        )
        combiner.add_strategy(confirmation)

        confirmation_signal = confirmation.combine(patterns)
        if confirmation_signal:
            print(f"   ✓ Signal: {confirmation_signal.signal.value.upper()}")
            print(f"   ✓ Confidence: {confirmation_signal.confidence:.2%}")
            print(f"   ✓ Reasoning: {confirmation_signal.reasoning}")
            print(
                f"   ✓ Required types confirmed: {confirmation_signal.metadata['required_types']}"
            )
        else:
            print("   ✗ No confirmation signal (missing required pattern types)")

        # Get all combined signals
        print(f"\n{'─'*70}")
        print("COMBINED ANALYSIS")
        print(f"{'─'*70}\n")

        all_signals = combiner.combine_patterns(patterns)
        print(f"Total combination signals: {len(all_signals)}\n")

        for i, signal in enumerate(all_signals, 1):
            print(f"{i}. {signal.strategy_name}")
            print(f"   Signal: {signal.signal.value.upper()}")
            print(f"   Confidence: {signal.confidence:.2%}")
            print(f"   Patterns: {len(signal.contributing_patterns)}")
            print(f"   Reasoning: {signal.reasoning}\n")

        # Get strongest signal
        strongest = combiner.get_strongest_signal(patterns)
        if strongest:
            print(f"🏆 STRONGEST SIGNAL")
            print(f"{'─'*70}")
            print(f"Strategy: {strongest.strategy_name}")
            print(f"Signal: {strongest.signal.value.upper()}")
            print(f"Confidence: {strongest.confidence:.2%}")
            print(f"Reasoning: {strongest.reasoning}\n")

        # Get consensus across strategies
        meta_consensus = combiner.get_consensus_signal(patterns)
        if meta_consensus:
            print(f"🎯 META CONSENSUS (strategies agree)")
            print(f"{'─'*70}")
            print(f"Signal: {meta_consensus.signal.value.upper()}")
            print(f"Confidence: {meta_consensus.confidence:.2%}")
            print(f"Reasoning: {meta_consensus.reasoning}")
            print(
                f"Agreeing strategies: {meta_consensus.metadata['agreeing_strategies']}\n"
            )
        else:
            print("⚠️  No meta consensus - strategies disagree\n")

        # Show top contributing patterns
        if strongest:
            print(f"📈 TOP CONTRIBUTING PATTERNS")
            print(f"{'─'*70}")
            sorted_patterns = sorted(
                strongest.contributing_patterns,
                key=lambda p: p.confidence,
                reverse=True,
            )
            for i, pattern in enumerate(sorted_patterns[:5], 1):
                print(f"{i}. {pattern.pattern_name}")
                print(f"   Type: {pattern.pattern_type.value}")
                print(f"   Signal: {pattern.signal.value.upper()}")
                print(f"   Confidence: {pattern.confidence:.2%}\n")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


async def multi_timeframe_analysis(
    engine: PatternRecognitionEngine,
    exchange: Exchange,
    symbol: str,
):
    """Analyze across multiple timeframes for confluence."""
    print(f"\n{'='*70}")
    print(f"MULTI-TIMEFRAME CONFLUENCE ANALYSIS: {symbol}")
    print(f"{'='*70}\n")

    timeframes = [
        Timeframe.ONE_HOUR,
        Timeframe.FOUR_HOURS,
        Timeframe.ONE_DAY,
    ]

    all_patterns = []

    # Collect patterns from all timeframes
    for tf in timeframes:
        try:
            result = await engine.analyze_symbol(
                exchange=exchange,
                symbol=symbol,
                timeframe=tf,
                limit=500,
            )

            if result and result.patterns:
                print(f"✓ {tf.value}: {len(result.patterns)} patterns detected")
                all_patterns.extend(result.patterns)
            else:
                print(f"✗ {tf.value}: No patterns")

        except Exception as e:
            print(f"✗ {tf.value}: Error - {e}")

    if not all_patterns:
        print("\nNo patterns detected across timeframes")
        return

    print(f"\nTotal patterns across timeframes: {len(all_patterns)}\n")

    # Apply timeframe confluence strategy
    print(f"{'─'*70}")
    print("TIMEFRAME CONFLUENCE")
    print(f"{'─'*70}\n")

    confluence = TimeframeConfluenceStrategy(
        min_timeframes=2,
        min_confidence=0.70,
    )

    signal = confluence.combine(all_patterns)

    if signal:
        print(f"✓ CONFLUENCE DETECTED")
        print(f"  Signal: {signal.signal.value.upper()}")
        print(f"  Confidence: {signal.confidence:.2%}")
        print(f"  Reasoning: {signal.reasoning}")
        print(f"  Aligned timeframes: {signal.metadata['aligned_timeframes']}")
        print(f"  Total timeframes analyzed: {signal.metadata['total_timeframes']}")
        print(f"  Contributing patterns: {len(signal.contributing_patterns)}")
    else:
        print("✗ No timeframe confluence detected")
        print("  Timeframes do not agree on direction")


async def main():
    """Run pattern combination examples."""

    # Setup
    config = get_default_config()
    setup_logger(config)

    print("\n" + "=" * 70)
    print("ADVANCED PATTERN COMBINATION STRATEGIES")
    print("=" * 70 + "\n")

    # Initialize engine
    engine = PatternRecognitionEngine(config)

    # Setup data provider
    data_provider = CryptoDataProvider(config)
    engine.set_data_provider(data_provider)

    # Setup pattern detectors
    print("Initializing pattern detectors...")

    # Technical indicators
    technical_detector = TechnicalPatternDetector()
    technical_detector.register_pattern(RSIPattern())
    technical_detector.register_pattern(MACDPattern())
    technical_detector.register_pattern(BollingerBandsPattern())
    technical_detector.register_pattern(StochasticPattern())
    technical_detector.register_pattern(VWAPPattern())
    technical_detector.register_pattern(MovingAverageCrossPattern(50, 200))
    engine.add_pattern_detector(technical_detector)

    # Candlestick patterns
    candlestick_detector = CandlestickPatternDetector()
    engine.add_pattern_detector(candlestick_detector)

    # Chart patterns
    chart_detector = TechnicalPatternDetector()
    chart_detector.register_pattern(HeadAndShouldersPattern())
    chart_detector.register_pattern(TrianglePattern())
    chart_detector.register_pattern(DoubleTopBottomPattern())
    chart_detector.register_pattern(FlagPattern())
    engine.add_pattern_detector(chart_detector)

    print(f"✓ Pattern detectors configured\n")

    # Example 1: Single timeframe with multiple strategies
    await analyze_with_combinations(
        engine,
        Exchange.BINANCE,
        "BTC/USDT",
        Timeframe.ONE_HOUR,
    )

    await asyncio.sleep(1)

    # Example 2: Multi-timeframe confluence
    await multi_timeframe_analysis(
        engine,
        Exchange.BINANCE,
        "ETH/USDT",
    )

    print(f"\n{'='*70}")
    print("ANALYSIS COMPLETE")
    print(f"{'='*70}\n")

    print("💡 Key Takeaways:")
    print("  • Multiple combination strategies provide different perspectives")
    print("  • Consensus strategies require pattern agreement")
    print("  • Weighted strategies prioritize certain pattern types")
    print("  • Confirmation strategies require multiple pattern types")
    print("  • Timeframe confluence strengthens signals")
    print("  • Meta consensus shows when strategies agree\n")

    # Cleanup
    await data_provider.close()


if __name__ == "__main__":
    asyncio.run(main())
