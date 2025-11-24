"""
Example: Multi-pattern analysis across timeframes and exchanges.

This example demonstrates:
1. Analyzing multiple symbols across different timeframes
2. Using all pattern detection types (technical, candlestick, chart)
3. Sending alerts to multiple channels
4. Data validation and sanitization
"""

import asyncio
from datetime import datetime

from src.core.engine import PatternRecognitionEngine
from src.core.types import Exchange, Timeframe
from src.data.provider import CryptoDataProvider
from src.patterns.detector import TechnicalPatternDetector
from src.patterns.technical import *
from src.patterns.candlestick import CandlestickPatternDetector
from src.patterns.chart import *
from src.analysis.analyzer import MarketAnalyzer
from src.alerts.handlers import ConsoleAlertHandler, FileAlertHandler
from src.utils.config import get_default_config
from src.utils.logger import setup_logger
from src.utils.validation import DataValidator


async def analyze_symbol(
    engine: PatternRecognitionEngine,
    exchange: Exchange,
    symbol: str,
    timeframe: Timeframe,
):
    """Analyze a single symbol and print results."""
    print(f"\n{'='*70}")
    print(f"ANALYZING: {symbol} on {exchange.value} ({timeframe.value})")
    print(f"{'='*70}\n")

    try:
        result = await engine.analyze_symbol(
            exchange=exchange,
            symbol=symbol,
            timeframe=timeframe,
            limit=500,
        )

        if result:
            # Print overall assessment
            print(f"📊 MARKET ASSESSMENT")
            print(f"{'─'*70}")
            print(f"Overall Signal: {result.overall_signal.value.upper()}")
            print(f"Confidence: {result.confidence:.2%}")
            print(f"Trend: {result.trend.upper()}")
            print(f"Volatility: {result.volatility:.4f}")
            print(f"Volume Profile: {result.volume_profile}")
            print(f"Risk Score: {result.risk_score:.2f}/1.00")
            print(f"Current Price: ${result.metadata['price']:,.2f}")

            # Support and resistance
            if result.support_levels:
                print(f"\n💚 Support Levels:")
                for level in result.support_levels[:3]:
                    print(f"   ${level:,.2f}")

            if result.resistance_levels:
                print(f"\n🔴 Resistance Levels:")
                for level in result.resistance_levels[:3]:
                    print(f"   ${level:,.2f}")

            # Detected patterns
            if result.patterns:
                print(f"\n📈 DETECTED PATTERNS ({len(result.patterns)})")
                print(f"{'─'*70}")

                # Group by type
                technical = [p for p in result.patterns if p.pattern_type.value == 'technical_indicator']
                candlestick = [p for p in result.patterns if p.pattern_type.value == 'candlestick_pattern']
                chart = [p for p in result.patterns if p.pattern_type.value == 'chart_pattern']

                if technical:
                    print(f"\nTechnical Indicators ({len(technical)}):")
                    for p in sorted(technical, key=lambda x: x.confidence, reverse=True)[:5]:
                        print(f"  • {p.pattern_name}")
                        print(f"    Signal: {p.signal.value.upper()}, Confidence: {p.confidence:.2%}")

                if candlestick:
                    print(f"\nCandlestick Patterns ({len(candlestick)}):")
                    for p in sorted(candlestick, key=lambda x: x.confidence, reverse=True)[:5]:
                        print(f"  • {p.pattern_name}")
                        print(f"    Signal: {p.signal.value.upper()}, Confidence: {p.confidence:.2%}")

                if chart:
                    print(f"\nChart Patterns ({len(chart)}):")
                    for p in sorted(chart, key=lambda x: x.confidence, reverse=True)[:5]:
                        print(f"  • {p.pattern_name}")
                        print(f"    Signal: {p.signal.value.upper()}, Confidence: {p.confidence:.2%}")
                        if p.target_price:
                            print(f"    Target: ${p.target_price:,.2f}")

            # Insights
            if result.insights:
                print(f"\n💡 INSIGHTS")
                print(f"{'─'*70}")
                for insight in result.insights:
                    print(f"  • {insight}")

        else:
            print("No analysis results available")

    except Exception as e:
        print(f"❌ Error analyzing {symbol}: {e}")


async def main():
    """Run multi-pattern analysis example."""

    # Setup
    config = get_default_config()
    setup_logger(config)

    print("\n" + "="*70)
    print("MULTI-PATTERN CRYPTOCURRENCY ANALYSIS")
    print("="*70 + "\n")

    # Initialize engine
    engine = PatternRecognitionEngine(config)

    # Setup data provider
    data_provider = CryptoDataProvider(config)
    engine.set_data_provider(data_provider)

    # Setup ALL pattern detectors
    print("Initializing pattern detectors...")

    # Technical indicators
    technical_detector = TechnicalPatternDetector()
    technical_detector.register_pattern(RSIPattern())
    technical_detector.register_pattern(MACDPattern())
    technical_detector.register_pattern(BollingerBandsPattern())
    technical_detector.register_pattern(StochasticPattern())
    technical_detector.register_pattern(VWAPPattern())
    technical_detector.register_pattern(MovingAverageCrossPattern(50, 200))
    technical_detector.register_pattern(ATRPattern())
    technical_detector.register_pattern(OBVPattern())

    engine.add_pattern_detector(technical_detector)
    print(f"✓ Registered {len(technical_detector.patterns)} technical indicators")

    # Candlestick patterns
    candlestick_detector = CandlestickPatternDetector()
    engine.add_pattern_detector(candlestick_detector)
    print(f"✓ Registered {len(candlestick_detector.patterns)} candlestick patterns")

    # Chart patterns
    chart_detector = TechnicalPatternDetector()  # Reuse for chart patterns
    chart_detector.register_pattern(HeadAndShouldersPattern())
    chart_detector.register_pattern(TrianglePattern())
    chart_detector.register_pattern(DoubleTopBottomPattern())
    chart_detector.register_pattern(FlagPattern())
    chart_detector.register_pattern(WedgePattern())

    engine.add_pattern_detector(chart_detector)
    print(f"✓ Registered {len(chart_detector.patterns)} chart patterns")

    # Setup analyzer
    analyzer = MarketAnalyzer()
    engine.add_analyzer(analyzer)
    print("✓ Analyzer configured")

    # Setup alert handlers
    console_handler = ConsoleAlertHandler()
    file_handler = FileAlertHandler()

    await console_handler.configure({'enabled': True})
    await file_handler.configure({'enabled': True, 'path': 'logs/alerts.log'})

    engine.add_alert_handler(console_handler)
    engine.add_alert_handler(file_handler)
    print("✓ Alert handlers configured\n")

    # Symbols to analyze
    symbols_to_analyze = [
        ("BTC/USDT", Timeframe.ONE_HOUR),
        ("ETH/USDT", Timeframe.ONE_HOUR),
        ("BTC/USDT", Timeframe.FOUR_HOURS),
    ]

    exchange = Exchange.BINANCE

    # Analyze each symbol
    for symbol, timeframe in symbols_to_analyze:
        await analyze_symbol(engine, exchange, symbol, timeframe)
        await asyncio.sleep(1)  # Rate limiting

    # Summary
    print(f"\n{'='*70}")
    print("ANALYSIS COMPLETE")
    print(f"{'='*70}")

    stats = engine.get_statistics()
    print(f"\nEngine Statistics:")
    print(f"  Symbols Analyzed: {len(symbols_to_analyze)}")
    print(f"  Pattern Detectors: {stats['pattern_detectors']}")
    print(f"  Alert Handlers: {stats['alert_handlers']}")
    print(f"  Cached Results: {stats['cached_analyses']}")

    print(f"\n✓ Alerts have been logged to: logs/alerts.log")
    print(f"✓ Check the file for detailed pattern detection alerts\n")

    # Cleanup
    await data_provider.close()


if __name__ == "__main__":
    asyncio.run(main())
