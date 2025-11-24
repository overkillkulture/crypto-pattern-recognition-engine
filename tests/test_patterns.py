"""Comprehensive tests for pattern detection."""

import pytest
import numpy as np
from datetime import datetime

from src.core.types import OHLCV, PatternType
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
from src.patterns.candlestick import (
    DojiPattern,
    HammerPattern,
    EngulfingPattern,
    MorningEveningStarPattern,
    ThreeSoldiersPattern,
    ShootingStarPattern,
)
from src.patterns.chart import (
    HeadAndShouldersPattern,
    TrianglePattern,
    DoubleTopBottomPattern,
    FlagPattern,
    WedgePattern,
)


def create_sample_data(length: int = 100, trend: str = 'random') -> OHLCV:
    """Create sample OHLCV data for testing."""
    timestamps = np.arange(length, dtype=float) * 3600  # Hourly candles

    if trend == 'uptrend':
        prices = np.linspace(100, 150, length) + np.random.randn(length) * 2
    elif trend == 'downtrend':
        prices = np.linspace(150, 100, length) + np.random.randn(length) * 2
    elif trend == 'sideways':
        prices = np.ones(length) * 125 + np.random.randn(length) * 3
    else:  # random
        prices = np.random.randn(length).cumsum() + 100

    # Ensure prices are positive
    prices = np.abs(prices) + 50

    return OHLCV(
        timestamps=timestamps,
        open=prices + np.random.randn(length) * 0.1,
        high=prices + np.abs(np.random.randn(length)) * 0.5,
        low=prices - np.abs(np.random.randn(length)) * 0.5,
        close=prices,
        volume=np.random.rand(length) * 1000 + 100,
    )


def create_overbought_rsi_data(length: int = 50) -> OHLCV:
    """Create data that will trigger overbought RSI."""
    timestamps = np.arange(length, dtype=float) * 3600
    # Strong uptrend to create overbought conditions
    prices = np.linspace(100, 150, length)

    return OHLCV(
        timestamps=timestamps,
        open=prices,
        high=prices + 1,
        low=prices - 1,
        close=prices,
        volume=np.ones(length) * 1000,
    )


def create_oversold_rsi_data(length: int = 50) -> OHLCV:
    """Create data that will trigger oversold RSI."""
    timestamps = np.arange(length, dtype=float) * 3600
    # Strong downtrend to create oversold conditions
    prices = np.linspace(150, 100, length)

    return OHLCV(
        timestamps=timestamps,
        open=prices,
        high=prices + 1,
        low=prices - 1,
        close=prices,
        volume=np.ones(length) * 1000,
    )


# ============================================================================
# TECHNICAL PATTERN TESTS
# ============================================================================

class TestRSIPattern:
    """Tests for RSI pattern detection."""

    def test_rsi_initialization(self):
        """Test RSI pattern initialization."""
        pattern = RSIPattern(period=14, overbought=70, oversold=30)
        assert pattern.name == "RSI"
        assert pattern.period == 14
        assert pattern.overbought == 70
        assert pattern.oversold == 30

    def test_rsi_detection_on_random_data(self):
        """Test RSI pattern detection on random data."""
        pattern = RSIPattern()
        data = create_sample_data(50)
        results = pattern.detect(data)
        assert isinstance(results, list)

    def test_rsi_overbought_detection(self):
        """Test RSI overbought detection."""
        pattern = RSIPattern(period=14, overbought=70)
        data = create_overbought_rsi_data(50)
        results = pattern.detect(data)

        # Should detect overbought condition
        assert any('overbought' in r.pattern_name.lower() for r in results)

    def test_rsi_oversold_detection(self):
        """Test RSI oversold detection."""
        pattern = RSIPattern(period=14, oversold=30)
        data = create_oversold_rsi_data(50)
        results = pattern.detect(data)

        # Should detect oversold condition
        assert any('oversold' in r.pattern_name.lower() for r in results)

    def test_rsi_validation(self):
        """Test RSI pattern validation."""
        pattern = RSIPattern()
        data = create_sample_data(50)
        results = pattern.detect(data)

        for result in results:
            assert pattern.validate(result)
            assert 0 <= result.metadata['rsi'] <= 100


class TestMACDPattern:
    """Tests for MACD pattern detection."""

    def test_macd_initialization(self):
        """Test MACD pattern initialization."""
        pattern = MACDPattern(fast=12, slow=26, signal=9)
        assert pattern.name == "MACD"
        assert pattern.fast == 12
        assert pattern.slow == 26
        assert pattern.signal == 9

    def test_macd_detection(self):
        """Test MACD pattern detection."""
        pattern = MACDPattern()
        data = create_sample_data(100)
        results = pattern.detect(data)
        assert isinstance(results, list)

    def test_macd_validation(self):
        """Test MACD pattern validation."""
        pattern = MACDPattern()
        data = create_sample_data(100)
        results = pattern.detect(data)

        for result in results:
            assert pattern.validate(result)
            assert 'macd' in result.metadata
            assert 'signal' in result.metadata


class TestBollingerBandsPattern:
    """Tests for Bollinger Bands pattern."""

    def test_bollinger_initialization(self):
        """Test Bollinger Bands initialization."""
        pattern = BollingerBandsPattern(period=20, std_dev=2.0)
        assert pattern.name == "Bollinger Bands"
        assert pattern.period == 20
        assert pattern.std_dev == 2.0

    def test_bollinger_detection(self):
        """Test Bollinger Bands detection."""
        pattern = BollingerBandsPattern()
        data = create_sample_data(50)
        results = pattern.detect(data)
        assert isinstance(results, list)

    def test_bollinger_validation(self):
        """Test Bollinger Bands validation."""
        pattern = BollingerBandsPattern()
        data = create_sample_data(50)
        results = pattern.detect(data)

        for result in results:
            assert pattern.validate(result)


class TestStochasticPattern:
    """Tests for Stochastic pattern."""

    def test_stochastic_initialization(self):
        """Test Stochastic initialization."""
        pattern = StochasticPattern(k_period=14, d_period=3)
        assert pattern.name == "Stochastic"
        assert pattern.k_period == 14
        assert pattern.d_period == 3

    def test_stochastic_detection(self):
        """Test Stochastic detection."""
        pattern = StochasticPattern()
        data = create_sample_data(50)
        results = pattern.detect(data)
        assert isinstance(results, list)


class TestVWAPPattern:
    """Tests for VWAP pattern."""

    def test_vwap_initialization(self):
        """Test VWAP initialization."""
        pattern = VWAPPattern()
        assert pattern.name == "VWAP"

    def test_vwap_detection(self):
        """Test VWAP detection."""
        pattern = VWAPPattern()
        data = create_sample_data(50)
        results = pattern.detect(data)
        assert isinstance(results, list)


class TestMovingAverageCrossPattern:
    """Tests for MA Cross pattern."""

    def test_ma_cross_initialization(self):
        """Test MA Cross initialization."""
        pattern = MovingAverageCrossPattern(fast_period=50, slow_period=200)
        assert pattern.name == "MA Cross"
        assert pattern.fast_period == 50
        assert pattern.slow_period == 200

    def test_ma_cross_detection(self):
        """Test MA Cross detection."""
        pattern = MovingAverageCrossPattern(fast_period=20, slow_period=50)
        data = create_sample_data(100)
        results = pattern.detect(data)
        assert isinstance(results, list)


class TestATRPattern:
    """Tests for ATR pattern."""

    def test_atr_initialization(self):
        """Test ATR initialization."""
        pattern = ATRPattern(period=14)
        assert pattern.name == "ATR"
        assert pattern.period == 14

    def test_atr_detection(self):
        """Test ATR detection."""
        pattern = ATRPattern()
        data = create_sample_data(50)
        results = pattern.detect(data)
        assert isinstance(results, list)


class TestOBVPattern:
    """Tests for OBV pattern."""

    def test_obv_initialization(self):
        """Test OBV initialization."""
        pattern = OBVPattern()
        assert pattern.name == "OBV"

    def test_obv_detection(self):
        """Test OBV detection."""
        pattern = OBVPattern()
        data = create_sample_data(50)
        results = pattern.detect(data)
        assert isinstance(results, list)


# ============================================================================
# CANDLESTICK PATTERN TESTS
# ============================================================================

class TestDojiPattern:
    """Tests for Doji pattern."""

    def test_doji_initialization(self):
        """Test Doji initialization."""
        pattern = DojiPattern()
        assert pattern.name == "Doji"

    def test_doji_detection(self):
        """Test Doji detection."""
        pattern = DojiPattern()
        data = create_sample_data(50)
        results = pattern.detect(data)
        assert isinstance(results, list)

    def test_doji_validation(self):
        """Test Doji validation."""
        pattern = DojiPattern()
        data = create_sample_data(50)
        results = pattern.detect(data)

        for result in results:
            assert result.pattern_type == PatternType.CANDLESTICK_PATTERN


class TestHammerPattern:
    """Tests for Hammer pattern."""

    def test_hammer_initialization(self):
        """Test Hammer initialization."""
        pattern = HammerPattern()
        assert pattern.name == "Hammer"

    def test_hammer_detection(self):
        """Test Hammer detection."""
        pattern = HammerPattern()
        data = create_sample_data(50)
        results = pattern.detect(data)
        assert isinstance(results, list)


class TestEngulfingPattern:
    """Tests for Engulfing pattern."""

    def test_engulfing_initialization(self):
        """Test Engulfing initialization."""
        pattern = EngulfingPattern()
        assert pattern.name == "Engulfing"

    def test_engulfing_detection(self):
        """Test Engulfing detection."""
        pattern = EngulfingPattern()
        data = create_sample_data(50)
        results = pattern.detect(data)
        assert isinstance(results, list)


class TestMorningEveningStarPattern:
    """Tests for Morning/Evening Star pattern."""

    def test_star_initialization(self):
        """Test Star initialization."""
        pattern = MorningEveningStarPattern()
        assert pattern.name == "Morning/Evening Star"

    def test_star_detection(self):
        """Test Star detection."""
        pattern = MorningEveningStarPattern()
        data = create_sample_data(50)
        results = pattern.detect(data)
        assert isinstance(results, list)


class TestThreeSoldiersPattern:
    """Tests for Three Soldiers pattern."""

    def test_soldiers_initialization(self):
        """Test Three Soldiers initialization."""
        pattern = ThreeSoldiersPattern()
        assert pattern.name == "Three Soldiers/Crows"

    def test_soldiers_detection(self):
        """Test Three Soldiers detection."""
        pattern = ThreeSoldiersPattern()
        data = create_sample_data(50)
        results = pattern.detect(data)
        assert isinstance(results, list)


class TestShootingStarPattern:
    """Tests for Shooting Star pattern."""

    def test_shooting_star_initialization(self):
        """Test Shooting Star initialization."""
        pattern = ShootingStarPattern()
        assert pattern.name == "Shooting Star"

    def test_shooting_star_detection(self):
        """Test Shooting Star detection."""
        pattern = ShootingStarPattern()
        data = create_sample_data(50)
        results = pattern.detect(data)
        assert isinstance(results, list)


# ============================================================================
# CHART PATTERN TESTS
# ============================================================================

class TestHeadAndShouldersPattern:
    """Tests for Head and Shoulders pattern."""

    def test_h_and_s_initialization(self):
        """Test H&S initialization."""
        pattern = HeadAndShouldersPattern()
        assert pattern.name == "Head and Shoulders"

    def test_h_and_s_detection(self):
        """Test H&S detection."""
        pattern = HeadAndShouldersPattern()
        data = create_sample_data(100)
        results = pattern.detect(data)
        assert isinstance(results, list)


class TestTrianglePattern:
    """Tests for Triangle pattern."""

    def test_triangle_initialization(self):
        """Test Triangle initialization."""
        pattern = TrianglePattern()
        assert pattern.name == "Triangle"

    def test_triangle_detection(self):
        """Test Triangle detection."""
        pattern = TrianglePattern()
        data = create_sample_data(50)
        results = pattern.detect(data)
        assert isinstance(results, list)


class TestDoubleTopBottomPattern:
    """Tests for Double Top/Bottom pattern."""

    def test_double_top_bottom_initialization(self):
        """Test Double Top/Bottom initialization."""
        pattern = DoubleTopBottomPattern()
        assert pattern.name == "Double Top/Bottom"

    def test_double_top_bottom_detection(self):
        """Test Double Top/Bottom detection."""
        pattern = DoubleTopBottomPattern()
        data = create_sample_data(100)
        results = pattern.detect(data)
        assert isinstance(results, list)


class TestFlagPattern:
    """Tests for Flag pattern."""

    def test_flag_initialization(self):
        """Test Flag initialization."""
        pattern = FlagPattern()
        assert pattern.name == "Flag"

    def test_flag_detection(self):
        """Test Flag detection."""
        pattern = FlagPattern()
        data = create_sample_data(50)
        results = pattern.detect(data)
        assert isinstance(results, list)


class TestWedgePattern:
    """Tests for Wedge pattern."""

    def test_wedge_initialization(self):
        """Test Wedge initialization."""
        pattern = WedgePattern()
        assert pattern.name == "Wedge"

    def test_wedge_detection(self):
        """Test Wedge detection."""
        pattern = WedgePattern()
        data = create_sample_data(50)
        results = pattern.detect(data)
        assert isinstance(results, list)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestPatternIntegration:
    """Integration tests for pattern detection."""

    def test_all_technical_patterns(self):
        """Test all technical patterns on same data."""
        data = create_sample_data(200)

        patterns = [
            RSIPattern(),
            MACDPattern(),
            BollingerBandsPattern(),
            StochasticPattern(),
            VWAPPattern(),
            ATRPattern(),
            OBVPattern(),
        ]

        for pattern in patterns:
            results = pattern.detect(data)
            assert isinstance(results, list)
            # Each result should be valid
            for result in results:
                assert pattern.validate(result)

    def test_all_candlestick_patterns(self):
        """Test all candlestick patterns on same data."""
        data = create_sample_data(100)

        patterns = [
            DojiPattern(),
            HammerPattern(),
            EngulfingPattern(),
            MorningEveningStarPattern(),
            ThreeSoldiersPattern(),
            ShootingStarPattern(),
        ]

        for pattern in patterns:
            results = pattern.detect(data)
            assert isinstance(results, list)

    def test_pattern_confidence_ranges(self):
        """Test that all patterns produce valid confidence values."""
        data = create_sample_data(200)

        all_patterns = [
            RSIPattern(),
            MACDPattern(),
            BollingerBandsPattern(),
            DojiPattern(),
            HammerPattern(),
            EngulfingPattern(),
        ]

        for pattern in all_patterns:
            results = pattern.detect(data)
            for result in results:
                assert 0 <= result.confidence <= 1, f"Invalid confidence for {pattern.name}"
