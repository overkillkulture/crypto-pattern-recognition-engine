"""Core interfaces for extensibility."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from src.core.types import (
    MarketData,
    OHLCV,
    PatternResult,
    Alert,
    Timeframe,
    Exchange,
    AnalysisResult,
    ModelPrediction,
)


class Pattern(ABC):
    """Base interface for all patterns."""

    def __init__(self):
        self.name: str = ""
        self.description: str = ""
        self.version: str = "1.0"

    @abstractmethod
    def detect(self, data: OHLCV) -> List[PatternResult]:
        """
        Detect pattern in the provided data.

        Args:
            data: OHLCV time series data

        Returns:
            List of detected pattern results
        """
        pass

    @abstractmethod
    def validate(self, result: PatternResult) -> bool:
        """
        Validate a pattern result.

        Args:
            result: Pattern result to validate

        Returns:
            True if valid, False otherwise
        """
        pass

    def get_metadata(self) -> Dict[str, Any]:
        """Get pattern metadata."""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
        }


class PatternDetector(ABC):
    """Base interface for pattern detection systems."""

    def __init__(self):
        self.patterns: List[Pattern] = []
        self.enabled: bool = True

    @abstractmethod
    async def detect_patterns(
        self,
        symbol: str,
        timeframe: Timeframe,
        data: OHLCV,
    ) -> List[PatternResult]:
        """
        Detect all patterns in the data.

        Args:
            symbol: Trading pair symbol
            timeframe: Timeframe for analysis
            data: OHLCV data

        Returns:
            List of detected patterns
        """
        pass

    @abstractmethod
    def register_pattern(self, pattern: Pattern) -> None:
        """Register a new pattern for detection."""
        pass

    @abstractmethod
    def unregister_pattern(self, pattern_name: str) -> None:
        """Unregister a pattern."""
        pass


class DataProvider(ABC):
    """Base interface for data providers."""

    @abstractmethod
    async def get_ohlcv(
        self,
        exchange: Exchange,
        symbol: str,
        timeframe: Timeframe,
        since: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> OHLCV:
        """
        Fetch OHLCV data.

        Args:
            exchange: Exchange to fetch from
            symbol: Trading pair symbol
            timeframe: Timeframe for candles
            since: Start time (optional)
            limit: Number of candles (optional)

        Returns:
            OHLCV data
        """
        pass

    @abstractmethod
    async def get_latest_price(
        self,
        exchange: Exchange,
        symbol: str,
    ) -> float:
        """Get latest price for a symbol."""
        pass

    @abstractmethod
    async def subscribe_realtime(
        self,
        exchange: Exchange,
        symbol: str,
        timeframe: Timeframe,
        callback,
    ) -> None:
        """Subscribe to real-time data updates."""
        pass


class MLModel(ABC):
    """Base interface for machine learning models."""

    def __init__(self):
        self.model_name: str = ""
        self.model_version: str = "1.0"
        self.trained: bool = False

    @abstractmethod
    async def train(
        self,
        training_data: OHLCV,
        labels: Optional[Any] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Train the model.

        Args:
            training_data: Training data
            labels: Training labels (if supervised)
            **kwargs: Additional training parameters

        Returns:
            Training metrics
        """
        pass

    @abstractmethod
    async def predict(
        self,
        data: OHLCV,
        **kwargs,
    ) -> ModelPrediction:
        """
        Make predictions on new data.

        Args:
            data: Input data
            **kwargs: Additional prediction parameters

        Returns:
            Model prediction
        """
        pass

    @abstractmethod
    def save(self, path: str) -> None:
        """Save model to disk."""
        pass

    @abstractmethod
    def load(self, path: str) -> None:
        """Load model from disk."""
        pass


class Analyzer(ABC):
    """Base interface for market analyzers."""

    @abstractmethod
    async def analyze(
        self,
        symbol: str,
        timeframe: Timeframe,
        data: OHLCV,
        patterns: List[PatternResult],
    ) -> AnalysisResult:
        """
        Perform comprehensive analysis.

        Args:
            symbol: Trading pair
            timeframe: Analysis timeframe
            data: OHLCV data
            patterns: Detected patterns

        Returns:
            Analysis result
        """
        pass


class AlertHandler(ABC):
    """Base interface for alert handlers."""

    @abstractmethod
    async def send_alert(self, alert: Alert) -> bool:
        """
        Send an alert.

        Args:
            alert: Alert to send

        Returns:
            True if sent successfully
        """
        pass

    @abstractmethod
    async def configure(self, config: Dict[str, Any]) -> None:
        """Configure the alert handler."""
        pass


class Strategy(ABC):
    """Base interface for trading strategies."""

    def __init__(self):
        self.name: str = ""
        self.description: str = ""

    @abstractmethod
    async def generate_signals(
        self,
        analysis: AnalysisResult,
    ) -> List[Dict[str, Any]]:
        """
        Generate trading signals based on analysis.

        Args:
            analysis: Market analysis result

        Returns:
            List of trading signals
        """
        pass

    @abstractmethod
    def validate_signal(self, signal: Dict[str, Any]) -> bool:
        """Validate a trading signal."""
        pass


class BacktestEngine(ABC):
    """Base interface for backtesting."""

    @abstractmethod
    async def backtest(
        self,
        strategy: Strategy,
        data: OHLCV,
        start_date: datetime,
        end_date: datetime,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Backtest a strategy.

        Args:
            strategy: Strategy to test
            data: Historical data
            start_date: Backtest start
            end_date: Backtest end
            **kwargs: Additional parameters

        Returns:
            Backtest results
        """
        pass
