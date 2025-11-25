"""WebSocket client for real-time data streaming."""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException

logger = logging.getLogger(__name__)


class WebSocketHandler(ABC):
    """Abstract base class for WebSocket message handlers."""

    @abstractmethod
    async def on_message(self, data: Dict[str, Any]):
        """
        Handle incoming WebSocket message.

        Args:
            data: Parsed message data
        """

    async def on_error(self, error: Exception):
        """
        Handle WebSocket error.

        Args:
            error: Error that occurred
        """
        logger.error(f"WebSocket error: {error}")

    async def on_connect(self):
        """Called when WebSocket connection is established."""
        logger.info("WebSocket connected")

    async def on_disconnect(self):
        """Called when WebSocket connection is closed."""
        logger.info("WebSocket disconnected")


class WebSocketClient:
    """
    WebSocket client for real-time data streaming.

    Supports automatic reconnection and message handling.

    Example:
        async def handle_message(data):
            print(f"Received: {data}")

        client = WebSocketClient(
            url="wss://stream.binance.com/ws",
            handler=MyHandler(),
        )
        await client.connect()
    """

    def __init__(
        self,
        url: str,
        handler: WebSocketHandler,
        reconnect: bool = True,
        reconnect_delay: float = 5.0,
        max_reconnect_attempts: int = 10,
        ping_interval: float = 20.0,
        ping_timeout: float = 10.0,
    ):
        """
        Initialize WebSocket client.

        Args:
            url: WebSocket URL
            handler: Message handler
            reconnect: Whether to automatically reconnect
            reconnect_delay: Delay between reconnection attempts
            max_reconnect_attempts: Maximum reconnection attempts
            ping_interval: Interval between ping messages
            ping_timeout: Timeout for ping response
        """
        self.url = url
        self.handler = handler
        self.reconnect = reconnect
        self.reconnect_delay = reconnect_delay
        self.max_reconnect_attempts = max_reconnect_attempts
        self.ping_interval = ping_interval
        self.ping_timeout = ping_timeout

        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.is_connected = False
        self.is_running = False
        self.reconnect_attempts = 0

        self._receive_task: Optional[asyncio.Task] = None
        self._ping_task: Optional[asyncio.Task] = None

    async def connect(self):
        """Connect to WebSocket server."""
        if self.is_running:
            logger.warning("WebSocket client already running")
            return

        self.is_running = True
        await self._connect_loop()

    async def _connect_loop(self):
        """Main connection loop with automatic reconnection."""
        while self.is_running:
            try:
                await self._establish_connection()
                self.reconnect_attempts = 0

                # Start message receiver
                self._receive_task = asyncio.create_task(self._receive_messages())
                self._ping_task = asyncio.create_task(self._ping_loop())

                # Wait for disconnect
                await self._receive_task

            except ConnectionClosed as e:
                logger.warning(f"WebSocket connection closed: {e}")
                await self._handle_disconnect()

            except WebSocketException as e:
                logger.error(f"WebSocket error: {e}")
                await self._handle_disconnect()

            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                await self._handle_disconnect()

            # Check reconnection
            if not self.is_running:
                break

            if self.reconnect and self.reconnect_attempts < self.max_reconnect_attempts:
                self.reconnect_attempts += 1
                logger.info(
                    f"Reconnecting in {self.reconnect_delay}s "
                    f"(attempt {self.reconnect_attempts}/{self.max_reconnect_attempts})"
                )
                await asyncio.sleep(self.reconnect_delay)
            else:
                logger.error("Max reconnection attempts reached")
                break

    async def _establish_connection(self):
        """Establish WebSocket connection."""
        logger.info(f"Connecting to {self.url}")

        self.ws = await websockets.connect(
            self.url,
            ping_interval=self.ping_interval,
            ping_timeout=self.ping_timeout,
        )

        self.is_connected = True
        await self.handler.on_connect()

        logger.info("WebSocket connected successfully")

    async def _receive_messages(self):
        """Receive and process messages."""
        try:
            async for message in self.ws:
                try:
                    # Parse JSON message
                    data = json.loads(message)
                    await self.handler.on_message(data)

                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse message: {e}")
                    continue

                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    await self.handler.on_error(e)

        except ConnectionClosed:
            logger.info("Connection closed by server")
        except Exception as e:
            logger.error(f"Error receiving messages: {e}")

    async def _ping_loop(self):
        """Send periodic ping messages to keep connection alive."""
        try:
            while self.is_connected and self.is_running:
                await asyncio.sleep(self.ping_interval)

                if self.ws and not self.ws.closed:
                    try:
                        pong_waiter = await self.ws.ping()
                        await asyncio.wait_for(pong_waiter, timeout=self.ping_timeout)
                    except asyncio.TimeoutError:
                        logger.warning("Ping timeout - connection may be dead")
                        break

        except Exception as e:
            logger.error(f"Ping loop error: {e}")

    async def _handle_disconnect(self):
        """Handle disconnection cleanup."""
        self.is_connected = False

        if self._receive_task and not self._receive_task.done():
            self._receive_task.cancel()

        if self._ping_task and not self._ping_task.done():
            self._ping_task.cancel()

        if self.ws:
            await self.ws.close()

        await self.handler.on_disconnect()

    async def disconnect(self):
        """Disconnect from WebSocket server."""
        logger.info("Disconnecting WebSocket client")

        self.is_running = False
        self.is_connected = False

        if self._receive_task and not self._receive_task.done():
            self._receive_task.cancel()

        if self._ping_task and not self._ping_task.done():
            self._ping_task.cancel()

        if self.ws:
            await self.ws.close()

        await self.handler.on_disconnect()

    async def send(self, data: Dict[str, Any]):
        """
        Send message to WebSocket server.

        Args:
            data: Data to send (will be JSON serialized)
        """
        if not self.is_connected or not self.ws:
            raise RuntimeError("WebSocket not connected")

        try:
            message = json.dumps(data)
            await self.ws.send(message)

        except Exception as e:
            logger.error(f"Error sending message: {e}")
            raise

    async def subscribe(self, channels: List[str]):
        """
        Subscribe to channels.

        Args:
            channels: List of channels to subscribe to
        """
        subscribe_msg = {
            "method": "SUBSCRIBE",
            "params": channels,
            "id": int(datetime.utcnow().timestamp() * 1000),
        }
        await self.send(subscribe_msg)
        logger.info(f"Subscribed to channels: {channels}")

    async def unsubscribe(self, channels: List[str]):
        """
        Unsubscribe from channels.

        Args:
            channels: List of channels to unsubscribe from
        """
        unsubscribe_msg = {
            "method": "UNSUBSCRIBE",
            "params": channels,
            "id": int(datetime.utcnow().timestamp() * 1000),
        }
        await self.send(unsubscribe_msg)
        logger.info(f"Unsubscribed from channels: {channels}")


class BinanceWebSocketHandler(WebSocketHandler):
    """
    WebSocket handler for Binance streams.

    Example handler implementation for processing Binance market data.
    """

    def __init__(self, on_candle: Optional[Callable] = None):
        """
        Initialize Binance handler.

        Args:
            on_candle: Callback for candle data
        """
        self.on_candle = on_candle
        self.last_update = datetime.utcnow()

    async def on_message(self, data: Dict[str, Any]):
        """Process Binance WebSocket message."""
        try:
            # Handle kline (candlestick) data
            if "e" in data and data["e"] == "kline":
                await self._handle_kline(data["k"])

            # Handle trade data
            elif "e" in data and data["e"] == "trade":
                await self._handle_trade(data)

            # Handle depth (order book) updates
            elif "e" in data and data["e"] == "depthUpdate":
                await self._handle_depth(data)

            self.last_update = datetime.utcnow()

        except Exception as e:
            logger.error(f"Error handling Binance message: {e}")
            await self.on_error(e)

    async def _handle_kline(self, kline: Dict[str, Any]):
        """Process kline/candlestick data."""
        if self.on_candle:
            candle_data = {
                "timestamp": kline["t"],
                "open": float(kline["o"]),
                "high": float(kline["h"]),
                "low": float(kline["l"]),
                "close": float(kline["c"]),
                "volume": float(kline["v"]),
                "is_closed": kline["x"],
            }
            await self.on_candle(candle_data)

    async def _handle_trade(self, trade: Dict[str, Any]):
        """Process trade data."""
        logger.debug(f"Trade: {trade['p']} @ {trade['q']}")

    async def _handle_depth(self, depth: Dict[str, Any]):
        """Process order book depth update."""
        logger.debug(
            f"Depth update: {len(depth.get('b', []))} bids, {len(depth.get('a', []))} asks"
        )
