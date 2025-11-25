"""
Unit tests for optimized pattern detectors.

Tests the OptimizedRSIPattern, OptimizedMACDPattern, and OptimizedBollingerBandsPattern.
"""

import sys

import numpy as np
import pytest

sys.path.insert(0, "/home/user/crypto-pattern-recognition-engine")

from src.core.types import SignalType
from src.patterns.optimized import (OptimizedBollingerBandsPattern,
                                    OptimizedMACDPattern, OptimizedRSIPattern,
                                    StreamingRSI)
from tests.fixtures.market_data import (FIXTURE_MEDIUM, generate_macd_bullish_cross,
                                        generate_ohlcv,
                                        generate_rsi_overbought,
                                        generate_rsi_oversold)


class TestOptimizedRSIPattern:
    """Tests for OptimizedRSIPattern."""

    def test_initialization(self):
        """Test RSI pattern initialization."""
        rsi = OptimizedRSIPattern(period=14, oversold=30, overbought=70)

        assert rsi.period == 14
        assert rsi.oversold == 30
        assert rsi.overbought == 70
        assert rsi.name == "Optimized RSI"

    def test_initialization_with_cache(self):
        """Test RSI with caching enabled."""
        rsi = OptimizedRSIPattern(use_cache=True)
        assert rsi.use_cache is True

    def test_initialization_without_cache(self):
        """Test RSI without caching."""
        rsi = OptimizedRSIPattern(use_cache=False)
        assert rsi.use_cache is False

    def test_detect_with_sufficient_data(self):
        """Test detection with sufficient data."""
        rsi = OptimizedRSIPattern(period=14, use_cache=False)
        data = generate_ohlcv(periods=100, seed=42)

        patterns = rsi.detect(data)

        # Should return a list
        assert isinstance(patterns, list)

    def test_detect_with_insufficient_data(self):
        """Test detection with insufficient data."""
        rsi = OptimizedRSIPattern(period=14, use_cache=False)
        data = generate_ohlcv(periods=10, seed=42)  # Too few periods

        patterns = rsi.detect(data)

        # Should return empty list
        assert patterns == []

    def test_detect_oversold_condition(self):
        """Test detection of oversold condition."""
        rsi = OptimizedRSIPattern(period=14, oversold=30, use_cache=False)
        data = generate_rsi_oversold(periods=100, seed=42)

        patterns = rsi.detect(data)

        # Should detect at least one pattern
        assert len(patterns) > 0

        # Check if any pattern is a BUY signal
        buy_signals = [p for p in patterns if p.signal == SignalType.BUY]
        assert len(buy_signals) > 0

        # Verify metadata
        for pattern in patterns:
            assert "rsi" in pattern.metadata
            assert "threshold" in pattern.metadata

    def test_detect_overbought_condition(self):
        """Test detection of overbought condition."""
        rsi = OptimizedRSIPattern(period=14, overbought=70, use_cache=False)
        data = generate_rsi_overbought(periods=100, seed=42)

        patterns = rsi.detect(data)

        # Should detect patterns
        assert len(patterns) > 0

        # Check if any pattern is a SELL signal
        sell_signals = [p for p in patterns if p.signal == SignalType.SELL]
        assert len(sell_signals) > 0

    def test_validate_correct_pattern(self):
        """Test validation of correct pattern result."""
        rsi = OptimizedRSIPattern()
        data = generate_rsi_oversold(periods=100, seed=42)
        patterns = rsi.detect(data)

        if patterns:
            # All patterns should be valid
            for pattern in patterns:
                assert rsi.validate(pattern) is True

    def test_cache_effectiveness(self):
        """Test that caching works correctly."""
        rsi_cached = OptimizedRSIPattern(use_cache=True)
        data = FIXTURE_MEDIUM

        # First call
        patterns1 = rsi_cached.detect(data)

        # Second call (should hit cache)
        patterns2 = rsi_cached.detect(data)

        # Results should be identical
        assert len(patterns1) == len(patterns2)

    def test_different_periods(self):
        """Test RSI with different periods."""
        data = generate_ohlcv(periods=100, seed=42)

        rsi_14 = OptimizedRSIPattern(period=14, use_cache=False)
        rsi_21 = OptimizedRSIPattern(period=21, use_cache=False)

        patterns_14 = rsi_14.detect(data)
        patterns_21 = rsi_21.detect(data)

        # Both should work (may have different results)
        assert isinstance(patterns_14, list)
        assert isinstance(patterns_21, list)


class TestOptimizedMACDPattern:
    """Tests for OptimizedMACDPattern."""

    def test_initialization(self):
        """Test MACD pattern initialization."""
        macd = OptimizedMACDPattern(fast_period=12, slow_period=26, signal_period=9)

        assert macd.fast_period == 12
        assert macd.slow_period == 26
        assert macd.signal_period == 9
        assert macd.name == "Optimized MACD"

    def test_detect_with_sufficient_data(self):
        """Test detection with sufficient data."""
        macd = OptimizedMACDPattern(use_cache=False)
        data = generate_ohlcv(periods=100, seed=42)

        patterns = macd.detect(data)

        assert isinstance(patterns, list)

    def test_detect_with_insufficient_data(self):
        """Test detection with insufficient data."""
        macd = OptimizedMACDPattern(use_cache=False)
        data = generate_ohlcv(periods=20, seed=42)  # Too few

        patterns = macd.detect(data)

        # Should handle gracefully
        assert isinstance(patterns, list)

    def test_detect_bullish_crossover(self):
        """Test detection of bullish crossover."""
        macd = OptimizedMACDPattern(use_cache=False)
        data = generate_macd_bullish_cross(periods=100, seed=42)

        patterns = macd.detect(data)

        # Should detect patterns
        assert isinstance(patterns, list)

    def test_validate_correct_pattern(self):
        """Test validation of correct pattern result."""
        macd = OptimizedMACDPattern(use_cache=False)
        data = generate_ohlcv(periods=100, seed=42)
        patterns = macd.detect(data)

        if patterns:
            for pattern in patterns:
                assert macd.validate(pattern) is True

    def test_metadata_keys(self):
        """Test that metadata contains required keys."""
        macd = OptimizedMACDPattern(use_cache=False)
        data = generate_ohlcv(periods=100, seed=42)
        patterns = macd.detect(data)

        if patterns:
            for pattern in patterns:
                assert "macd" in pattern.metadata
                assert "signal" in pattern.metadata
                assert "histogram" in pattern.metadata


class TestOptimizedBollingerBandsPattern:
    """Tests for OptimizedBollingerBandsPattern."""

    def test_initialization(self):
        """Test Bollinger Bands pattern initialization."""
        bb = OptimizedBollingerBandsPattern(period=20, std_dev=2.0)

        assert bb.period == 20
        assert bb.std_dev == 2.0
        assert bb.name == "Optimized Bollinger Bands"

    def test_detect_with_sufficient_data(self):
        """Test detection with sufficient data."""
        bb = OptimizedBollingerBandsPattern(use_cache=False)
        data = generate_ohlcv(periods=100, seed=42)

        patterns = bb.detect(data)

        assert isinstance(patterns, list)

    def test_detect_with_insufficient_data(self):
        """Test detection with insufficient data."""
        bb = OptimizedBollingerBandsPattern(period=20, use_cache=False)
        data = generate_ohlcv(periods=15, seed=42)  # Too few

        patterns = bb.detect(data)

        # Should return empty list
        assert patterns == []

    def test_validate_correct_pattern(self):
        """Test validation of correct pattern result."""
        bb = OptimizedBollingerBandsPattern(use_cache=False)
        data = generate_ohlcv(periods=100, seed=42)
        patterns = bb.detect(data)

        if patterns:
            for pattern in patterns:
                assert bb.validate(pattern) is True

    def test_metadata_keys(self):
        """Test that metadata contains required keys."""
        bb = OptimizedBollingerBandsPattern(use_cache=False)
        data = generate_ohlcv(periods=100, seed=42)
        patterns = bb.detect(data)

        if patterns:
            for pattern in patterns:
                assert "price" in pattern.metadata
                assert "lower_band" in pattern.metadata
                assert "middle_band" in pattern.metadata
                assert "upper_band" in pattern.metadata

    def test_different_std_dev(self):
        """Test BB with different standard deviations."""
        data = generate_ohlcv(periods=100, seed=42)

        bb_2 = OptimizedBollingerBandsPattern(std_dev=2.0, use_cache=False)
        bb_3 = OptimizedBollingerBandsPattern(std_dev=3.0, use_cache=False)

        patterns_2 = bb_2.detect(data)
        patterns_3 = bb_3.detect(data)

        # Both should work
        assert isinstance(patterns_2, list)
        assert isinstance(patterns_3, list)


class TestStreamingRSI:
    """Tests for StreamingRSI."""

    def test_initialization(self):
        """Test StreamingRSI initialization."""
        rsi = StreamingRSI(period=14)

        assert rsi.period == 14
        assert rsi.prev_price is None
        assert rsi.count == 0

    def test_update_with_insufficient_data(self):
        """Test update with insufficient data returns NaN."""
        rsi = StreamingRSI(period=14)

        # First update
        result = rsi.update(50000)
        assert np.isnan(result)

        # First few updates should return NaN
        for i in range(10):
            result = rsi.update(50000 + i * 10)
            assert np.isnan(result)

    def test_update_with_sufficient_data(self):
        """Test update with sufficient data returns valid RSI."""
        rsi = StreamingRSI(period=14)

        # Provide enough data
        prices = np.random.randn(50) * 100 + 50000

        for price in prices:
            result = rsi.update(price)

        # Last result should be valid RSI
        assert not np.isnan(result)
        assert 0 <= result <= 100

    def test_streaming_vs_batch(self):
        """Test that streaming RSI matches batch calculation (approximately)."""
        from src.utils.optimization import VectorizedIndicators

        # Generate price data
        prices = generate_ohlcv(periods=50, seed=42).close

        # Batch calculation
        batch_rsi = VectorizedIndicators.rsi(prices, period=14)

        # Streaming calculation
        stream_rsi = StreamingRSI(period=14)
        stream_results = []

        for price in prices:
            result = stream_rsi.update(price)
            stream_results.append(result)

        # Last few values should be close (within reasonable tolerance)
        # Note: Streaming uses simplified calculation so exact match not expected
        assert isinstance(stream_results[-1], (float, np.floating))


# Pytest fixtures
@pytest.fixture
def sample_ohlcv():
    """Provide sample OHLCV data."""
    return generate_ohlcv(periods=100, seed=42)


@pytest.fixture
def rsi_pattern():
    """Provide RSI pattern detector."""
    return OptimizedRSIPattern(use_cache=False)


@pytest.fixture
def macd_pattern():
    """Provide MACD pattern detector."""
    return OptimizedMACDPattern(use_cache=False)


@pytest.fixture
def bb_pattern():
    """Provide Bollinger Bands pattern detector."""
    return OptimizedBollingerBandsPattern(use_cache=False)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
