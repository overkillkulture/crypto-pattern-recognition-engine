"""
Basic example: Analyze a single cryptocurrency pair.

This example demonstrates how to:
1. Initialize the pattern recognition engine
2. Configure data providers and pattern detectors
3. Analyze a trading pair
4. Display the results
"""

import asyncio
from datetime import datetime

from src.alerts.handlers import ConsoleAlertHandler
from src.analysis.analyzer import MarketAnalyzer
from src.core.engine import PatternRecognitionEngine
from src.core.types import Exchange, Timeframe
from src.data.provider import CryptoDataProvider
from src.patterns.detector import TechnicalPatternDetector
from src.patterns.technical import MACDPattern, RSIPattern
from src.utils.config import get_default_config
from src.utils.logger import setup_logger


async def main():
    """Run basic analysis example."""

    # 1. Setup configuration
    config = get_default_config()
    setup_logger(config)

    print("\n" + "=" * 60)
    print("Crypto Pattern Recognition Engine - Basic Example")
    print("=" * 60 + "\n")

    # 2. Initialize engine
    engine = PatternRecognitionEngine(config)

    # 3. Setup data provider
    data_provider = CryptoDataProvider(config)
    engine.set_data_provider(data_provider)

    # 4. Setup pattern detectors
    detector = TechnicalPatternDetector()
    detector.register_pattern(RSIPattern(period=14, overbought=70, oversold=30))
    detector.register_pattern(MACDPattern(fast=12, slow=26, signal=9))
    engine.add_pattern_detector(detector)

    # 5. Setup analyzer
    analyzer = MarketAnalyzer()
    engine.add_analyzer(analyzer)

    # 6. Setup alerts
    alert_handler = ConsoleAlertHandler()
    await alert_handler.configure({"enabled": True})
    engine.add_alert_handler(alert_handler)

    # 7. Configure and analyze
    symbol = "BTC/USDT"
    exchange = Exchange.BINANCE
    timeframe = Timeframe.ONE_HOUR

    print(f"Analyzing: {symbol}")
    print(f"Exchange: {exchange.value}")
    print(f"Timeframe: {timeframe.value}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n" + "-" * 60 + "\n")

    try:
        # Run analysis
        result = await engine.analyze_symbol(
            exchange=exchange,
            symbol=symbol,
            timeframe=timeframe,
            limit=500,
        )

        # Display results
        if result:
            print("📊 ANALYSIS RESULTS\n")
            print(f"Overall Signal: {result.overall_signal.value.upper()}")
            print(f"Confidence: {result.confidence:.2%}")
            print(f"Trend: {result.trend.upper()}")
            print(f"Volatility: {result.volatility:.4f}")
            print(f"Volume Profile: {result.volume_profile}")
            print(f"Risk Score: {result.risk_score:.2f}")
            print(f"\nCurrent Price: ${result.metadata['price']:,.2f}")

            print(f"\n📈 PATTERNS DETECTED: {len(result.patterns)}\n")
            for i, pattern in enumerate(result.patterns, 1):
                print(f"{i}. {pattern.pattern_name}")
                print(f"   Signal: {pattern.signal.value}")
                print(f"   Confidence: {pattern.confidence:.2%}")
                print(f"   Time: {pattern.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
                print()

            if result.support_levels:
                print(
                    f"💚 SUPPORT LEVELS: {', '.join(f'${x:,.2f}' for x in result.support_levels)}"
                )

            if result.resistance_levels:
                print(
                    f"🔴 RESISTANCE LEVELS: {', '.join(f'${x:,.2f}' for x in result.resistance_levels)}"
                )

            if result.insights:
                print(f"\n💡 INSIGHTS:\n")
                for insight in result.insights:
                    print(f"   • {insight}")

        else:
            print("No analysis results available.")

    except Exception as e:
        print(f"❌ Error during analysis: {e}")

    finally:
        # Cleanup
        await data_provider.close()

    print("\n" + "=" * 60)
    print("Analysis complete!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
