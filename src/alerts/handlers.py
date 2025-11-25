"""Alert handler implementations."""

import asyncio
from pathlib import Path
from typing import Any, Dict

import aiohttp
from loguru import logger

from src.core.interfaces import AlertHandler
from src.core.types import Alert


class ConsoleAlertHandler(AlertHandler):
    """Send alerts to console output."""

    def __init__(self):
        self.enabled = True

    async def send_alert(self, alert: Alert) -> bool:
        """Print alert to console."""
        if not self.enabled:
            return False

        message = f"""
{'='*60}
🚨 ALERT [{alert.priority.value.upper()}]
{'='*60}
{alert.message}
Pattern ID: {alert.pattern_result.pattern_id}
Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
{'='*60}
"""
        print(message)
        logger.info(f"Alert sent to console: {alert.alert_id}")
        return True

    async def configure(self, config: Dict[str, Any]) -> None:
        """Configure console handler."""
        self.enabled = config.get("enabled", True)


class FileAlertHandler(AlertHandler):
    """Write alerts to a log file."""

    def __init__(self, file_path: str = "logs/alerts.log"):
        self.file_path = Path(file_path)
        self.enabled = True
        self._ensure_file_exists()

    def _ensure_file_exists(self) -> None:
        """Create alerts file and directory if they don't exist."""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            self.file_path.touch()

    async def send_alert(self, alert: Alert) -> bool:
        """Write alert to file."""
        if not self.enabled:
            return False

        try:
            with open(self.file_path, "a") as f:
                f.write(f"\n{'='*80}\n")
                f.write(
                    f"[{alert.timestamp.isoformat()}] "
                    f"ALERT [{alert.priority.value.upper()}]\n"
                )
                f.write(f"{alert.message}\n")
                f.write(f"Pattern: {alert.pattern_result.pattern_name}\n")
                f.write(f"Symbol: {alert.pattern_result.symbol}\n")
                f.write(f"Signal: {alert.pattern_result.signal.value}\n")
                f.write(f"Confidence: {alert.pattern_result.confidence:.2%}\n")
                f.write(f"Alert ID: {alert.alert_id}\n")
                f.write(f"{'='*80}\n")

            logger.info(f"Alert written to file: {alert.alert_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to write alert to file: {e}")
            return False

    async def configure(self, config: Dict[str, Any]) -> None:
        """Configure file handler."""
        self.enabled = config.get("enabled", True)
        if "path" in config:
            self.file_path = Path(config["path"])
            self._ensure_file_exists()


class WebhookAlertHandler(AlertHandler):
    """Send alerts via HTTP webhook with retry logic."""

    def __init__(self, webhook_url: str = "", max_retries: int = 3):
        self.webhook_url = webhook_url
        self.max_retries = max_retries
        self.enabled = True
        self.timeout = aiohttp.ClientTimeout(total=10)

    async def send_alert(self, alert: Alert) -> bool:
        """Send alert to webhook endpoint."""
        if not self.enabled or not self.webhook_url:
            logger.warning("Webhook not configured or disabled")
            return False

        # Prepare payload
        payload = {
            "alert_id": alert.alert_id,
            "timestamp": alert.timestamp.isoformat(),
            "priority": alert.priority.value,
            "message": alert.message,
            "pattern": {
                "id": alert.pattern_result.pattern_id,
                "name": alert.pattern_result.pattern_name,
                "type": alert.pattern_result.pattern_type.value,
                "symbol": alert.pattern_result.symbol,
                "timeframe": (
                    alert.pattern_result.timeframe.value
                    if alert.pattern_result.timeframe
                    else None
                ),
                "signal": alert.pattern_result.signal.value,
                "confidence": alert.pattern_result.confidence,
                "metadata": alert.pattern_result.metadata,
            },
        }

        # Retry logic
        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession(timeout=self.timeout) as session:
                    async with session.post(self.webhook_url, json=payload) as response:
                        if response.status == 200:
                            logger.info(
                                f"Webhook alert sent successfully: {alert.alert_id}"
                            )
                            return True
                        else:
                            logger.warning(f"Webhook returned status {response.status}")

            except aiohttp.ClientError as e:
                logger.error(
                    f"Webhook error (attempt {attempt + 1}/{self.max_retries}): {e}"
                )
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2**attempt)  # Exponential backoff

            except Exception as e:
                logger.error(f"Unexpected error sending webhook: {e}")
                break

        logger.error(f"Failed to send webhook after {self.max_retries} attempts")
        return False

    async def configure(self, config: Dict[str, Any]) -> None:
        """Configure webhook handler."""
        self.enabled = config.get("enabled", True)
        self.webhook_url = config.get("url", self.webhook_url)
        self.max_retries = config.get("max_retries", 3)


class TelegramAlertHandler(AlertHandler):
    """Send alerts via Telegram Bot API with retry logic."""

    def __init__(self, bot_token: str = "", chat_id: str = "", max_retries: int = 3):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.max_retries = max_retries
        self.enabled = True
        self.timeout = aiohttp.ClientTimeout(total=10)

    async def send_alert(self, alert: Alert) -> bool:
        """Send alert to Telegram chat."""
        if not self.enabled or not self.bot_token or not self.chat_id:
            logger.warning("Telegram not configured or disabled")
            return False

        # Format message
        pattern = alert.pattern_result
        message = f"""
🚨 *ALERT [{alert.priority.value.upper()}]*

*Pattern:* {pattern.pattern_name}
*Symbol:* {pattern.symbol}
*Signal:* {pattern.signal.value.upper()}
*Confidence:* {pattern.confidence:.2%}

{alert.message}

*Time:* {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
        """.strip()

        # Telegram API endpoint
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "Markdown",
        }

        # Retry logic
        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession(timeout=self.timeout) as session:
                    async with session.post(url, json=payload) as response:
                        if response.status == 200:
                            logger.info(
                                f"Telegram alert sent successfully: {alert.alert_id}"
                            )
                            return True
                        else:
                            response_text = await response.text()
                            logger.warning(
                                f"Telegram API error: {response.status} - {response_text}"
                            )

            except aiohttp.ClientError as e:
                logger.error(
                    f"Telegram error (attempt {attempt + 1}/{self.max_retries}): {e}"
                )
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2**attempt)  # Exponential backoff

            except Exception as e:
                logger.error(f"Unexpected error sending Telegram message: {e}")
                break

        logger.error(f"Failed to send Telegram alert after {self.max_retries} attempts")
        return False

    async def configure(self, config: Dict[str, Any]) -> None:
        """Configure Telegram handler."""
        self.enabled = config.get("enabled", True)
        self.bot_token = config.get("bot_token", self.bot_token)
        self.chat_id = config.get("chat_id", self.chat_id)
        self.max_retries = config.get("max_retries", 3)


class DiscordAlertHandler(AlertHandler):
    """Send alerts via Discord webhook."""

    def __init__(self, webhook_url: str = "", max_retries: int = 3):
        self.webhook_url = webhook_url
        self.max_retries = max_retries
        self.enabled = True
        self.timeout = aiohttp.ClientTimeout(total=10)

    async def send_alert(self, alert: Alert) -> bool:
        """Send alert to Discord channel via webhook."""
        if not self.enabled or not self.webhook_url:
            logger.warning("Discord webhook not configured or disabled")
            return False

        pattern = alert.pattern_result

        # Discord embed format
        color = {
            "low": 0x808080,  # Gray
            "medium": 0xFFA500,  # Orange
            "high": 0xFF4500,  # Red-Orange
            "critical": 0xFF0000,  # Red
        }.get(alert.priority.value, 0x808080)

        payload = {
            "embeds": [
                {
                    "title": f"🚨 {alert.priority.value.upper()} Alert",
                    "description": alert.message,
                    "color": color,
                    "fields": [
                        {
                            "name": "Pattern",
                            "value": pattern.pattern_name,
                            "inline": True,
                        },
                        {"name": "Symbol", "value": pattern.symbol, "inline": True},
                        {
                            "name": "Signal",
                            "value": pattern.signal.value.upper(),
                            "inline": True,
                        },
                        {
                            "name": "Confidence",
                            "value": f"{pattern.confidence:.2%}",
                            "inline": True,
                        },
                        {
                            "name": "Timeframe",
                            "value": (
                                pattern.timeframe.value if pattern.timeframe else "N/A"
                            ),
                            "inline": True,
                        },
                    ],
                    "timestamp": alert.timestamp.isoformat(),
                    "footer": {"text": f"Alert ID: {alert.alert_id}"},
                }
            ]
        }

        # Retry logic
        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession(timeout=self.timeout) as session:
                    async with session.post(self.webhook_url, json=payload) as response:
                        if response.status in [200, 204]:
                            logger.info(
                                f"Discord alert sent successfully: {alert.alert_id}"
                            )
                            return True
                        else:
                            logger.warning(
                                f"Discord webhook returned status {response.status}"
                            )

            except aiohttp.ClientError as e:
                logger.error(
                    f"Discord error (attempt {attempt + 1}/{self.max_retries}): {e}"
                )
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2**attempt)

            except Exception as e:
                logger.error(f"Unexpected error sending Discord alert: {e}")
                break

        logger.error(f"Failed to send Discord alert after {self.max_retries} attempts")
        return False

    async def configure(self, config: Dict[str, Any]) -> None:
        """Configure Discord handler."""
        self.enabled = config.get("enabled", True)
        self.webhook_url = config.get("webhook_url", self.webhook_url)
        self.max_retries = config.get("max_retries", 3)
