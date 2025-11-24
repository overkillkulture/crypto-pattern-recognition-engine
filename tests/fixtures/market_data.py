"""
Test fixtures for market data generation.

Provides reusable OHLCV data generators for testing.
"""

import numpy as np
from datetime import datetime, timedelta
from typing import Optional

import sys
sys.path.insert(0, '/home/user/crypto-pattern-recognition-engine')

from src.core.types import OHLCV


def generate_ohlcv(
    periods: int = 100,
    initial_price: float = 50000.0,
    trend: str = "neutral",
    volatility: float = 0.02,
    seed: Optional[int] = None,
) -> OHLCV:
    """
    Generate synthetic OHLCV data for testing.

    Args:
        periods: Number of periods to generate
        initial_price: Starting price
        trend: Market trend ("uptrend", "downtrend", "neutral")
        volatility: Price volatility (std dev of returns)
        seed: Random seed for reproducibility

    Returns:
        OHLCV object with generated data
    """
    if seed is not None:
        np.random.seed(seed)

    # Generate timestamps (hourly)
    timestamps = np.array([
        (datetime.now() - timedelta(hours=periods-i)).timestamp()
        for i in range(periods)
    ])

    # Base returns
    returns = np.random.randn(periods) * volatility

    # Add trend
    if trend == "uptrend":
        trend_component = np.linspace(0, 0.0005, periods)
        returns += trend_component
    elif trend == "downtrend":
        trend_component = np.linspace(0, -0.0005, periods)
        returns += trend_component

    # Generate prices
    prices = initial_price * np.cumprod(1 + returns)

    # Generate OHLCV
    closes = prices
    opens = np.roll(closes, 1)
    opens[0] = initial_price

    highs = np.maximum(opens, closes) * (1 + np.abs(np.random.randn(periods)) * 0.005)
    lows = np.minimum(opens, closes) * (1 - np.abs(np.random.randn(periods)) * 0.005)
    volumes = np.random.lognormal(20, 1, periods) * 100

    return OHLCV(
        timestamps=timestamps,
        open=opens,
        high=highs,
        low=lows,
        close=closes,
        volume=volumes,
    )


def generate_uptrend(periods: int = 100, **kwargs) -> OHLCV:
    """Generate uptrending market data."""
    return generate_ohlcv(periods=periods, trend="uptrend", **kwargs)


def generate_downtrend(periods: int = 100, **kwargs) -> OHLCV:
    """Generate downtrending market data."""
    return generate_ohlcv(periods=periods, trend="downtrend", **kwargs)


def generate_ranging(periods: int = 100, **kwargs) -> OHLCV:
    """Generate ranging/neutral market data."""
    kwargs['volatility'] = kwargs.get('volatility', 0.01)
    return generate_ohlcv(periods=periods, trend="neutral", **kwargs)


def generate_volatile(periods: int = 100, **kwargs) -> OHLCV:
    """Generate highly volatile market data."""
    kwargs['volatility'] = kwargs.get('volatility', 0.04)
    return generate_ohlcv(periods=periods, trend="neutral", **kwargs)


def generate_rsi_oversold(periods: int = 100, **kwargs) -> OHLCV:
    """
    Generate data that will trigger RSI oversold condition.

    Creates strong downtrend followed by small bounce.
    """
    if kwargs.get('seed') is not None:
        np.random.seed(kwargs['seed'])

    initial_price = kwargs.get('initial_price', 50000.0)

    # Strong downtrend
    downtrend = generate_downtrend(periods=periods-10, volatility=0.03, **kwargs)

    # Small bounce at end
    bounce_returns = np.random.randn(10) * 0.01 + 0.001
    bounce_prices = downtrend.close[-1] * np.cumprod(1 + bounce_returns)

    # Combine
    all_closes = np.concatenate([downtrend.close, bounce_prices])
    all_timestamps = np.concatenate([
        downtrend.timestamps,
        downtrend.timestamps[-1] + np.arange(1, 11) * 3600
    ])

    opens = np.roll(all_closes, 1)
    opens[0] = initial_price

    highs = np.maximum(opens, all_closes) * (1 + np.abs(np.random.randn(periods)) * 0.005)
    lows = np.minimum(opens, all_closes) * (1 - np.abs(np.random.randn(periods)) * 0.005)
    volumes = np.random.lognormal(20, 1, periods) * 100

    return OHLCV(
        timestamps=all_timestamps,
        open=opens,
        high=highs,
        low=lows,
        close=all_closes,
        volume=volumes,
    )


def generate_rsi_overbought(periods: int = 100, **kwargs) -> OHLCV:
    """
    Generate data that will trigger RSI overbought condition.

    Creates strong uptrend followed by small pullback.
    """
    if kwargs.get('seed') is not None:
        np.random.seed(kwargs['seed'])

    initial_price = kwargs.get('initial_price', 50000.0)

    # Strong uptrend
    uptrend = generate_uptrend(periods=periods-10, volatility=0.03, **kwargs)

    # Small pullback at end
    pullback_returns = np.random.randn(10) * 0.01 - 0.001
    pullback_prices = uptrend.close[-1] * np.cumprod(1 + pullback_returns)

    # Combine
    all_closes = np.concatenate([uptrend.close, pullback_prices])
    all_timestamps = np.concatenate([
        uptrend.timestamps,
        uptrend.timestamps[-1] + np.arange(1, 11) * 3600
    ])

    opens = np.roll(all_closes, 1)
    opens[0] = initial_price

    highs = np.maximum(opens, all_closes) * (1 + np.abs(np.random.randn(periods)) * 0.005)
    lows = np.minimum(opens, all_closes) * (1 - np.abs(np.random.randn(periods)) * 0.005)
    volumes = np.random.lognormal(20, 1, periods) * 100

    return OHLCV(
        timestamps=all_timestamps,
        open=opens,
        high=highs,
        low=lows,
        close=all_closes,
        volume=volumes,
    )


def generate_macd_bullish_cross(periods: int = 100, **kwargs) -> OHLCV:
    """Generate data with MACD bullish crossover."""
    if kwargs.get('seed') is not None:
        np.random.seed(kwargs['seed'])

    # Downtrend followed by uptrend
    downtrend = generate_downtrend(periods=periods//2, **kwargs)
    uptrend = generate_uptrend(periods=periods//2, initial_price=downtrend.close[-1], **kwargs)

    all_closes = np.concatenate([downtrend.close, uptrend.close])
    all_timestamps = np.concatenate([
        downtrend.timestamps,
        downtrend.timestamps[-1] + np.arange(1, len(uptrend.close) + 1) * 3600
    ])

    opens = np.roll(all_closes, 1)
    opens[0] = kwargs.get('initial_price', 50000.0)

    highs = np.maximum(opens, all_closes) * (1 + np.abs(np.random.randn(periods)) * 0.005)
    lows = np.minimum(opens, all_closes) * (1 - np.abs(np.random.randn(periods)) * 0.005)
    volumes = np.random.lognormal(20, 1, periods) * 100

    return OHLCV(
        timestamps=all_timestamps,
        open=opens,
        high=highs,
        low=lows,
        close=all_closes,
        volume=volumes,
    )


# Commonly used fixtures
FIXTURE_SMALL = generate_ohlcv(periods=50, seed=42)
FIXTURE_MEDIUM = generate_ohlcv(periods=200, seed=42)
FIXTURE_LARGE = generate_ohlcv(periods=1000, seed=42)

FIXTURE_UPTREND = generate_uptrend(periods=100, seed=42)
FIXTURE_DOWNTREND = generate_downtrend(periods=100, seed=42)
FIXTURE_RANGING = generate_ranging(periods=100, seed=42)

FIXTURE_RSI_OVERSOLD = generate_rsi_oversold(periods=100, seed=42)
FIXTURE_RSI_OVERBOUGHT = generate_rsi_overbought(periods=100, seed=42)
FIXTURE_MACD_CROSS = generate_macd_bullish_cross(periods=100, seed=42)
