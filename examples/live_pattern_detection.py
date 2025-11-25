"""
Live Pattern Detection Demo

Demonstrates real-time pattern detection on live Binance data.

This example:
1. Connects to Binance WebSocket for real-time price data
2. Maintains a rolling window of candles
3. Runs pattern detection on each new candle
4. Prints detected patterns and trading signals in real-time

Usage:
    python examples/live_pattern_detection.py --symbol BTC/USDT --timeframe 1m

    Optional arguments:
        --symbol: Trading pair (default: BTC/USDT)
        --timeframe: Candle timeframe (default: 1m)
        --window-size: Number of candles to keep (default: 100)
        --testnet: Use Binance testnet
"""

import argparse
import asyncio
from collections import deque
from datetime import datetime
from typing import Any, Dict

import numpy as np
from loguru import logger

from src.core.types import OHLCV, SignalType, Timeframe
from src.exchanges.binance import BinanceConnector, BinanceMarket
from src.patterns.advanced import (ADXPattern, ParabolicSARPattern,
                                   StochasticPattern)
from src.patterns.optimized import (OptimizedBollingerBandsPattern,
                                    OptimizedMACDPattern, OptimizedRSIPattern)


class LivePatternDetector:
    """
    Real-time pattern detection system.

    Maintains a rolling window of candles and runs pattern detection
    on each new candle received from the exchange.
    """

    def __init__(
        self,
        symbol: str = "BTC/USDT",
        timeframe: Timeframe = Timeframe.ONE_MINUTE,
        window_size: int = 100,
        testnet: bool = False,
    ):
        """
        Initialize live pattern detector.

        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
            timeframe: Candle timeframe
            window_size: Number of candles to keep in memory
            testnet: Use Binance testnet
        """
        self.symbol = symbol
        self.timeframe = timeframe
        self.window_size = window_size
        self.testnet = testnet

        # Initialize Binance connector
        self.connector = BinanceConnector(
            market=BinanceMarket.SPOT,
            testnet=testnet,
        )

        # Initialize pattern detectors
        self.detectors = {
            "RSI": OptimizedRSIPattern(),
            "MACD": OptimizedMACDPattern(),
            "Bollinger Bands": OptimizedBollingerBandsPattern(),
            "ADX": ADXPattern(),
            "Parabolic SAR": ParabolicSARPattern(),
            "Stochastic": StochasticPattern(),
        }

        # Rolling window of candles
        self.candle_window = deque(maxlen=window_size)

        # Statistics
        self.stats = {
            "candles_received": 0,
            "patterns_detected": 0,
            "buy_signals": 0,
            "sell_signals": 0,
            "hold_signals": 0,
            "start_time": datetime.now(),
        }

        logger.info(f"Initialized LivePatternDetector for {symbol} {timeframe}")
        logger.info(f"Using {len(self.detectors)} pattern detectors")

    async def start(self):
        """Start live pattern detection."""
        logger.info("=" * 80)
        logger.info("LIVE PATTERN DETECTION - STARTING")
        logger.info("=" * 80)
        logger.info(f"Symbol: {self.symbol}")
        logger.info(f"Timeframe: {self.timeframe.value}")
        logger.info(f"Window Size: {self.window_size} candles")
        logger.info(f"Detectors: {', '.join(self.detectors.keys())}")
        logger.info("=" * 80)

        # Load initial historical data
        await self._load_initial_data()

        # Subscribe to real-time candles
        logger.info(f"Subscribing to {self.symbol} {self.timeframe.value} stream...")

        await self.connector.subscribe_klines(
            symbol=self.symbol,
            timeframe=self.timeframe,
            callback=self._on_candle,
        )

        # Keep running
        logger.info("🟢 LIVE - Waiting for candles...")
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("\n" + "=" * 80)
            logger.info("Shutting down...")
            await self.stop()

    async def _load_initial_data(self):
        """Load initial historical data to populate the window."""
        logger.info(f"Loading initial {self.window_size} candles...")

        ohlcv = await self.connector.get_ohlcv(
            symbol=self.symbol,
            timeframe=self.timeframe,
            limit=self.window_size,
        )

        # Populate window
        for i in range(len(ohlcv)):
            candle = {
                "timestamp": int(ohlcv.timestamps[i]),
                "open": float(ohlcv.open[i]),
                "high": float(ohlcv.high[i]),
                "low": float(ohlcv.low[i]),
                "close": float(ohlcv.close[i]),
                "volume": float(ohlcv.volume[i]),
            }
            self.candle_window.append(candle)

        logger.info(f"✓ Loaded {len(self.candle_window)} historical candles")

        # Run initial pattern detection
        await self._detect_patterns()

    async def _on_candle(self, candle_data: Dict[str, Any]):
        """
        Handle incoming candle data from WebSocket.

        Args:
            candle_data: Candle data from Binance WebSocket
        """
        # Only process closed candles
        if not candle_data.get("is_closed", False):
            return

        # Add to window
        self.candle_window.append(
            {
                "timestamp": candle_data["timestamp"],
                "open": candle_data["open"],
                "high": candle_data["high"],
                "low": candle_data["low"],
                "close": candle_data["close"],
                "volume": candle_data["volume"],
            }
        )

        self.stats["candles_received"] += 1

        # Log candle
        timestamp = datetime.fromtimestamp(candle_data["timestamp"] / 1000)
        logger.info("")
        logger.info("─" * 80)
        logger.info(f"📊 NEW CANDLE - {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(
            f"   O: ${candle_data['open']:.2f}  H: ${candle_data['high']:.2f}  "
            f"L: ${candle_data['low']:.2f}  C: ${candle_data['close']:.2f}  "
            f"V: {candle_data['volume']:.2f}"
        )

        # Detect patterns
        await self._detect_patterns()

    async def _detect_patterns(self):
        """Run pattern detection on current window."""
        if len(self.candle_window) < 50:
            # Need minimum data for patterns
            return

        # Convert window to OHLCV
        ohlcv = self._window_to_ohlcv()

        # Run all detectors
        all_patterns = []

        for name, detector in self.detectors.items():
            try:
                patterns = detector.detect(ohlcv)
                if patterns:
                    all_patterns.extend([(name, p) for p in patterns])
            except Exception as e:
                logger.error(f"Error in {name} detector: {e}")

        # Process detected patterns
        if all_patterns:
            self.stats["patterns_detected"] += len(all_patterns)

            logger.info("")
            logger.info(f"🔍 PATTERNS DETECTED: {len(all_patterns)}")
            logger.info("─" * 80)

            # Group by signal type
            buy_patterns = []
            sell_patterns = []
            hold_patterns = []

            for detector_name, pattern in all_patterns:
                if pattern.signal == SignalType.BUY:
                    buy_patterns.append((detector_name, pattern))
                    self.stats["buy_signals"] += 1
                elif pattern.signal == SignalType.SELL:
                    sell_patterns.append((detector_name, pattern))
                    self.stats["sell_signals"] += 1
                else:
                    hold_patterns.append((detector_name, pattern))
                    self.stats["hold_signals"] += 1

            # Display patterns
            if buy_patterns:
                logger.info("📈 BUY SIGNALS:")
                for detector_name, pattern in buy_patterns:
                    self._print_pattern(detector_name, pattern)

            if sell_patterns:
                logger.info("📉 SELL SIGNALS:")
                for detector_name, pattern in sell_patterns:
                    self._print_pattern(detector_name, pattern)

            if hold_patterns:
                logger.info("⏸️  HOLD SIGNALS:")
                for detector_name, pattern in hold_patterns:
                    self._print_pattern(detector_name, pattern)

            # Signal consensus
            self._print_consensus(buy_patterns, sell_patterns, hold_patterns)

        # Print statistics
        self._print_stats()

    def _print_pattern(self, detector_name: str, pattern):
        """Print pattern details."""
        logger.info(f"   [{detector_name}] {pattern.pattern_name}")
        logger.info(f"      Confidence: {pattern.confidence:.1%}")
        if pattern.metadata:
            metadata_str = ", ".join(
                f"{k}={v:.2f}" if isinstance(v, (int, float)) else f"{k}={v}"
                for k, v in list(pattern.metadata.items())[:3]  # Show first 3
            )
            logger.info(f"      Data: {metadata_str}")

    def _print_consensus(self, buy_patterns, sell_patterns, hold_patterns):
        """Print signal consensus analysis."""
        total = len(buy_patterns) + len(sell_patterns) + len(hold_patterns)
        if total == 0:
            return

        buy_pct = len(buy_patterns) / total * 100
        sell_pct = len(sell_patterns) / total * 100
        hold_pct = len(hold_patterns) / total * 100

        logger.info("")
        logger.info("📊 CONSENSUS:")
        logger.info(f"   BUY:  {len(buy_patterns)}/{total} ({buy_pct:.0f}%)")
        logger.info(f"   SELL: {len(sell_patterns)}/{total} ({sell_pct:.0f}%)")
        logger.info(f"   HOLD: {len(hold_patterns)}/{total} ({hold_pct:.0f}%)")

        # Decision
        if buy_pct > 50:
            logger.info("   ⚡ CONSENSUS: BUY")
        elif sell_pct > 50:
            logger.info("   ⚡ CONSENSUS: SELL")
        else:
            logger.info("   ⚡ CONSENSUS: HOLD (no clear majority)")

    def _print_stats(self):
        """Print session statistics."""
        runtime = (datetime.now() - self.stats["start_time"]).total_seconds()
        logger.info("")
        logger.info(f"📈 SESSION STATS:")
        logger.info(f"   Runtime: {runtime:.0f}s")
        logger.info(f"   Candles: {self.stats['candles_received']}")
        logger.info(f"   Patterns: {self.stats['patterns_detected']}")
        logger.info(
            f"   Signals: 📈{self.stats['buy_signals']} BUY | "
            f"📉{self.stats['sell_signals']} SELL | "
            f"⏸️{self.stats['hold_signals']} HOLD"
        )

    def _window_to_ohlcv(self) -> OHLCV:
        """Convert candle window to OHLCV structure."""
        candles = list(self.candle_window)

        return OHLCV(
            timestamps=np.array([c["timestamp"] / 1000 for c in candles]),
            open=np.array([c["open"] for c in candles]),
            high=np.array([c["high"] for c in candles]),
            low=np.array([c["low"] for c in candles]),
            close=np.array([c["close"] for c in candles]),
            volume=np.array([c["volume"] for c in candles]),
        )

    async def stop(self):
        """Stop live pattern detection."""
        logger.info("Closing connections...")
        await self.connector.close()
        logger.info("✓ Stopped")

        # Final stats
        logger.info("")
        logger.info("=" * 80)
        logger.info("FINAL STATISTICS")
        logger.info("=" * 80)
        self._print_stats()
        logger.info("=" * 80)


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Live Pattern Detection")
    parser.add_argument(
        "--symbol", type=str, default="BTC/USDT", help="Trading pair (e.g., BTC/USDT)"
    )
    parser.add_argument(
        "--timeframe",
        type=str,
        default="1m",
        help="Candle timeframe (1m, 5m, 15m, 1h, etc.)",
    )
    parser.add_argument(
        "--window-size",
        type=int,
        default=100,
        help="Number of candles to keep in memory",
    )
    parser.add_argument("--testnet", action="store_true", help="Use Binance testnet")

    args = parser.parse_args()

    # Map timeframe string to enum
    timeframe_map = {
        "1m": Timeframe.ONE_MINUTE,
        "5m": Timeframe.FIVE_MINUTES,
        "15m": Timeframe.FIFTEEN_MINUTES,
        "30m": Timeframe.THIRTY_MINUTES,
        "1h": Timeframe.ONE_HOUR,
        "4h": Timeframe.FOUR_HOURS,
        "1d": Timeframe.ONE_DAY,
        "1w": Timeframe.ONE_WEEK,
    }

    timeframe = timeframe_map.get(args.timeframe, Timeframe.ONE_MINUTE)

    # Create and start detector
    detector = LivePatternDetector(
        symbol=args.symbol,
        timeframe=timeframe,
        window_size=args.window_size,
        testnet=args.testnet,
    )

    await detector.start()


if __name__ == "__main__":
    asyncio.run(main())
