"""Main entry point for the Crypto Pattern Recognition Engine."""

import asyncio
import sys

from loguru import logger

from src.alerts.handlers import ConsoleAlertHandler, FileAlertHandler
from src.analysis.analyzer import MarketAnalyzer
from src.core.engine import PatternRecognitionEngine
from src.core.types import Exchange, Timeframe
from src.data.provider import CryptoDataProvider
from src.patterns.detector import TechnicalPatternDetector
from src.patterns.technical import MACDPattern, RSIPattern
from src.utils.config import load_config, validate_config
from src.utils.logger import setup_logger


async def main():
    """Main application entry point."""
    try:
        # Load configuration
        config = load_config()
        validate_config(config)

        # Setup logging
        setup_logger(config)
        logger.info("🚀 Starting Crypto Pattern Recognition Engine")

        # Initialize engine
        engine = PatternRecognitionEngine(config)

        # Setup data provider
        data_provider = CryptoDataProvider(config)
        engine.set_data_provider(data_provider)

        # Setup pattern detectors
        technical_detector = TechnicalPatternDetector()

        # Register technical patterns
        technical_detector.register_pattern(RSIPattern())
        technical_detector.register_pattern(MACDPattern())
        # More patterns will be added in Phase 4

        engine.add_pattern_detector(technical_detector)

        # Setup analyzer
        analyzer = MarketAnalyzer()
        engine.add_analyzer(analyzer)

        # Setup alert handlers
        console_handler = ConsoleAlertHandler()
        file_handler = FileAlertHandler()

        await console_handler.configure(
            config.get("alerts", {}).get("channels", {}).get("console", {})
        )
        await file_handler.configure(
            config.get("alerts", {}).get("channels", {}).get("file", {})
        )

        engine.add_alert_handler(console_handler)
        engine.add_alert_handler(file_handler)

        # Configure active symbols and timeframes
        symbols = config.get("pairs", ["BTC/USDT"])
        timeframes = [Timeframe(tf) for tf in config.get("timeframes", ["1h"])]

        # Determine active exchanges
        exchanges = []
        for exchange_name, exchange_config in config.get("exchanges", {}).items():
            if exchange_config.get("enabled", False):
                exchanges.append(Exchange(exchange_name))

        if not exchanges:
            logger.error("No exchanges enabled in configuration")
            return

        engine.configure(symbols, timeframes, exchanges)

        # Display startup info
        logger.info(
            f"Configured: {len(symbols)} symbols, "
            f"{len(timeframes)} timeframes, {len(exchanges)} exchanges"
        )
        logger.info(f"Symbols: {', '.join(symbols)}")
        logger.info(f"Timeframes: {', '.join(tf.value for tf in timeframes)}")
        logger.info(f"Exchanges: {', '.join(ex.value for ex in exchanges)}")

        # Check if we should run continuously or single analysis
        realtime_config = config.get("realtime", {})

        if realtime_config.get("enabled", False):
            # Run continuous monitoring
            logger.info("Starting continuous monitoring mode...")
            await engine.start()
        else:
            # Run single analysis for each configured pair
            logger.info("Running single analysis mode...")

            for exchange in exchanges:
                for symbol in symbols:
                    for timeframe in timeframes:
                        logger.info(
                            f"\nAnalyzing {symbol} on {exchange.value} ({timeframe.value})"
                        )

                        try:
                            result = await engine.analyze_symbol(
                                exchange=exchange,
                                symbol=symbol,
                                timeframe=timeframe,
                                limit=500,
                            )

                            if result:
                                logger.info(f"Analysis complete for {symbol}")
                                logger.info(
                                    f"Overall Signal: {result.overall_signal.value}"
                                )
                                logger.info(f"Confidence: {result.confidence:.2%}")
                                logger.info(f"Trend: {result.trend}")
                                logger.info(f"Volatility: {result.volatility:.4f}")
                                logger.info(
                                    f"Patterns detected: {len(result.patterns)}"
                                )

                                if result.insights:
                                    logger.info("Insights:")
                                    for insight in result.insights:
                                        logger.info(f"  - {insight}")

                        except Exception as e:
                            logger.error(f"Error analyzing {symbol}: {e}")

            logger.info(
                "\nAnalysis complete. Check logs/alerts.log for detailed alerts."
            )

        # Cleanup
        await data_provider.close()
        logger.info("Engine stopped")

    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
