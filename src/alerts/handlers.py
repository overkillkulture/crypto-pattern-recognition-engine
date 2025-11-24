"""Alert handler implementations."""

from pathlib import Path
from typing import Dict, Any
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
        self.enabled = config.get('enabled', True)


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
            with open(self.file_path, 'a') as f:
                f.write(f"\n{'='*80}\n")
                f.write(f"[{alert.timestamp.isoformat()}] "
                       f"ALERT [{alert.priority.value.upper()}]\n")
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
        self.enabled = config.get('enabled', True)
        if 'path' in config:
            self.file_path = Path(config['path'])
            self._ensure_file_exists()


# Placeholder for additional alert handlers (Phase 6)
class WebhookAlertHandler(AlertHandler):
    """Send alerts via webhook. TODO: Implement in Phase 6."""

    async def send_alert(self, alert: Alert) -> bool:
        # TODO: Implement webhook posting
        logger.warning("Webhook alerts not yet implemented")
        return False

    async def configure(self, config: Dict[str, Any]) -> None:
        pass


class TelegramAlertHandler(AlertHandler):
    """Send alerts via Telegram. TODO: Implement in Phase 6."""

    async def send_alert(self, alert: Alert) -> bool:
        # TODO: Implement Telegram bot integration
        logger.warning("Telegram alerts not yet implemented")
        return False

    async def configure(self, config: Dict[str, Any]) -> None:
        pass
