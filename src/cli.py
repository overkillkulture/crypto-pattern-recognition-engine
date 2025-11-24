"""Command-line interface for the pattern recognition engine."""

import asyncio
import argparse
import sys
from loguru import logger

from src.main import main as engine_main
from src.utils.config import load_config


def create_parser() -> argparse.ArgumentParser:
    """Create CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Crypto Pattern Recognition Engine - World-class cryptocurrency analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default config
  crypto-pattern

  # Specify config file
  crypto-pattern --config config/custom.yaml

  # Analyze specific symbol
  crypto-pattern --symbol BTC/USDT --timeframe 1h

  # Enable continuous monitoring
  crypto-pattern --realtime

  # Show version
  crypto-pattern --version
        """
    )

    parser.add_argument(
        '--config',
        type=str,
        default='config/config.yaml',
        help='Path to configuration file (default: config/config.yaml)'
    )

    parser.add_argument(
        '--symbol',
        type=str,
        help='Trading pair to analyze (e.g., BTC/USDT)'
    )

    parser.add_argument(
        '--timeframe',
        type=str,
        choices=['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w'],
        help='Timeframe for analysis'
    )

    parser.add_argument(
        '--exchange',
        type=str,
        choices=['binance', 'coinbase', 'kraken', 'bybit', 'okx'],
        help='Exchange to use'
    )

    parser.add_argument(
        '--realtime',
        action='store_true',
        help='Enable real-time continuous monitoring'
    )

    parser.add_argument(
        '--log-level',
        type=str,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )

    parser.add_argument(
        '--version',
        action='version',
        version='Crypto Pattern Recognition Engine v0.1.0'
    )

    return parser


def main():
    """CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    # TODO: Apply CLI arguments to override config
    # This will be fully implemented in Phase 7

    try:
        # Run the engine
        asyncio.run(engine_main())

    except KeyboardInterrupt:
        logger.info("\nShutdown requested by user")
        sys.exit(0)

    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
