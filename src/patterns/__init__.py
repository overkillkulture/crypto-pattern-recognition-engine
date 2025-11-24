"""Pattern detection modules."""

from src.patterns.detector import TechnicalPatternDetector
from src.patterns.technical import (
    RSIPattern,
    MACDPattern,
    BollingerBandsPattern,
    StochasticPattern,
    VWAPPattern,
    MovingAverageCrossPattern,
    ATRPattern,
    OBVPattern,
)
from src.patterns.candlestick import CandlestickPatternDetector
from src.patterns.chart import (
    HeadAndShouldersPattern,
    TrianglePattern,
    DoubleTopBottomPattern,
    FlagPattern,
    WedgePattern,
)

__all__ = [
    "TechnicalPatternDetector",
    "RSIPattern",
    "MACDPattern",
    "BollingerBandsPattern",
    "StochasticPattern",
    "VWAPPattern",
    "MovingAverageCrossPattern",
    "ATRPattern",
    "OBVPattern",
    "CandlestickPatternDetector",
    "HeadAndShouldersPattern",
    "TrianglePattern",
    "DoubleTopBottomPattern",
    "FlagPattern",
    "WedgePattern",
]
