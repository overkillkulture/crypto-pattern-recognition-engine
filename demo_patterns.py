"""
Quick Pattern Detection Demo - Run the crypto pattern recognition engine!
"""

import asyncio
import sys
from datetime import datetime

import numpy as np
import ccxt.async_support as ccxt

# Add src to path
sys.path.insert(0, '/home/user/crypto-pattern-recognition-engine')

from src.core.types import OHLCV, Exchange, Timeframe, PatternType, SignalType
from src.patterns.technical import (
    RSIPattern,
    MACDPattern,
    BollingerBandsPattern,
    StochasticPattern,
)
from src.patterns.candlestick import CandlestickPatternDetector


async def fetch_ohlcv_data(symbol='BTC/USDT', timeframe='1h', limit=200):
    """Fetch OHLCV data from Binance."""
    print(f"📊 Fetching {symbol} data ({timeframe})...")

    exchange = ccxt.binance()

    try:
        ohlcv = await exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        await exchange.close()

        # Convert to our OHLCV format
        timestamps = np.array([candle[0] / 1000 for candle in ohlcv])  # ms to seconds
        opens = np.array([candle[1] for candle in ohlcv])
        highs = np.array([candle[2] for candle in ohlcv])
        lows = np.array([candle[3] for candle in ohlcv])
        closes = np.array([candle[4] for candle in ohlcv])
        volumes = np.array([candle[5] for candle in ohlcv])

        data = OHLCV(
            timestamps=timestamps,
            open=opens,
            high=highs,
            low=lows,
            close=closes,
            volume=volumes,
        )

        print(f"✓ Fetched {len(ohlcv)} candles")
        print(f"  Price range: ${lows.min():.2f} - ${highs.max():.2f}")
        print(f"  Current price: ${closes[-1]:.2f}")
        print()

        return data

    except Exception as e:
        print(f"❌ Error fetching data: {e}")
        await exchange.close()
        raise


async def detect_technical_patterns(data, symbol='BTC/USDT'):
    """Detect technical indicator patterns."""
    print("🔍 DETECTING TECHNICAL PATTERNS")
    print("="*70)

    patterns = [
        RSIPattern(period=14, oversold=30, overbought=70),
        MACDPattern(),
        BollingerBandsPattern(period=20, std_dev=2.0),
        StochasticPattern(),
    ]

    all_results = []

    for pattern in patterns:
        try:
            results = pattern.detect(data)
            all_results.extend(results)

            if results:
                for result in results:
                    signal_emoji = "🟢" if result.signal == SignalType.BUY else "🔴" if result.signal == SignalType.SELL else "⚪"
                    print(f"\n{signal_emoji} {result.pattern_name}")
                    print(f"   Signal: {result.signal.value.upper()}")
                    print(f"   Confidence: {result.confidence:.1%}")
                    if result.entry_price:
                        print(f"   Entry: ${result.entry_price:.2f}")
                    if result.target_price:
                        print(f"   Target: ${result.target_price:.2f}")
                    if result.stop_loss:
                        print(f"   Stop Loss: ${result.stop_loss:.2f}")
                    if result.description:
                        print(f"   Note: {result.description}")
            else:
                print(f"\n⚪ {pattern.__class__.__name__}: No signal")

        except Exception as e:
            print(f"\n❌ {pattern.__class__.__name__}: Error - {e}")

    return all_results


async def detect_candlestick_patterns(data, symbol='BTC/USDT'):
    """Detect candlestick patterns."""
    print("\n" + "="*70)
    print("🕯️  DETECTING CANDLESTICK PATTERNS")
    print("="*70)

    detector = CandlestickPatternDetector()

    try:
        results = await detector.detect_patterns(symbol, Timeframe.ONE_HOUR, data)

        if results:
            for result in results:
                signal_emoji = "🟢" if result.signal == SignalType.BUY else "🔴" if result.signal == SignalType.SELL else "⚪"
                print(f"\n{signal_emoji} {result.pattern_name}")
                print(f"   Signal: {result.signal.value.upper()}")
                print(f"   Confidence: {result.confidence:.1%}")
                if result.description:
                    print(f"   Note: {result.description}")
        else:
            print("\n⚪ No candlestick patterns detected")

        return results

    except Exception as e:
        print(f"\n❌ Error detecting candlestick patterns: {e}")
        return []


async def analyze_signals(all_patterns):
    """Analyze all detected patterns and provide summary."""
    print("\n" + "="*70)
    print("📈 SIGNAL SUMMARY")
    print("="*70)

    if not all_patterns:
        print("\n⚠️  No patterns detected")
        return

    # Count signals
    buy_signals = [p for p in all_patterns if p.signal == SignalType.BUY]
    sell_signals = [p for p in all_patterns if p.signal == SignalType.SELL]
    neutral_signals = [p for p in all_patterns if p.signal == SignalType.NEUTRAL]

    print(f"\nTotal Patterns Detected: {len(all_patterns)}")
    print(f"  🟢 BUY signals: {len(buy_signals)}")
    print(f"  🔴 SELL signals: {len(sell_signals)}")
    print(f"  ⚪ NEUTRAL signals: {len(neutral_signals)}")

    # Calculate average confidence
    if buy_signals:
        avg_buy_conf = np.mean([p.confidence for p in buy_signals])
        print(f"\n📊 Average BUY confidence: {avg_buy_conf:.1%}")

    if sell_signals:
        avg_sell_conf = np.mean([p.confidence for p in sell_signals])
        print(f"📊 Average SELL confidence: {avg_sell_conf:.1%}")

    # Overall sentiment
    print("\n" + "="*70)
    if len(buy_signals) > len(sell_signals):
        print("🚀 OVERALL SENTIMENT: BULLISH")
        print(f"   {len(buy_signals)} patterns suggest buying")
    elif len(sell_signals) > len(buy_signals):
        print("📉 OVERALL SENTIMENT: BEARISH")
        print(f"   {len(sell_signals)} patterns suggest selling")
    else:
        print("➡️  OVERALL SENTIMENT: NEUTRAL")
        print(f"   Equal number of buy/sell signals")

    print("="*70)


async def main():
    """Run pattern detection demo."""
    print("\n" + "="*70)
    print("🚀 CRYPTO PATTERN RECOGNITION ENGINE - LIVE DEMO")
    print("="*70)
    print()

    try:
        # Fetch data
        data = await fetch_ohlcv_data('BTC/USDT', '1h', 200)

        # Detect patterns
        technical_patterns = await detect_technical_patterns(data, 'BTC/USDT')
        candlestick_patterns = await detect_candlestick_patterns(data, 'BTC/USDT')

        # Combine all patterns
        all_patterns = technical_patterns + candlestick_patterns

        # Analyze
        await analyze_signals(all_patterns)

        print("\n✅ Pattern detection complete!\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
