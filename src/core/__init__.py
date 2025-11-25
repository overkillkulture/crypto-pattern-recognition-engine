"""Core engine components and interfaces."""

from src.core.engine import PatternRecognitionEngine
from src.core.interfaces import (AlertHandler, DataProvider, Pattern,
                                 PatternDetector)
from src.core.types import (Alert, Exchange, MarketData, PatternResult,
                            Timeframe)

__all__ = [
    "PatternRecognitionEngine",
    "Pattern",
    "PatternDetector",
    "DataProvider",
    "AlertHandler",
    "MarketData",
    "PatternResult",
    "Alert",
    "Timeframe",
    "Exchange",
]
