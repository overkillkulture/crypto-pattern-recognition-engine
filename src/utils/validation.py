"""Data validation and sanitization utilities."""

from datetime import datetime
from typing import Any, Dict

import numpy as np
from loguru import logger

from src.core.types import (OHLCV, Exchange, MarketData, PatternResult,
                            Timeframe)


class ValidationError(Exception):
    """Custom exception for validation errors."""


class DataValidator:
    """Validator for market data and engine inputs."""

    @staticmethod
    def validate_ohlcv(data: OHLCV, min_length: int = 1) -> bool:
        """
        Validate OHLCV data structure.

        Args:
            data: OHLCV data to validate
            min_length: Minimum required data length

        Returns:
            True if valid

        Raises:
            ValidationError: If validation fails
        """
        # Check type
        if not isinstance(data, OHLCV):
            raise ValidationError(f"Expected OHLCV, got {type(data)}")

        # Check lengths match
        lengths = [
            len(data.timestamps),
            len(data.open),
            len(data.high),
            len(data.low),
            len(data.close),
            len(data.volume),
        ]

        if len(set(lengths)) != 1:
            raise ValidationError(f"Mismatched array lengths: {lengths}")

        # Check minimum length
        if lengths[0] < min_length:
            raise ValidationError(f"Insufficient data: {lengths[0]} < {min_length}")

        # Check for NaN values
        arrays = [data.open, data.high, data.low, data.close, data.volume]
        for i, arr in enumerate(arrays):
            if np.any(np.isnan(arr)):
                names = ["open", "high", "low", "close", "volume"]
                raise ValidationError(f"NaN values found in {names[i]}")

        # Check for negative values
        if np.any(data.open < 0) or np.any(data.close < 0):
            raise ValidationError("Negative prices found")

        if np.any(data.volume < 0):
            raise ValidationError("Negative volume found")

        # Check OHLC relationships
        if not np.all(data.high >= data.low):
            raise ValidationError("High must be >= Low")

        if not np.all(data.high >= data.open):
            raise ValidationError("High must be >= Open")

        if not np.all(data.high >= data.close):
            raise ValidationError("High must be >= Close")

        if not np.all(data.low <= data.open):
            raise ValidationError("Low must be <= Open")

        if not np.all(data.low <= data.close):
            raise ValidationError("Low must be <= Close")

        # Check timestamps are sorted
        if not np.all(data.timestamps[1:] >= data.timestamps[:-1]):
            raise ValidationError("Timestamps must be sorted chronologically")

        logger.debug(f"OHLCV validation passed: {len(data)} candles")
        return True

    @staticmethod
    def sanitize_ohlcv(data: OHLCV) -> OHLCV:
        """
        Sanitize OHLCV data by removing invalid candles.

        Args:
            data: OHLCV data to sanitize

        Returns:
            Sanitized OHLCV data
        """
        # Find valid indices
        valid_mask = np.ones(len(data.close), dtype=bool)

        # Remove NaN values
        for arr in [data.open, data.high, data.low, data.close, data.volume]:
            valid_mask &= ~np.isnan(arr)

        # Remove negative values
        valid_mask &= (data.open >= 0) & (data.close >= 0) & (data.volume >= 0)

        # Remove invalid OHLC relationships
        valid_mask &= data.high >= data.low
        valid_mask &= data.high >= data.open
        valid_mask &= data.high >= data.close
        valid_mask &= data.low <= data.open
        valid_mask &= data.low <= data.close

        # Apply mask
        if not np.all(valid_mask):
            removed_count = np.sum(~valid_mask)
            logger.warning(f"Removed {removed_count} invalid candles")

            return OHLCV(
                timestamps=data.timestamps[valid_mask],
                open=data.open[valid_mask],
                high=data.high[valid_mask],
                low=data.low[valid_mask],
                close=data.close[valid_mask],
                volume=data.volume[valid_mask],
            )

        return data

    @staticmethod
    def validate_market_data(data: MarketData) -> bool:
        """
        Validate MarketData object.

        Args:
            data: Market data to validate

        Returns:
            True if valid

        Raises:
            ValidationError: If validation fails
        """
        # Check required fields
        if not isinstance(data.exchange, Exchange):
            raise ValidationError(f"Invalid exchange: {data.exchange}")

        if not isinstance(data.timeframe, Timeframe):
            raise ValidationError(f"Invalid timeframe: {data.timeframe}")

        if not isinstance(data.timestamp, datetime):
            raise ValidationError(f"Invalid timestamp: {data.timestamp}")

        # Validate OHLCV values
        if data.high < data.low:
            raise ValidationError(f"High {data.high} < Low {data.low}")

        if data.high < data.open or data.high < data.close:
            raise ValidationError("High must be >= Open and Close")

        if data.low > data.open or data.low > data.close:
            raise ValidationError("Low must be <= Open and Close")

        if data.volume < 0:
            raise ValidationError(f"Negative volume: {data.volume}")

        return True

    @staticmethod
    def validate_symbol(symbol: str) -> bool:
        """
        Validate trading pair symbol.

        Args:
            symbol: Trading pair (e.g., "BTC/USDT")

        Returns:
            True if valid

        Raises:
            ValidationError: If validation fails
        """
        if not symbol or not isinstance(symbol, str):
            raise ValidationError(f"Invalid symbol: {symbol}")

        if "/" not in symbol:
            raise ValidationError(f"Symbol must contain '/': {symbol}")

        parts = symbol.split("/")
        if len(parts) != 2:
            raise ValidationError(f"Symbol must be BASE/QUOTE format: {symbol}")

        base, quote = parts
        if not base or not quote:
            raise ValidationError(f"Empty base or quote currency: {symbol}")

        return True

    @staticmethod
    def validate_config(config: Dict[str, Any]) -> bool:
        """
        Validate engine configuration.

        Args:
            config: Configuration dictionary

        Returns:
            True if valid

        Raises:
            ValidationError: If validation fails
        """
        required_keys = ["exchanges", "pairs", "timeframes"]

        for key in required_keys:
            if key not in config:
                raise ValidationError(f"Missing required config key: {key}")

        # Validate exchanges
        if not config["exchanges"]:
            raise ValidationError("No exchanges configured")

        # Validate pairs
        if not config["pairs"]:
            raise ValidationError("No trading pairs configured")

        for symbol in config["pairs"]:
            DataValidator.validate_symbol(symbol)

        # Validate timeframes
        if not config["timeframes"]:
            raise ValidationError("No timeframes configured")

        valid_timeframes = [tf.value for tf in Timeframe]
        for tf in config["timeframes"]:
            if tf not in valid_timeframes:
                raise ValidationError(f"Invalid timeframe: {tf}")

        logger.debug("Configuration validation passed")
        return True

    @staticmethod
    def validate_pattern_result(result: PatternResult) -> bool:
        """
        Validate pattern detection result.

        Args:
            result: Pattern result to validate

        Returns:
            True if valid

        Raises:
            ValidationError: If validation fails
        """
        # Check confidence range
        if not 0 <= result.confidence <= 1:
            raise ValidationError(f"Confidence must be in [0, 1]: {result.confidence}")

        # Check required fields
        if not result.pattern_id:
            raise ValidationError("Missing pattern_id")

        if not result.pattern_name:
            raise ValidationError("Missing pattern_name")

        # Validate prices if present
        if result.entry_price is not None and result.entry_price < 0:
            raise ValidationError(f"Negative entry price: {result.entry_price}")

        if result.target_price is not None and result.target_price < 0:
            raise ValidationError(f"Negative target price: {result.target_price}")

        if result.stop_loss is not None and result.stop_loss < 0:
            raise ValidationError(f"Negative stop loss: {result.stop_loss}")

        return True

    @staticmethod
    def detect_outliers(prices: np.ndarray, threshold: float = 3.0) -> np.ndarray:
        """
        Detect outliers using Z-score method.

        Args:
            prices: Price array
            threshold: Z-score threshold (default 3.0)

        Returns:
            Boolean mask where True indicates outlier
        """
        if len(prices) < 2:
            return np.zeros(len(prices), dtype=bool)

        mean = np.mean(prices)
        std = np.std(prices)

        if std == 0:
            return np.zeros(len(prices), dtype=bool)

        z_scores = np.abs((prices - mean) / std)
        return z_scores > threshold

    @staticmethod
    def clean_price_data(prices: np.ndarray, max_pct_change: float = 0.5) -> np.ndarray:
        """
        Clean price data by removing extreme jumps.

        Args:
            prices: Price array
            max_pct_change: Maximum allowed percentage change between candles

        Returns:
            Cleaned price array
        """
        if len(prices) < 2:
            return prices

        # Calculate percentage changes
        pct_changes = np.abs(np.diff(prices) / prices[:-1])

        # Find extreme changes
        extreme_changes = pct_changes > max_pct_change

        if np.any(extreme_changes):
            logger.warning(f"Found {np.sum(extreme_changes)} extreme price changes")

            # Interpolate extreme values
            cleaned = prices.copy()
            for i in np.where(extreme_changes)[0]:
                if i > 0:
                    cleaned[i + 1] = (cleaned[i] + prices[i + 1]) / 2

            return cleaned

        return prices
