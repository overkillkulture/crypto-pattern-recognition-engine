"""Pattern detection modules."""

from src.patterns.candlestick import CandlestickPatternDetector
from src.patterns.chart import (CupAndHandlePattern, DiamondPattern,
                                DoubleTopBottomPattern, FlagPattern,
                                HeadAndShouldersPattern, RectanglePattern,
                                TrianglePattern, WedgePattern)
from src.patterns.combinations import (CombinedSignal, ConfirmationStrategy,
                                       ConsensusStrategy,
                                       PatternCombinationStrategy,
                                       PatternCombiner,
                                       TimeframeConfluenceStrategy,
                                       WeightedStrategy)
from src.patterns.detector import TechnicalPatternDetector
from src.patterns.technical import (ADXPattern, ATRPattern,
                                    BollingerBandsPattern, MACDPattern,
                                    MovingAverageCrossPattern, OBVPattern,
                                    ParabolicSARPattern, RSIPattern,
                                    StochasticPattern, VWAPPattern)

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
    "ADXPattern",
    "ParabolicSARPattern",
    "CandlestickPatternDetector",
    "HeadAndShouldersPattern",
    "TrianglePattern",
    "DoubleTopBottomPattern",
    "FlagPattern",
    "WedgePattern",
    "CupAndHandlePattern",
    "RectanglePattern",
    "DiamondPattern",
    # Combinations
    "CombinedSignal",
    "PatternCombinationStrategy",
    "ConsensusStrategy",
    "WeightedStrategy",
    "ConfirmationStrategy",
    "TimeframeConfluenceStrategy",
    "PatternCombiner",
]
