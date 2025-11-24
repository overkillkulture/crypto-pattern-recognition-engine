"""Metrics calculation utilities."""

import numpy as np
from typing import List, Tuple


def calculate_rsi(prices: np.ndarray, period: int = 14) -> np.ndarray:
    """
    Calculate Relative Strength Index.

    Args:
        prices: Price array
        period: RSI period

    Returns:
        RSI values
    """
    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)

    avg_gains = np.convolve(gains, np.ones(period), 'valid') / period
    avg_losses = np.convolve(losses, np.ones(period), 'valid') / period

    rs = avg_gains / (avg_losses + 1e-10)
    rsi = 100 - (100 / (1 + rs))

    return np.concatenate([np.full(period, np.nan), rsi])


def calculate_sma(prices: np.ndarray, period: int) -> np.ndarray:
    """Calculate Simple Moving Average."""
    return np.convolve(prices, np.ones(period), 'valid') / period


def calculate_ema(prices: np.ndarray, period: int) -> np.ndarray:
    """Calculate Exponential Moving Average."""
    ema = np.zeros_like(prices)
    ema[0] = prices[0]
    multiplier = 2 / (period + 1)

    for i in range(1, len(prices)):
        ema[i] = (prices[i] - ema[i-1]) * multiplier + ema[i-1]

    return ema


def calculate_macd(
    prices: np.ndarray,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Calculate MACD indicator.

    Returns:
        macd_line, signal_line, histogram
    """
    ema_fast = calculate_ema(prices, fast)
    ema_slow = calculate_ema(prices, slow)

    macd_line = ema_fast - ema_slow
    signal_line = calculate_ema(macd_line, signal)
    histogram = macd_line - signal_line

    return macd_line, signal_line, histogram


def calculate_bollinger_bands(
    prices: np.ndarray,
    period: int = 20,
    std_dev: float = 2.0
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Calculate Bollinger Bands.

    Returns:
        upper_band, middle_band, lower_band
    """
    middle = calculate_sma(prices, period)

    # Pad to match original length
    middle_full = np.concatenate([np.full(period-1, np.nan), middle])

    std = np.array([
        np.std(prices[max(0, i-period+1):i+1])
        for i in range(len(prices))
    ])

    upper = middle_full + (std_dev * std)
    lower = middle_full - (std_dev * std)

    return upper, middle_full, lower


def calculate_atr(
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    period: int = 14
) -> np.ndarray:
    """Calculate Average True Range."""
    tr1 = high - low
    tr2 = np.abs(high - np.roll(close, 1))
    tr3 = np.abs(low - np.roll(close, 1))

    tr = np.maximum(tr1, np.maximum(tr2, tr3))
    tr[0] = tr1[0]  # First value

    atr = calculate_ema(tr, period)
    return atr


def calculate_vwap(
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    volume: np.ndarray
) -> np.ndarray:
    """Calculate Volume Weighted Average Price."""
    typical_price = (high + low + close) / 3
    return np.cumsum(typical_price * volume) / np.cumsum(volume)


def calculate_obv(close: np.ndarray, volume: np.ndarray) -> np.ndarray:
    """Calculate On-Balance Volume."""
    obv = np.zeros_like(volume)
    obv[0] = volume[0]

    for i in range(1, len(close)):
        if close[i] > close[i-1]:
            obv[i] = obv[i-1] + volume[i]
        elif close[i] < close[i-1]:
            obv[i] = obv[i-1] - volume[i]
        else:
            obv[i] = obv[i-1]

    return obv


def calculate_metrics(prices: np.ndarray) -> dict:
    """Calculate comprehensive metrics."""
    return {
        'mean': np.mean(prices),
        'std': np.std(prices),
        'min': np.min(prices),
        'max': np.max(prices),
        'median': np.median(prices),
        'volatility': np.std(np.diff(prices) / prices[:-1]),
    }
