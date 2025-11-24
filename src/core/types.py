"""Core type definitions for the pattern recognition engine."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
import numpy as np


class Timeframe(str, Enum):
    """Trading timeframes."""
    ONE_MINUTE = "1m"
    FIVE_MINUTES = "5m"
    FIFTEEN_MINUTES = "15m"
    THIRTY_MINUTES = "30m"
    ONE_HOUR = "1h"
    FOUR_HOURS = "4h"
    ONE_DAY = "1d"
    ONE_WEEK = "1w"


class Exchange(str, Enum):
    """Supported exchanges."""
    BINANCE = "binance"
    COINBASE = "coinbase"
    KRAKEN = "kraken"
    BYBIT = "bybit"
    OKX = "okx"
    KUCOIN = "kucoin"


class PatternType(str, Enum):
    """Pattern categories."""
    TECHNICAL_INDICATOR = "technical_indicator"
    CHART_PATTERN = "chart_pattern"
    CANDLESTICK_PATTERN = "candlestick_pattern"
    ORDER_FLOW = "order_flow"
    HARMONIC = "harmonic"
    ELLIOTT_WAVE = "elliott_wave"
    ML_PREDICTED = "ml_predicted"
    ANOMALY = "anomaly"


class SignalType(str, Enum):
    """Trading signals."""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    STRONG_BUY = "strong_buy"
    STRONG_SELL = "strong_sell"


class Priority(str, Enum):
    """Alert priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class MarketData:
    """Market data for a trading pair."""
    exchange: Exchange
    symbol: str
    timeframe: Timeframe
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float

    # Optional extended data
    trades: Optional[int] = None
    buy_volume: Optional[float] = None
    sell_volume: Optional[float] = None
    vwap: Optional[float] = None

    def to_ohlcv(self) -> List[float]:
        """Convert to OHLCV array."""
        return [self.open, self.high, self.low, self.close, self.volume]


@dataclass
class OHLCV:
    """OHLCV time series data."""
    timestamps: np.ndarray
    open: np.ndarray
    high: np.ndarray
    low: np.ndarray
    close: np.ndarray
    volume: np.ndarray

    def __len__(self) -> int:
        return len(self.timestamps)

    def to_dict(self) -> Dict[str, np.ndarray]:
        """Convert to dictionary format."""
        return {
            'timestamp': self.timestamps,
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume,
        }


@dataclass
class PatternResult:
    """Result of pattern detection."""
    pattern_id: str
    pattern_name: str
    pattern_type: PatternType
    symbol: str
    timeframe: Timeframe
    timestamp: datetime
    confidence: float
    signal: SignalType

    # Pattern-specific data
    metadata: Dict[str, Any]

    # Price levels
    entry_price: Optional[float] = None
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None

    # Additional analysis
    strength: Optional[float] = None
    description: Optional[str] = None
    indicators: Optional[Dict[str, float]] = None


@dataclass
class Alert:
    """Alert generated from pattern detection."""
    alert_id: str
    timestamp: datetime
    pattern_result: PatternResult
    priority: Priority
    message: str

    # Alert metadata
    triggered_by: str
    conditions: Dict[str, Any]

    # Delivery tracking
    sent: bool = False
    sent_to: List[str] = None
    acknowledged: bool = False


@dataclass
class AnalysisResult:
    """Comprehensive analysis result."""
    symbol: str
    timeframe: Timeframe
    timestamp: datetime

    # Detected patterns
    patterns: List[PatternResult]

    # Overall signal
    overall_signal: SignalType
    confidence: float

    # Market conditions
    trend: str  # bullish, bearish, neutral
    volatility: float
    volume_profile: str  # high, normal, low

    # Technical levels
    support_levels: List[float]
    resistance_levels: List[float]

    # Risk metrics
    risk_score: float

    # Additional insights
    insights: List[str]
    metadata: Dict[str, Any]


@dataclass
class ModelPrediction:
    """Machine learning model prediction."""
    model_name: str
    symbol: str
    timestamp: datetime
    prediction_type: str

    # Predictions
    predicted_price: Optional[float] = None
    predicted_direction: Optional[SignalType] = None
    predicted_volatility: Optional[float] = None

    # Confidence and probability
    confidence: float = 0.0
    probabilities: Optional[Dict[str, float]] = None

    # Model metadata
    model_version: str = "1.0"
    features_used: Optional[List[str]] = None


@dataclass
class BacktestResult:
    """Backtesting result for a strategy."""
    strategy_name: str
    start_date: datetime
    end_date: datetime

    # Performance metrics
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float

    # Trade statistics
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_profit: float
    avg_loss: float

    # Equity curve
    equity_curve: np.ndarray

    # Detailed trades
    trades: List[Dict[str, Any]]
