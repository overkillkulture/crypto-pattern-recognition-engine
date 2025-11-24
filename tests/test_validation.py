"""Tests for data validation."""

import pytest
import numpy as np
from datetime import datetime

from src.core.types import OHLCV, Exchange, Timeframe, MarketData
from src.utils.validation import DataValidator, ValidationError


def create_valid_ohlcv(length: int = 50) -> OHLCV:
    """Create valid OHLCV data for testing."""
    timestamps = np.arange(length, dtype=float) * 3600
    prices = np.linspace(100, 150, length)

    return OHLCV(
        timestamps=timestamps,
        open=prices,
        high=prices + 2,
        low=prices - 2,
        close=prices + 1,
        volume=np.ones(length) * 1000,
    )


def create_invalid_ohlcv_high_low() -> OHLCV:
    """Create OHLCV with invalid high/low relationship."""
    timestamps = np.arange(10, dtype=float) * 3600
    return OHLCV(
        timestamps=timestamps,
        open=np.ones(10) * 100,
        high=np.ones(10) * 90,  # High < Low (invalid!)
        low=np.ones(10) * 95,
        close=np.ones(10) * 92,
        volume=np.ones(10) * 1000,
    )


def create_ohlcv_with_nan() -> OHLCV:
    """Create OHLCV with NaN values."""
    timestamps = np.arange(10, dtype=float) * 3600
    prices = np.ones(10) * 100
    prices[5] = np.nan  # Inject NaN

    return OHLCV(
        timestamps=timestamps,
        open=prices,
        high=prices + 2,
        low=prices - 2,
        close=prices,
        volume=np.ones(10) * 1000,
    )


class TestDataValidator:
    """Tests for DataValidator class."""

    def test_validate_valid_ohlcv(self):
        """Test validation of valid OHLCV data."""
        data = create_valid_ohlcv(50)
        assert DataValidator.validate_ohlcv(data, min_length=10)

    def test_validate_ohlcv_insufficient_length(self):
        """Test validation fails with insufficient data."""
        data = create_valid_ohlcv(5)

        with pytest.raises(ValidationError, match="Insufficient data"):
            DataValidator.validate_ohlcv(data, min_length=10)

    def test_validate_ohlcv_with_nan(self):
        """Test validation fails with NaN values."""
        data = create_ohlcv_with_nan()

        with pytest.raises(ValidationError, match="NaN values"):
            DataValidator.validate_ohlcv(data)

    def test_validate_ohlcv_invalid_high_low(self):
        """Test validation fails with invalid high/low."""
        data = create_invalid_ohlcv_high_low()

        with pytest.raises(ValidationError, match="High must be >= Low"):
            DataValidator.validate_ohlcv(data)

    def test_validate_ohlcv_negative_prices(self):
        """Test validation fails with negative prices."""
        data = create_valid_ohlcv(10)
        data.close[5] = -10  # Negative price

        with pytest.raises(ValidationError, match="Negative prices"):
            DataValidator.validate_ohlcv(data)

    def test_validate_ohlcv_negative_volume(self):
        """Test validation fails with negative volume."""
        data = create_valid_ohlcv(10)
        data.volume[5] = -100  # Negative volume

        with pytest.raises(ValidationError, match="Negative volume"):
            DataValidator.validate_ohlcv(data)

    def test_sanitize_ohlcv_removes_nan(self):
        """Test sanitization removes NaN values."""
        data = create_ohlcv_with_nan()
        original_length = len(data)

        sanitized = DataValidator.sanitize_ohlcv(data)

        # Should have removed the NaN candle
        assert len(sanitized) < original_length
        # Remaining data should be valid
        assert DataValidator.validate_ohlcv(sanitized, min_length=1)

    def test_sanitize_ohlcv_valid_data_unchanged(self):
        """Test sanitization doesn't change valid data."""
        data = create_valid_ohlcv(10)
        original_length = len(data)

        sanitized = DataValidator.sanitize_ohlcv(data)

        # Should not remove any candles
        assert len(sanitized) == original_length

    def test_validate_symbol_valid(self):
        """Test validation of valid symbol."""
        assert DataValidator.validate_symbol("BTC/USDT")
        assert DataValidator.validate_symbol("ETH/BTC")

    def test_validate_symbol_invalid_format(self):
        """Test validation fails with invalid symbol format."""
        with pytest.raises(ValidationError, match="must contain '/'"):
            DataValidator.validate_symbol("BTCUSDT")

        with pytest.raises(ValidationError):
            DataValidator.validate_symbol("")

        with pytest.raises(ValidationError):
            DataValidator.validate_symbol("BTC/")

    def test_validate_config_valid(self):
        """Test validation of valid config."""
        config = {
            'exchanges': {'binance': {'enabled': True}},
            'pairs': ['BTC/USDT'],
            'timeframes': ['1h', '4h'],
        }

        assert DataValidator.validate_config(config)

    def test_validate_config_missing_keys(self):
        """Test validation fails with missing keys."""
        config = {'exchanges': {}}  # Missing 'pairs' and 'timeframes'

        with pytest.raises(ValidationError, match="Missing required config key"):
            DataValidator.validate_config(config)

    def test_validate_config_empty_exchanges(self):
        """Test validation fails with no exchanges."""
        config = {
            'exchanges': {},  # No exchanges
            'pairs': ['BTC/USDT'],
            'timeframes': ['1h'],
        }

        with pytest.raises(ValidationError, match="No exchanges configured"):
            DataValidator.validate_config(config)

    def test_validate_config_invalid_symbol(self):
        """Test validation fails with invalid symbols."""
        config = {
            'exchanges': {'binance': {'enabled': True}},
            'pairs': ['BTCUSDT'],  # Invalid format
            'timeframes': ['1h'],
        }

        with pytest.raises(ValidationError):
            DataValidator.validate_config(config)

    def test_validate_config_invalid_timeframe(self):
        """Test validation fails with invalid timeframe."""
        config = {
            'exchanges': {'binance': {'enabled': True}},
            'pairs': ['BTC/USDT'],
            'timeframes': ['invalid_tf'],
        }

        with pytest.raises(ValidationError, match="Invalid timeframe"):
            DataValidator.validate_config(config)

    def test_validate_market_data(self):
        """Test validation of MarketData."""
        data = MarketData(
            exchange=Exchange.BINANCE,
            symbol="BTC/USDT",
            timeframe=Timeframe.ONE_HOUR,
            timestamp=datetime.now(),
            open=100.0,
            high=105.0,
            low=95.0,
            close=102.0,
            volume=1000.0,
        )

        assert DataValidator.validate_market_data(data)

    def test_validate_market_data_invalid_high_low(self):
        """Test validation fails with invalid high/low in MarketData."""
        data = MarketData(
            exchange=Exchange.BINANCE,
            symbol="BTC/USDT",
            timeframe=Timeframe.ONE_HOUR,
            timestamp=datetime.now(),
            open=100.0,
            high=90.0,  # High < Low (invalid!)
            low=95.0,
            close=92.0,
            volume=1000.0,
        )

        with pytest.raises(ValidationError):
            DataValidator.validate_market_data(data)

    def test_detect_outliers(self):
        """Test outlier detection."""
        # Create data with outliers
        prices = np.ones(100) * 100
        prices[50] = 200  # Outlier
        prices[75] = 300  # Outlier

        outliers = DataValidator.detect_outliers(prices, threshold=3.0)

        assert isinstance(outliers, np.ndarray)
        assert outliers.dtype == bool
        assert np.sum(outliers) >= 2  # Should detect at least 2 outliers

    def test_clean_price_data(self):
        """Test price data cleaning."""
        # Create data with extreme jump
        prices = np.ones(100) * 100
        prices[50] = 200  # 100% jump

        cleaned = DataValidator.clean_price_data(prices, max_pct_change=0.5)

        # Extreme jump should be smoothed
        assert cleaned[50] < 200
        assert cleaned[50] > 100

    def test_clean_price_data_no_extreme_changes(self):
        """Test cleaning doesn't affect normal data."""
        prices = np.linspace(100, 110, 100)  # Gradual change

        cleaned = DataValidator.clean_price_data(prices, max_pct_change=0.5)

        # Should be unchanged
        np.testing.assert_array_almost_equal(cleaned, prices)


class TestValidationErrorHandling:
    """Tests for error handling in validation."""

    def test_validation_error_message(self):
        """Test ValidationError provides clear messages."""
        try:
            raise ValidationError("Test error message")
        except ValidationError as e:
            assert str(e) == "Test error message"

    def test_validation_error_is_exception(self):
        """Test ValidationError is proper Exception."""
        assert issubclass(ValidationError, Exception)
