"""Tests for pattern detection."""

import pytest
import numpy as np
from datetime import datetime

from src.core.types import OHLCV
from src.patterns.technical import RSIPattern, MACDPattern


def create_sample_data(length: int = 100) -> OHLCV:
    """Create sample OHLCV data for testing."""
    timestamps = np.arange(length, dtype=float)
    prices = np.random.randn(length).cumsum() + 100

    return OHLCV(
        timestamps=timestamps,
        open=prices + np.random.randn(length) * 0.1,
        high=prices + np.abs(np.random.randn(length)) * 0.5,
        low=prices - np.abs(np.random.randn(length)) * 0.5,
        close=prices,
        volume=np.random.rand(length) * 1000,
    )


class TestRSIPattern:
    """Tests for RSI pattern detection."""

    def test_rsi_initialization(self):
        """Test RSI pattern initialization."""
        pattern = RSIPattern(period=14, overbought=70, oversold=30)

        assert pattern.name == "RSI"
        assert pattern.period == 14
        assert pattern.overbought == 70
        assert pattern.oversold == 30

    def test_rsi_detection(self):
        """Test RSI pattern detection."""
        pattern = RSIPattern()
        data = create_sample_data(50)

        results = pattern.detect(data)

        # Results should be a list (may be empty)
        assert isinstance(results, list)

    def test_rsi_validation(self):
        """Test RSI pattern validation."""
        pattern = RSIPattern()
        data = create_sample_data(50)
        results = pattern.detect(data)

        # All results should be valid
        for result in results:
            assert pattern.validate(result)


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

        # Results should be a list (may be empty)
        assert isinstance(results, list)

    def test_macd_validation(self):
        """Test MACD pattern validation."""
        pattern = MACDPattern()
        data = create_sample_data(100)
        results = pattern.detect(data)

        # All results should be valid
        for result in results:
            assert pattern.validate(result)


# More tests will be added in Phase 8
@pytest.mark.skip(reason="To be implemented in Phase 8")
class TestCandlestickPatterns:
    """Tests for candlestick patterns (Phase 8)."""
    pass


@pytest.mark.skip(reason="To be implemented in Phase 8")
class TestChartPatterns:
    """Tests for chart patterns (Phase 8)."""
    pass
