"""Unit tests for advanced pattern detectors (ADX, Parabolic SAR, Stochastic)."""

import pytest
import numpy as np
from datetime import datetime, timedelta

from src.patterns.advanced import ADXPattern, ParabolicSARPattern, StochasticPattern
from src.core.types import OHLCV, SignalType
from tests.fixtures.market_data import generate_ohlcv, generate_uptrend, generate_downtrend


class TestADXPattern:
    """Tests for ADX pattern detector."""

    def test_initialization(self):
        """Test ADX pattern initialization."""
        adx = ADXPattern(period=14, strong_trend_threshold=25.0)
        assert adx.period == 14
        assert adx.strong_trend_threshold == 25.0
        assert adx.name == "ADX Trend Strength"

    def test_detect_with_insufficient_data(self):
        """Test ADX with insufficient data."""
        adx = ADXPattern(period=14)
        data = generate_ohlcv(periods=20, seed=42)
        patterns = adx.detect(data)
        # May or may not have patterns with 20 periods, but shouldn't crash
        assert isinstance(patterns, list)

    def test_detect_with_sufficient_data(self):
        """Test ADX with sufficient data."""
        adx = ADXPattern(period=14)
        data = generate_ohlcv(periods=100, seed=42)
        patterns = adx.detect(data)
        assert isinstance(patterns, list)

    def test_detect_strong_uptrend(self):
        """Test ADX detecting strong uptrend."""
        adx = ADXPattern(period=14, strong_trend_threshold=20.0)
        data = generate_uptrend(periods=100, seed=42)
        patterns = adx.detect(data)

        # Should detect some trend patterns
        assert len(patterns) > 0

        # Check metadata
        for pattern in patterns:
            assert 'adx' in pattern.metadata
            assert 'plus_di' in pattern.metadata
            assert 'minus_di' in pattern.metadata
            assert pattern.metadata['adx'] >= 0

    def test_detect_strong_downtrend(self):
        """Test ADX detecting strong downtrend."""
        adx = ADXPattern(period=14, strong_trend_threshold=20.0)
        data = generate_downtrend(periods=100, seed=42)
        patterns = adx.detect(data)

        # Should detect some trend patterns
        assert len(patterns) > 0

        # Check metadata
        for pattern in patterns:
            assert 'adx' in pattern.metadata
            assert 'trend_strength' in pattern.metadata

    def test_validate_correct_pattern(self):
        """Test validation of correct ADX pattern."""
        adx = ADXPattern(period=14)
        data = generate_uptrend(periods=100, seed=42)
        patterns = adx.detect(data)

        if len(patterns) > 0:
            pattern = patterns[0]
            assert adx.validate(pattern)

    def test_different_periods(self):
        """Test ADX with different periods."""
        data = generate_ohlcv(periods=100, seed=42)

        adx_14 = ADXPattern(period=14)
        adx_20 = ADXPattern(period=20)

        patterns_14 = adx_14.detect(data)
        patterns_20 = adx_20.detect(data)

        # Both should work
        assert isinstance(patterns_14, list)
        assert isinstance(patterns_20, list)


class TestParabolicSARPattern:
    """Tests for Parabolic SAR pattern detector."""

    def test_initialization(self):
        """Test SAR pattern initialization."""
        sar = ParabolicSARPattern(acceleration=0.02, maximum=0.20)
        assert sar.acceleration == 0.02
        assert sar.maximum == 0.20
        assert sar.name == "Parabolic SAR"

    def test_detect_with_insufficient_data(self):
        """Test SAR with insufficient data."""
        sar = ParabolicSARPattern()
        data = generate_ohlcv(periods=3, seed=42)
        patterns = sar.detect(data)
        assert isinstance(patterns, list)
        assert len(patterns) == 0

    def test_detect_with_sufficient_data(self):
        """Test SAR with sufficient data."""
        sar = ParabolicSARPattern()
        data = generate_ohlcv(periods=100, seed=42)
        patterns = sar.detect(data)
        assert isinstance(patterns, list)

    def test_detect_uptrend(self):
        """Test SAR detecting uptrend."""
        sar = ParabolicSARPattern()
        data = generate_uptrend(periods=100, seed=42)
        patterns = sar.detect(data)

        # Should detect trend patterns
        assert len(patterns) > 0

        # Check metadata
        pattern = patterns[0]
        assert 'sar' in pattern.metadata
        assert 'price' in pattern.metadata
        assert 'trend' in pattern.metadata
        assert 'reversal' in pattern.metadata

    def test_detect_downtrend(self):
        """Test SAR detecting downtrend."""
        sar = ParabolicSARPattern()
        data = generate_downtrend(periods=100, seed=42)
        patterns = sar.detect(data)

        # Should detect trend patterns
        assert len(patterns) > 0

        # Check for downtrend signals
        pattern = patterns[0]
        assert 'trend' in pattern.metadata

    def test_validate_correct_pattern(self):
        """Test validation of correct SAR pattern."""
        sar = ParabolicSARPattern()
        data = generate_ohlcv(periods=100, seed=42)
        patterns = sar.detect(data)

        if len(patterns) > 0:
            pattern = patterns[0]
            assert sar.validate(pattern)

    def test_different_acceleration(self):
        """Test SAR with different acceleration factors."""
        data = generate_ohlcv(periods=100, seed=42)

        sar_slow = ParabolicSARPattern(acceleration=0.01, maximum=0.10)
        sar_fast = ParabolicSARPattern(acceleration=0.03, maximum=0.30)

        patterns_slow = sar_slow.detect(data)
        patterns_fast = sar_fast.detect(data)

        # Both should work
        assert isinstance(patterns_slow, list)
        assert isinstance(patterns_fast, list)


class TestStochasticPattern:
    """Tests for Stochastic Oscillator pattern detector."""

    def test_initialization(self):
        """Test Stochastic pattern initialization."""
        stoch = StochasticPattern(k_period=14, d_period=3, overbought=80, oversold=20)
        assert stoch.k_period == 14
        assert stoch.d_period == 3
        assert stoch.overbought == 80
        assert stoch.oversold == 20
        assert stoch.name == "Stochastic Oscillator"

    def test_detect_with_insufficient_data(self):
        """Test Stochastic with insufficient data."""
        stoch = StochasticPattern()
        data = generate_ohlcv(periods=10, seed=42)
        patterns = stoch.detect(data)
        assert isinstance(patterns, list)

    def test_detect_with_sufficient_data(self):
        """Test Stochastic with sufficient data."""
        stoch = StochasticPattern()
        data = generate_ohlcv(periods=100, seed=42)
        patterns = stoch.detect(data)
        assert isinstance(patterns, list)

    def test_detect_oversold(self):
        """Test Stochastic detecting oversold condition."""
        stoch = StochasticPattern(k_period=14, d_period=3, oversold=30)
        # Generate data that tends toward oversold
        data = generate_downtrend(periods=100, seed=42)
        patterns = stoch.detect(data)

        # Check metadata if patterns found
        if len(patterns) > 0:
            pattern = patterns[0]
            assert 'k' in pattern.metadata
            assert 'd' in pattern.metadata
            assert 0 <= pattern.metadata['k'] <= 100
            assert 0 <= pattern.metadata['d'] <= 100

    def test_detect_overbought(self):
        """Test Stochastic detecting overbought condition."""
        stoch = StochasticPattern(k_period=14, d_period=3, overbought=70)
        # Generate data that tends toward overbought
        data = generate_uptrend(periods=100, seed=42)
        patterns = stoch.detect(data)

        # Check metadata if patterns found
        if len(patterns) > 0:
            pattern = patterns[0]
            assert 'k' in pattern.metadata
            assert 'd' in pattern.metadata

    def test_validate_correct_pattern(self):
        """Test validation of correct Stochastic pattern."""
        stoch = StochasticPattern()
        data = generate_ohlcv(periods=100, seed=42)
        patterns = stoch.detect(data)

        if len(patterns) > 0:
            pattern = patterns[0]
            assert stoch.validate(pattern)

    def test_different_periods(self):
        """Test Stochastic with different periods."""
        data = generate_ohlcv(periods=100, seed=42)

        stoch_fast = StochasticPattern(k_period=5, d_period=3)
        stoch_slow = StochasticPattern(k_period=21, d_period=5)

        patterns_fast = stoch_fast.detect(data)
        patterns_slow = stoch_slow.detect(data)

        # Both should work
        assert isinstance(patterns_fast, list)
        assert isinstance(patterns_slow, list)

    def test_metadata_keys(self):
        """Test that all required metadata keys are present."""
        stoch = StochasticPattern()
        data = generate_ohlcv(periods=100, seed=42)
        patterns = stoch.detect(data)

        if len(patterns) > 0:
            pattern = patterns[0]
            assert 'k' in pattern.metadata
            assert 'd' in pattern.metadata
            assert 'zone' in pattern.metadata


class TestAdvancedPatternsIntegration:
    """Integration tests for advanced patterns working together."""

    def test_all_patterns_on_same_data(self):
        """Test all advanced patterns on the same dataset."""
        data = generate_ohlcv(periods=100, seed=42)

        adx = ADXPattern(period=14)
        sar = ParabolicSARPattern()
        stoch = StochasticPattern()

        adx_patterns = adx.detect(data)
        sar_patterns = sar.detect(data)
        stoch_patterns = stoch.detect(data)

        # All should return lists
        assert isinstance(adx_patterns, list)
        assert isinstance(sar_patterns, list)
        assert isinstance(stoch_patterns, list)

    def test_pattern_combination_uptrend(self):
        """Test pattern combination on uptrend."""
        data = generate_uptrend(periods=100, seed=42)

        adx = ADXPattern(period=14, strong_trend_threshold=20.0)
        sar = ParabolicSARPattern()
        stoch = StochasticPattern()

        adx_patterns = adx.detect(data)
        sar_patterns = sar.detect(data)
        stoch_patterns = stoch.detect(data)

        # At least one detector should find something
        total_patterns = len(adx_patterns) + len(sar_patterns) + len(stoch_patterns)
        assert total_patterns > 0

    def test_pattern_combination_downtrend(self):
        """Test pattern combination on downtrend."""
        data = generate_downtrend(periods=100, seed=42)

        adx = ADXPattern(period=14, strong_trend_threshold=20.0)
        sar = ParabolicSARPattern()
        stoch = StochasticPattern()

        adx_patterns = adx.detect(data)
        sar_patterns = sar.detect(data)
        stoch_patterns = stoch.detect(data)

        # At least one detector should find something
        total_patterns = len(adx_patterns) + len(sar_patterns) + len(stoch_patterns)
        assert total_patterns > 0

    def test_signal_agreement(self):
        """Test if multiple patterns agree on signal direction."""
        data = generate_uptrend(periods=100, seed=42)

        adx = ADXPattern(period=14, strong_trend_threshold=15.0)
        sar = ParabolicSARPattern()

        adx_patterns = adx.detect(data)
        sar_patterns = sar.detect(data)

        if len(adx_patterns) > 0 and len(sar_patterns) > 0:
            # Just check they produced valid signals
            assert adx_patterns[0].signal in [SignalType.BUY, SignalType.SELL, SignalType.HOLD]
            assert sar_patterns[0].signal in [SignalType.BUY, SignalType.SELL, SignalType.HOLD]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
