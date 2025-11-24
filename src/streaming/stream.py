"""Real-time streaming pattern detection engine."""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
from collections import deque
import numpy as np

from src.core.types import OHLCV, PatternResult, Exchange, Timeframe
from src.core.interfaces import PatternDetector
from src.streaming.websocket import WebSocketClient, WebSocketHandler

logger = logging.getLogger(__name__)


@dataclass
class StreamConfig:
    """Configuration for streaming engine."""

    symbol: str
    exchange: Exchange
    timeframe: Timeframe
    buffer_size: int = 500  # Number of candles to keep in buffer
    update_interval: float = 1.0  # Minimum seconds between pattern detections


class CandleBuffer:
    """
    Rolling buffer for OHLCV candle data.

    Maintains a fixed-size buffer of recent candles for pattern detection.
    """

    def __init__(self, max_size: int = 500):
        """
        Initialize candle buffer.

        Args:
            max_size: Maximum number of candles to store
        """
        self.max_size = max_size
        self.timestamps = deque(maxlen=max_size)
        self.open = deque(maxlen=max_size)
        self.high = deque(maxlen=max_size)
        self.low = deque(maxlen=max_size)
        self.close = deque(maxlen=max_size)
        self.volume = deque(maxlen=max_size)

    def add_candle(
        self,
        timestamp: float,
        open_price: float,
        high_price: float,
        low_price: float,
        close_price: float,
        volume: float,
    ):
        """Add a new candle to the buffer."""
        self.timestamps.append(timestamp)
        self.open.append(open_price)
        self.high.append(high_price)
        self.low.append(low_price)
        self.close.append(close_price)
        self.volume.append(volume)

    def update_last_candle(
        self,
        high_price: float,
        low_price: float,
        close_price: float,
        volume: float,
    ):
        """Update the most recent (current) candle."""
        if not self.timestamps:
            return

        self.high[-1] = max(self.high[-1], high_price)
        self.low[-1] = min(self.low[-1], low_price)
        self.close[-1] = close_price
        self.volume[-1] = volume

    def to_ohlcv(self) -> OHLCV:
        """Convert buffer to OHLCV format."""
        return OHLCV(
            timestamps=np.array(list(self.timestamps)),
            open=np.array(list(self.open)),
            high=np.array(list(self.high)),
            low=np.array(list(self.low)),
            close=np.array(list(self.close)),
            volume=np.array(list(self.volume)),
        )

    def size(self) -> int:
        """Get current buffer size."""
        return len(self.timestamps)

    def is_full(self) -> bool:
        """Check if buffer is at capacity."""
        return len(self.timestamps) >= self.max_size

    def clear(self):
        """Clear the buffer."""
        self.timestamps.clear()
        self.open.clear()
        self.high.clear()
        self.low.clear()
        self.close.clear()
        self.volume.clear()


class StreamingPatternHandler(WebSocketHandler):
    """WebSocket handler that performs real-time pattern detection."""

    def __init__(
        self,
        config: StreamConfig,
        pattern_detectors: List[PatternDetector],
        on_pattern: Optional[Callable[[PatternResult], None]] = None,
    ):
        """
        Initialize streaming pattern handler.

        Args:
            config: Stream configuration
            pattern_detectors: List of pattern detectors
            on_pattern: Callback for detected patterns
        """
        self.config = config
        self.pattern_detectors = pattern_detectors
        self.on_pattern = on_pattern

        self.candle_buffer = CandleBuffer(max_size=config.buffer_size)
        self.last_detection_time = datetime.utcnow()
        self.current_candle_timestamp: Optional[int] = None

    async def on_message(self, data: Dict[str, Any]):
        """Process incoming WebSocket message."""
        try:
            # Handle kline (candlestick) data
            if 'e' in data and data['e'] == 'kline':
                await self._handle_kline(data['k'])

        except Exception as e:
            logger.error(f"Error processing stream message: {e}")

    async def _handle_kline(self, kline: Dict[str, Any]):
        """Process kline data and detect patterns."""
        timestamp = kline['t'] / 1000  # Convert ms to seconds
        open_price = float(kline['o'])
        high_price = float(kline['h'])
        low_price = float(kline['l'])
        close_price = float(kline['c'])
        volume = float(kline['v'])
        is_closed = kline['x']

        # Check if this is a new candle
        if self.current_candle_timestamp != kline['t']:
            # New candle - add to buffer
            if self.current_candle_timestamp is not None:
                # Previous candle closed, add it
                self.candle_buffer.add_candle(
                    timestamp=self.current_candle_timestamp / 1000,
                    open_price=open_price,
                    high_price=high_price,
                    low_price=low_price,
                    close_price=close_price,
                    volume=volume,
                )

            self.current_candle_timestamp = kline['t']

        else:
            # Update current candle
            self.candle_buffer.update_last_candle(
                high_price=high_price,
                low_price=low_price,
                close_price=close_price,
                volume=volume,
            )

        # Run pattern detection on closed candles
        if is_closed:
            await self._run_pattern_detection()

    async def _run_pattern_detection(self):
        """Run pattern detection on buffered data."""
        # Throttle detection
        now = datetime.utcnow()
        elapsed = (now - self.last_detection_time).total_seconds()

        if elapsed < self.config.update_interval:
            return

        if self.candle_buffer.size() < 50:
            logger.debug("Insufficient data for pattern detection")
            return

        try:
            # Convert buffer to OHLCV
            ohlcv = self.candle_buffer.to_ohlcv()

            # Run all pattern detectors
            detected_patterns: List[PatternResult] = []

            for detector in self.pattern_detectors:
                try:
                    patterns = await detector.detect_patterns(
                        symbol=self.config.symbol,
                        timeframe=self.config.timeframe,
                        data=ohlcv,
                    )
                    detected_patterns.extend(patterns)

                except Exception as e:
                    logger.error(f"Pattern detector {detector.__class__.__name__} failed: {e}")

            # Notify on new patterns
            if detected_patterns:
                logger.info(f"Detected {len(detected_patterns)} patterns in real-time")

                for pattern in detected_patterns:
                    if self.on_pattern:
                        try:
                            await self.on_pattern(pattern)
                        except Exception as e:
                            logger.error(f"Pattern callback failed: {e}")

            self.last_detection_time = now

        except Exception as e:
            logger.error(f"Pattern detection failed: {e}")


class StreamingEngine:
    """
    Real-time streaming pattern detection engine.

    Connects to exchange WebSocket and performs pattern detection on live data.

    Example:
        config = StreamConfig(
            symbol="BTC/USDT",
            exchange=Exchange.BINANCE,
            timeframe=Timeframe.ONE_MINUTE,
        )

        engine = StreamingEngine(config)
        engine.add_pattern_detector(RSIPattern())

        await engine.start()
    """

    def __init__(self, config: StreamConfig):
        """
        Initialize streaming engine.

        Args:
            config: Stream configuration
        """
        self.config = config
        self.pattern_detectors: List[PatternDetector] = []
        self.pattern_callbacks: List[Callable] = []

        self.ws_client: Optional[WebSocketClient] = None
        self.handler: Optional[StreamingPatternHandler] = None
        self.is_running = False

    def add_pattern_detector(self, detector: PatternDetector):
        """
        Add a pattern detector.

        Args:
            detector: Pattern detector to add
        """
        self.pattern_detectors.append(detector)

    def on_pattern(self, callback: Callable[[PatternResult], None]):
        """
        Register callback for pattern detection.

        Args:
            callback: Callback function
        """
        self.pattern_callbacks.append(callback)

    async def start(self):
        """Start streaming and pattern detection."""
        if self.is_running:
            logger.warning("Streaming engine already running")
            return

        logger.info(
            f"Starting streaming engine for {self.config.symbol} "
            f"on {self.config.exchange.value} ({self.config.timeframe.value})"
        )

        # Create handler
        self.handler = StreamingPatternHandler(
            config=self.config,
            pattern_detectors=self.pattern_detectors,
            on_pattern=self._handle_pattern,
        )

        # Create WebSocket URL (Binance example)
        ws_url = self._build_websocket_url()

        # Create WebSocket client
        self.ws_client = WebSocketClient(
            url=ws_url,
            handler=self.handler,
            reconnect=True,
        )

        # Connect
        self.is_running = True
        await self.ws_client.connect()

    async def stop(self):
        """Stop streaming and pattern detection."""
        if not self.is_running:
            return

        logger.info("Stopping streaming engine")

        self.is_running = False

        if self.ws_client:
            await self.ws_client.disconnect()

        logger.info("Streaming engine stopped")

    def _build_websocket_url(self) -> str:
        """Build WebSocket URL for exchange."""
        # Binance WebSocket URLs
        if self.config.exchange == Exchange.BINANCE:
            symbol = self.config.symbol.replace('/', '').lower()
            interval = self._timeframe_to_binance_interval(self.config.timeframe)
            return f"wss://stream.binance.com:9443/ws/{symbol}@kline_{interval}"

        # Other exchanges can be added here
        raise ValueError(f"Unsupported exchange: {self.config.exchange}")

    def _timeframe_to_binance_interval(self, timeframe: Timeframe) -> str:
        """Convert Timeframe to Binance interval string."""
        mapping = {
            Timeframe.ONE_MINUTE: '1m',
            Timeframe.FIVE_MINUTES: '5m',
            Timeframe.FIFTEEN_MINUTES: '15m',
            Timeframe.ONE_HOUR: '1h',
            Timeframe.FOUR_HOURS: '4h',
            Timeframe.ONE_DAY: '1d',
        }
        return mapping.get(timeframe, '1h')

    async def _handle_pattern(self, pattern: PatternResult):
        """Handle detected pattern by notifying all callbacks."""
        for callback in self.pattern_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(pattern)
                else:
                    callback(pattern)
            except Exception as e:
                logger.error(f"Pattern callback failed: {e}")
