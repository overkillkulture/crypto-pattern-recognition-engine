"""Pattern detector implementations."""

from typing import List
from datetime import datetime
from loguru import logger

from src.core.interfaces import PatternDetector, Pattern
from src.core.types import OHLCV, PatternResult, Timeframe


class TechnicalPatternDetector(PatternDetector):
    """
    Detector for technical indicator patterns.

    Extensible framework for adding new technical patterns.
    """

    def __init__(self):
        super().__init__()
        self.patterns: List[Pattern] = []
        logger.info("Technical Pattern Detector initialized")

    async def detect_patterns(
        self,
        symbol: str,
        timeframe: Timeframe,
        data: OHLCV,
    ) -> List[PatternResult]:
        """Detect all registered patterns in the data."""
        all_results = []

        for pattern in self.patterns:
            try:
                results = pattern.detect(data)

                # Add context to results
                for result in results:
                    result.symbol = symbol
                    result.timeframe = timeframe

                all_results.extend(results)
                logger.debug(f"{pattern.name}: {len(results)} patterns detected")

            except Exception as e:
                logger.error(f"Error detecting {pattern.name}: {e}")

        return all_results

    def register_pattern(self, pattern: Pattern) -> None:
        """Register a new pattern."""
        self.patterns.append(pattern)
        logger.info(f"Registered pattern: {pattern.name}")

    def unregister_pattern(self, pattern_name: str) -> None:
        """Unregister a pattern."""
        self.patterns = [p for p in self.patterns if p.name != pattern_name]
        logger.info(f"Unregistered pattern: {pattern_name}")

    def list_patterns(self) -> List[str]:
        """List all registered patterns."""
        return [p.name for p in self.patterns]
