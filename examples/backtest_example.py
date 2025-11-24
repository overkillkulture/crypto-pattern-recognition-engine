"""
Example: Backtest a pattern-based trading strategy.

This example demonstrates:
1. Setting up the pattern recognition engine
2. Detecting patterns on historical data
3. Backtesting a strategy
4. Analyzing performance metrics
"""

import asyncio
from datetime import datetime, timedelta

from src.core.engine import PatternRecognitionEngine
from src.core.types import Exchange, Timeframe
from src.data.provider import CryptoDataProvider
from src.patterns.detector import TechnicalPatternDetector
from src.patterns.technical import RSIPattern, MACDPattern, BollingerBandsPattern
from src.patterns.candlestick import CandlestickPatternDetector
from src.backtest.engine import BacktestEngine
from src.backtest.strategy import SimplePatternStrategy, TrendFollowingStrategy
from src.backtest.metrics import BacktestMetrics
from src.utils.config import get_default_config
from src.utils.logger import setup_logger


async def main():
    """Run backtesting example."""

    # Setup
    config = get_default_config()
    setup_logger(config)

    print("\n" + "="*60)
    print("PATTERN-BASED STRATEGY BACKTEST")
    print("="*60 + "\n")

    # Initialize components
    data_provider = CryptoDataProvider(config)

    # Setup pattern detectors
    technical_detector = TechnicalPatternDetector()
    technical_detector.register_pattern(RSIPattern())
    technical_detector.register_pattern(MACDPattern())
    technical_detector.register_pattern(BollingerBandsPattern())

    candlestick_detector = CandlestickPatternDetector()

    # Fetch historical data
    symbol = "BTC/USDT"
    exchange = Exchange.BINANCE
    timeframe = Timeframe.ONE_HOUR

    print(f"Fetching historical data: {symbol} ({timeframe.value})")
    print("This may take a moment...\n")

    try:
        # Get last 30 days of hourly data
        data = await data_provider.get_ohlcv(
            exchange=exchange,
            symbol=symbol,
            timeframe=timeframe,
            limit=720,  # ~30 days of hourly candles
        )

        print(f"✓ Fetched {len(data)} candles")
        print(f"  Date range: {datetime.fromtimestamp(data.timestamps[0]).date()} to "
              f"{datetime.fromtimestamp(data.timestamps[-1]).date()}\n")

        # Detect patterns
        print("Detecting patterns...")
        all_patterns = []

        # Technical patterns
        tech_patterns = await technical_detector.detect_patterns(symbol, timeframe, data)
        all_patterns.extend(tech_patterns)

        # Candlestick patterns
        candle_patterns = await candlestick_detector.detect_patterns(symbol, timeframe, data)
        all_patterns.extend(candle_patterns)

        print(f"✓ Detected {len(all_patterns)} patterns\n")

        # Backtest multiple strategies
        strategies = [
            SimplePatternStrategy(min_confidence=0.75),
            TrendFollowingStrategy(fast_ma=20, slow_ma=50),
        ]

        for strategy in strategies:
            print("-" * 60)
            print(f"BACKTESTING: {strategy.name}")
            print("-" * 60)

            # Initialize backtest engine
            backtest = BacktestEngine(
                initial_capital=10000.0,
                position_size_pct=0.10,  # 10% per trade
                fee_rate=0.001,  # 0.1% fees
            )

            # Run backtest
            results = await backtest.run(strategy, data, all_patterns)

            # Print results
            BacktestMetrics.print_summary(results['metrics'])

            # Show sample trades
            if results['trades']:
                print("Sample Trades:")
                for i, trade in enumerate(results['trades'][:5]):  # Show first 5
                    direction = "LONG" if trade.direction == 'long' else "SHORT"
                    print(f"\n  Trade {i+1} ({direction}):")
                    print(f"    Entry: {trade.entry_time.strftime('%Y-%m-%d %H:%M')} @ ${trade.entry_price:.2f}")
                    print(f"    Exit:  {trade.exit_time.strftime('%Y-%m-%d %H:%M')} @ ${trade.exit_price:.2f}")
                    print(f"    P&L:   ${trade.pnl:.2f} ({trade.pnl_pct*100:.2f}%)")
                    if trade.pattern:
                        print(f"    Pattern: {trade.pattern.pattern_name} (confidence: {trade.pattern.confidence:.2%})")

                print(f"\n  ... and {len(results['trades']) - 5} more trades")

            print()

        # Compare strategies
        print("=" * 60)
        print("STRATEGY COMPARISON")
        print("=" * 60)
        print()

        # Re-run both for comparison
        comparison = []
        for strategy in strategies:
            backtest = BacktestEngine(initial_capital=10000.0)
            results = await backtest.run(strategy, data, all_patterns)
            comparison.append({
                'name': strategy.name,
                'return': results['metrics']['total_return_pct'],
                'sharpe': results['metrics']['sharpe_ratio'],
                'max_dd': results['metrics']['max_drawdown_pct'],
                'win_rate': results['metrics']['win_rate'],
                'trades': results['metrics']['total_trades'],
            })

        # Print comparison table
        print(f"{'Strategy':<30} {'Return':<12} {'Sharpe':<10} {'Max DD':<12} {'Win Rate':<12} {'Trades'}")
        print("-" * 95)
        for s in comparison:
            print(f"{s['name']:<30} {s['return']:>10.2f}%  {s['sharpe']:>8.2f}  {s['max_dd']:>10.2f}%  "
                  f"{s['win_rate']:>10.2f}%  {s['trades']:>7}")

        print("\n" + "=" * 60)
        print("Backtest complete!")
        print("=" * 60 + "\n")

        # Best strategy
        best = max(comparison, key=lambda x: x['return'])
        print(f"🏆 Best performing strategy: {best['name']}")
        print(f"   Return: {best['return']:.2f}%\n")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await data_provider.close()


if __name__ == "__main__":
    asyncio.run(main())
