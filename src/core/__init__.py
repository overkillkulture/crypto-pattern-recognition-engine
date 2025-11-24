"""Core engine components and interfaces."""

from src.core.engine import PatternRecognitionEngine
from src.core.interfaces import (
    Pattern,
    PatternDetector,
    DataProvider,
    AlertHandler,
)
from src.core.types import (
    MarketData,
    PatternResult,
    Alert,
    Timeframe,
    Exchange,
)

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
