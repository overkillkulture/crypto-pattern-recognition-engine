"""
Binance Exchange Connector - Production-grade implementation.

Features:
- REST API with rate limiting and retry logic
- WebSocket streaming for real-time data
- Historical data bulk fetching
- Exponential backoff for errors
- Support for Spot, Futures, and Margin trading
- Comprehensive error handling
"""

import asyncio
import time
from collections import deque
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np

import ccxt.async_support as ccxt
from loguru import logger

from src.core.types import OHLCV, Timeframe
from src.streaming.websocket import WebSocketClient, BinanceWebSocketHandler


class BinanceMarket(str, Enum):
    """Binance market types."""
    SPOT = "spot"
    FUTURES_USD_M = "futures_usd_m"  # USDT-Margined Futures
    FUTURES_COIN_M = "futures_coin_m"  # Coin-Margined Futures
    MARGIN = "margin"


@dataclass
class RateLimitConfig:
    """Rate limiting configuration."""
    requests_per_minute: int = 1200  # Binance default: 1200/min
    weight_per_minute: int = 6000     # Weight-based limit
    orders_per_second: int = 10       # Order rate limit
    orders_per_day: int = 200000      # Daily order limit


@dataclass
class RetryConfig:
    """Retry configuration for failed requests."""
    max_retries: int = 4
    base_delay: float = 1.0           # Initial delay in seconds
    max_delay: float = 32.0           # Maximum delay
    exponential_base: float = 2.0     # Exponential backoff multiplier


class RateLimiter:
    """
    Token bucket rate limiter with weight support.

    Implements Binance's request weight system for API rate limiting.
    """

    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.request_times: deque = deque()
        self.weight_used: deque = deque()
        self.lock = asyncio.Lock()

    async def acquire(self, weight: int = 1) -> None:
        """
        Acquire rate limit token.

        Args:
            weight: Request weight (Binance assigns different weights to endpoints)
        """
        async with self.lock:
            now = time.time()
            minute_ago = now - 60

            # Remove old entries
            while self.request_times and self.request_times[0] < minute_ago:
                self.request_times.popleft()
            while self.weight_used and self.weight_used[0][0] < minute_ago:
                self.weight_used.popleft()

            # Calculate current usage
            current_requests = len(self.request_times)
            current_weight = sum(w for _, w in self.weight_used)

            # Check if we need to wait
            requests_available = self.config.requests_per_minute - current_requests
            weight_available = self.config.weight_per_minute - current_weight

            if requests_available <= 0 or weight_available < weight:
                # Calculate wait time
                if self.request_times:
                    oldest_request = self.request_times[0]
                    wait_time = 61 - (now - oldest_request)
                    if wait_time > 0:
                        logger.debug(f"Rate limit reached, waiting {wait_time:.2f}s")
                        await asyncio.sleep(wait_time)
                        # Retry acquisition after waiting
                        return await self.acquire(weight)

            # Record this request
            self.request_times.append(now)
            self.weight_used.append((now, weight))


class BinanceConnector:
    """
    Production-grade Binance connector.

    Supports:
    - REST API with intelligent rate limiting
    - WebSocket streaming
    - Bulk historical data fetching
    - Automatic retry with exponential backoff
    - Multiple market types (spot, futures, margin)

    Example:
        connector = BinanceConnector(
            api_key="your_key",
            api_secret="your_secret"
        )

        # Fetch historical data
        ohlcv = await connector.get_historical_ohlcv(
            symbol="BTC/USDT",
            timeframe=Timeframe.ONE_HOUR,
            since=datetime.now() - timedelta(days=30)
        )

        # Stream real-time data
        await connector.subscribe_klines(
            symbol="BTC/USDT",
            timeframe=Timeframe.ONE_MINUTE,
            callback=on_candle
        )
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        market: BinanceMarket = BinanceMarket.SPOT,
        testnet: bool = False,
        rate_limit_config: Optional[RateLimitConfig] = None,
        retry_config: Optional[RetryConfig] = None,
    ):
        """
        Initialize Binance connector.

        Args:
            api_key: Binance API key (optional for public endpoints)
            api_secret: Binance API secret
            market: Market type (spot, futures, margin)
            testnet: Use testnet instead of production
            rate_limit_config: Custom rate limiting config
            retry_config: Custom retry config
        """
        self.market = market
        self.testnet = testnet

        # Configuration
        self.rate_limit_config = rate_limit_config or RateLimitConfig()
        self.retry_config = retry_config or RetryConfig()

        # Rate limiter
        self.rate_limiter = RateLimiter(self.rate_limit_config)

        # Initialize exchange
        self.exchange = self._create_exchange(api_key, api_secret)

        # WebSocket clients
        self.ws_clients: Dict[str, WebSocketClient] = {}

        # Statistics
        self.stats = {
            'requests_sent': 0,
            'requests_failed': 0,
            'retries_performed': 0,
            'rate_limits_hit': 0,
            'websocket_reconnects': 0,
        }

        logger.info(f"Initialized BinanceConnector (market={market}, testnet={testnet})")

    def _create_exchange(self, api_key: Optional[str], api_secret: Optional[str]) -> ccxt.Exchange:
        """Create CCXT exchange instance."""
        config = {
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': False,  # We handle rate limiting ourselves
            'options': {
                'defaultType': self.market.value,
            }
        }

        if self.testnet:
            config['urls'] = {
                'api': {
                    'public': 'https://testnet.binance.vision/api',
                    'private': 'https://testnet.binance.vision/api',
                }
            }

        return ccxt.binance(config)

    async def _request_with_retry(
        self,
        func: Callable,
        *args,
        weight: int = 1,
        **kwargs
    ) -> Any:
        """
        Execute request with rate limiting and exponential backoff retry.

        Args:
            func: Async function to call
            weight: Request weight for rate limiting
            *args, **kwargs: Arguments to pass to function

        Returns:
            Result from function call
        """
        for attempt in range(self.retry_config.max_retries + 1):
            try:
                # Apply rate limiting
                await self.rate_limiter.acquire(weight=weight)

                # Execute request
                result = await func(*args, **kwargs)
                self.stats['requests_sent'] += 1

                return result

            except ccxt.RateLimitExceeded as e:
                self.stats['rate_limits_hit'] += 1
                logger.warning(f"Rate limit exceeded: {e}")

                # Wait longer for rate limit errors
                delay = min(
                    self.retry_config.base_delay * (2 ** attempt),
                    self.retry_config.max_delay
                )
                logger.info(f"Waiting {delay}s before retry (rate limit)")
                await asyncio.sleep(delay)

            except (ccxt.NetworkError, ccxt.ExchangeError) as e:
                self.stats['requests_failed'] += 1

                if attempt >= self.retry_config.max_retries:
                    logger.error(f"Max retries exceeded: {e}")
                    raise

                self.stats['retries_performed'] += 1

                # Exponential backoff
                delay = min(
                    self.retry_config.base_delay * (self.retry_config.exponential_base ** attempt),
                    self.retry_config.max_delay
                )

                logger.warning(f"Request failed (attempt {attempt + 1}/{self.retry_config.max_retries + 1}): {e}")
                logger.info(f"Retrying in {delay:.2f}s...")
                await asyncio.sleep(delay)

            except Exception as e:
                self.stats['requests_failed'] += 1
                logger.error(f"Unexpected error: {e}")
                raise

        raise RuntimeError("Max retries exceeded")

    async def get_ohlcv(
        self,
        symbol: str,
        timeframe: Timeframe,
        since: Optional[datetime] = None,
        limit: int = 500,
    ) -> OHLCV:
        """
        Fetch OHLCV data for a symbol.

        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
            timeframe: Candle timeframe
            since: Start time (optional)
            limit: Number of candles (max 1000)

        Returns:
            OHLCV data structure
        """
        since_ms = None
        if since:
            since_ms = int(since.timestamp() * 1000)

        # Weight: 1 for default, higher for large limits
        weight = 1 if limit <= 100 else 2

        data = await self._request_with_retry(
            self.exchange.fetch_ohlcv,
            symbol,
            timeframe.value,
            since=since_ms,
            limit=limit,
            weight=weight,
        )

        # Convert to OHLCV structure
        if not data:
            logger.warning(f"No data returned for {symbol} {timeframe}")
            return OHLCV(
                timestamps=np.array([]),
                open=np.array([]),
                high=np.array([]),
                low=np.array([]),
                close=np.array([]),
                volume=np.array([]),
            )

        timestamps = np.array([candle[0] / 1000 for candle in data])
        opens = np.array([candle[1] for candle in data])
        highs = np.array([candle[2] for candle in data])
        lows = np.array([candle[3] for candle in data])
        closes = np.array([candle[4] for candle in data])
        volumes = np.array([candle[5] for candle in data])

        logger.debug(f"Fetched {len(data)} candles for {symbol} {timeframe}")

        return OHLCV(
            timestamps=timestamps,
            open=opens,
            high=highs,
            low=lows,
            close=closes,
            volume=volumes,
        )

    async def get_historical_ohlcv(
        self,
        symbol: str,
        timeframe: Timeframe,
        since: datetime,
        until: Optional[datetime] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> OHLCV:
        """
        Fetch large historical OHLCV dataset in chunks.

        Automatically handles pagination for datasets larger than 1000 candles.

        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
            timeframe: Candle timeframe
            since: Start time
            until: End time (optional, defaults to now)
            progress_callback: Optional callback(current, total) for progress updates

        Returns:
            Complete OHLCV data structure
        """
        if until is None:
            until = datetime.now()

        # Calculate timeframe duration
        timeframe_minutes = {
            Timeframe.ONE_MINUTE: 1,
            Timeframe.FIVE_MINUTES: 5,
            Timeframe.FIFTEEN_MINUTES: 15,
            Timeframe.THIRTY_MINUTES: 30,
            Timeframe.ONE_HOUR: 60,
            Timeframe.FOUR_HOURS: 240,
            Timeframe.ONE_DAY: 1440,
            Timeframe.ONE_WEEK: 10080,
        }

        minutes = timeframe_minutes.get(timeframe, 60)
        candle_duration = timedelta(minutes=minutes)

        # Calculate expected candles
        total_duration = until - since
        expected_candles = int(total_duration / candle_duration)

        logger.info(f"Fetching {expected_candles} candles for {symbol} {timeframe} from {since} to {until}")

        # Fetch in chunks
        all_data = []
        current_since = since
        chunk_size = 1000  # Binance max

        chunk_num = 0
        while current_since < until:
            chunk_num += 1

            # Fetch chunk
            ohlcv = await self.get_ohlcv(
                symbol=symbol,
                timeframe=timeframe,
                since=current_since,
                limit=chunk_size,
            )

            if len(ohlcv) == 0:
                logger.warning(f"No data returned for chunk starting at {current_since}")
                break

            # Filter data within range
            mask = ohlcv.timestamps <= until.timestamp()
            filtered_ohlcv = OHLCV(
                timestamps=ohlcv.timestamps[mask],
                open=ohlcv.open[mask],
                high=ohlcv.high[mask],
                low=ohlcv.low[mask],
                close=ohlcv.close[mask],
                volume=ohlcv.volume[mask],
            )

            all_data.append(filtered_ohlcv)

            # Progress update
            fetched_count = sum(len(chunk) for chunk in all_data)
            if progress_callback:
                progress_callback(fetched_count, expected_candles)

            logger.debug(f"Chunk {chunk_num}: {len(filtered_ohlcv)} candles (total: {fetched_count})")

            # Update cursor
            if len(ohlcv) < chunk_size:
                # Got less than requested, we're done
                break

            # Move to next chunk
            last_timestamp = datetime.fromtimestamp(ohlcv.timestamps[-1])
            current_since = last_timestamp + candle_duration

            # Small delay to avoid hammering the API
            await asyncio.sleep(0.1)

        # Combine all chunks
        if not all_data:
            logger.warning("No historical data fetched")
            return OHLCV(
                timestamps=np.array([]),
                open=np.array([]),
                high=np.array([]),
                low=np.array([]),
                close=np.array([]),
                volume=np.array([]),
            )

        combined = OHLCV(
            timestamps=np.concatenate([chunk.timestamps for chunk in all_data]),
            open=np.concatenate([chunk.open for chunk in all_data]),
            high=np.concatenate([chunk.high for chunk in all_data]),
            low=np.concatenate([chunk.low for chunk in all_data]),
            close=np.concatenate([chunk.close for chunk in all_data]),
            volume=np.concatenate([chunk.volume for chunk in all_data]),
        )

        # Remove duplicates (can happen at chunk boundaries)
        unique_indices = np.unique(combined.timestamps, return_index=True)[1]
        combined = OHLCV(
            timestamps=combined.timestamps[unique_indices],
            open=combined.open[unique_indices],
            high=combined.high[unique_indices],
            low=combined.low[unique_indices],
            close=combined.close[unique_indices],
            volume=combined.volume[unique_indices],
        )

        logger.info(f"Fetched {len(combined)} total candles for {symbol} {timeframe}")

        return combined

    async def get_latest_price(self, symbol: str) -> float:
        """
        Get latest price for a symbol.

        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')

        Returns:
            Latest price
        """
        ticker = await self._request_with_retry(
            self.exchange.fetch_ticker,
            symbol,
            weight=1,
        )

        return ticker['last']

    async def get_24h_stats(self, symbol: str) -> Dict[str, Any]:
        """
        Get 24-hour statistics for a symbol.

        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')

        Returns:
            24h statistics including volume, high, low, change
        """
        ticker = await self._request_with_retry(
            self.exchange.fetch_ticker,
            symbol,
            weight=1,
        )

        return {
            'symbol': symbol,
            'last': ticker['last'],
            'high': ticker['high'],
            'low': ticker['low'],
            'volume': ticker['quoteVolume'],
            'change_percent': ticker['percentage'],
            'timestamp': datetime.fromtimestamp(ticker['timestamp'] / 1000),
        }

    async def subscribe_klines(
        self,
        symbol: str,
        timeframe: Timeframe,
        callback: Callable[[Dict[str, Any]], None],
    ) -> str:
        """
        Subscribe to real-time kline/candlestick data via WebSocket.

        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
            timeframe: Candle timeframe
            callback: Callback function for new candles

        Returns:
            Subscription ID (for unsubscribing)
        """
        # Convert symbol format
        binance_symbol = symbol.replace('/', '').lower()

        # Build stream name
        stream_name = f"{binance_symbol}@kline_{timeframe.value}"

        # WebSocket URL
        ws_url = "wss://stream.binance.com:9443/ws"
        if self.testnet:
            ws_url = "wss://testnet.binance.vision/ws"

        # Create handler
        handler = BinanceWebSocketHandler(on_candle=callback)

        # Create WebSocket client
        client = WebSocketClient(
            url=ws_url,
            handler=handler,
            reconnect=True,
            max_reconnect_attempts=10,
        )

        # Store client
        subscription_id = stream_name
        self.ws_clients[subscription_id] = client

        # Connect and subscribe
        asyncio.create_task(self._start_websocket(client, [stream_name]))

        logger.info(f"Subscribed to {stream_name}")

        return subscription_id

    async def _start_websocket(self, client: WebSocketClient, streams: List[str]):
        """Start WebSocket client and subscribe to streams."""
        try:
            await client.connect()
            await client.subscribe(streams)
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            self.stats['websocket_reconnects'] += 1

    async def unsubscribe(self, subscription_id: str):
        """
        Unsubscribe from a WebSocket stream.

        Args:
            subscription_id: ID returned from subscribe_klines
        """
        if subscription_id in self.ws_clients:
            client = self.ws_clients[subscription_id]
            await client.disconnect()
            del self.ws_clients[subscription_id]
            logger.info(f"Unsubscribed from {subscription_id}")

    async def get_exchange_info(self) -> Dict[str, Any]:
        """
        Get exchange information and trading rules.

        Returns:
            Exchange metadata including limits, fees, symbols
        """
        info = await self._request_with_retry(
            self.exchange.fetch_markets,
            weight=10,
        )

        return {
            'markets_count': len(info),
            'markets': info,
            'rate_limits': self.exchange.rateLimit,
        }

    def get_stats(self) -> Dict[str, Any]:
        """
        Get connector statistics.

        Returns:
            Statistics including request counts, errors, retries
        """
        return {
            **self.stats,
            'success_rate': (
                (self.stats['requests_sent'] - self.stats['requests_failed'])
                / max(self.stats['requests_sent'], 1)
            ) * 100,
        }

    async def close(self):
        """Close all connections."""
        # Close all WebSocket clients
        for client in self.ws_clients.values():
            await client.disconnect()
        self.ws_clients.clear()

        # Close exchange connection
        await self.exchange.close()

        logger.info("BinanceConnector closed")
