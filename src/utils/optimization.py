"""
Performance optimization utilities.

Lightweight, efficient tools for:
- Caching expensive calculations
- Vectorized operations
- Memory-efficient data structures
- Performance profiling
"""

import functools
import hashlib
import time
from collections import OrderedDict
from typing import Any, Callable, Optional, Tuple

import numpy as np


class TTLCache:
    """Time-To-Live cache with automatic expiration."""

    def __init__(self, maxsize: int = 128, ttl: float = 300.0):
        """
        Initialize TTL cache.

        Args:
            maxsize: Maximum cache size
            ttl: Time-to-live in seconds
        """
        self.cache = OrderedDict()
        self.maxsize = maxsize
        self.ttl = ttl
        self.timestamps = {}

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        if key not in self.cache:
            return None

        # Check expiration
        if time.time() - self.timestamps[key] > self.ttl:
            del self.cache[key]
            del self.timestamps[key]
            return None

        # Move to end (LRU)
        self.cache.move_to_end(key)
        return self.cache[key]

    def set(self, key: str, value: Any):
        """Set value in cache."""
        if key in self.cache:
            self.cache.move_to_end(key)
        else:
            if len(self.cache) >= self.maxsize:
                # Remove oldest
                oldest = next(iter(self.cache))
                del self.cache[oldest]
                del self.timestamps[oldest]

        self.cache[key] = value
        self.timestamps[key] = time.time()

    def clear(self):
        """Clear cache."""
        self.cache.clear()
        self.timestamps.clear()


# Global pattern cache
_pattern_cache = TTLCache(maxsize=256, ttl=300.0)


def cache_key(*args, **kwargs) -> str:
    """
    Generate cache key from function arguments.

    Fast hash-based key generation for numpy arrays and primitives.
    """
    key_parts = []

    for arg in args:
        if isinstance(arg, np.ndarray):
            # Fast hash for numpy arrays
            key_parts.append(f"arr_{arg.shape}_{arg.dtype}_{hash(arg.tobytes())}")
        else:
            key_parts.append(str(arg))

    for k, v in sorted(kwargs.items()):
        if isinstance(v, np.ndarray):
            key_parts.append(f"{k}=arr_{v.shape}_{v.dtype}_{hash(v.tobytes())}")
        else:
            key_parts.append(f"{k}={v}")

    # Fast hash
    key_str = "|".join(key_parts)
    return hashlib.md5(key_str.encode()).hexdigest()[:16]


def cached_pattern(ttl: float = 300.0):
    """
    Decorator to cache pattern detection results.

    Args:
        ttl: Time-to-live in seconds

    Usage:
        @cached_pattern(ttl=60.0)
        def detect(self, data: OHLCV):
            # expensive calculation
            return patterns
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            key = f"{func.__qualname__}:{cache_key(*args, **kwargs)}"

            # Check cache
            cached = _pattern_cache.get(key)
            if cached is not None:
                return cached

            # Compute
            result = func(*args, **kwargs)

            # Cache result
            _pattern_cache.set(key, result)

            return result

        wrapper.cache_clear = lambda: _pattern_cache.clear()
        return wrapper

    return decorator


class RollingWindow:
    """
    Memory-efficient rolling window for time series.

    Uses circular buffer to avoid repeated array copying.
    """

    def __init__(self, window_size: int, dtype=np.float64):
        """
        Initialize rolling window.

        Args:
            window_size: Size of rolling window
            dtype: Data type for storage
        """
        self.window_size = window_size
        self.buffer = np.zeros(window_size, dtype=dtype)
        self.index = 0
        self.filled = False

    def append(self, value: float):
        """Add value to window."""
        self.buffer[self.index] = value
        self.index = (self.index + 1) % self.window_size
        if self.index == 0:
            self.filled = True

    def get_array(self) -> np.ndarray:
        """Get ordered array of window values."""
        if not self.filled:
            return self.buffer[: self.index]

        # Return in correct order
        return np.concatenate([self.buffer[self.index :], self.buffer[: self.index]])

    def mean(self) -> float:
        """Fast mean calculation."""
        if not self.filled:
            return np.mean(self.buffer[: self.index])
        return np.mean(self.buffer)

    def std(self) -> float:
        """Fast std calculation."""
        if not self.filled:
            return np.std(self.buffer[: self.index])
        return np.std(self.buffer)


class VectorizedIndicators:
    """
    Vectorized implementations of common technical indicators.

    Optimized for speed and memory efficiency.
    """

    @staticmethod
    def sma(prices: np.ndarray, period: int) -> np.ndarray:
        """
        Simple Moving Average (vectorized).

        ~10x faster than loop-based implementation.
        """
        # Use convolution for speed
        weights = np.ones(period) / period
        return np.convolve(prices, weights, mode="valid")

    @staticmethod
    def ema(prices: np.ndarray, period: int, adjust: bool = True) -> np.ndarray:
        """
        Exponential Moving Average (vectorized).

        Args:
            prices: Price array
            period: EMA period
            adjust: Use adjusted calculation (faster)

        Returns:
            EMA values
        """
        alpha = 2.0 / (period + 1)

        if adjust:
            # Adjusted calculation (faster)
            weights = (1 - alpha) ** np.arange(len(prices))
            weights /= weights.sum()
            return np.convolve(prices[::-1], weights)[len(prices) - 1 :: -1]
        else:
            # Classic calculation
            ema = np.zeros_like(prices)
            ema[0] = prices[0]

            for i in range(1, len(prices)):
                ema[i] = alpha * prices[i] + (1 - alpha) * ema[i - 1]

            return ema

    @staticmethod
    def rsi(prices: np.ndarray, period: int = 14) -> np.ndarray:
        """
        Relative Strength Index (vectorized).

        Memory-efficient implementation using in-place operations.
        """
        # Calculate price changes
        deltas = np.diff(prices)

        # Separate gains and losses
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        # Calculate average gains/losses
        avg_gains = np.zeros(len(deltas))
        avg_losses = np.zeros(len(deltas))

        # Initial averages
        avg_gains[period - 1] = np.mean(gains[:period])
        avg_losses[period - 1] = np.mean(losses[:period])

        # Smoothed averages
        alpha = 1.0 / period
        for i in range(period, len(deltas)):
            avg_gains[i] = alpha * gains[i] + (1 - alpha) * avg_gains[i - 1]
            avg_losses[i] = alpha * losses[i] + (1 - alpha) * avg_losses[i - 1]

        # Calculate RS and RSI
        rs = np.divide(
            avg_gains, avg_losses, out=np.zeros_like(avg_gains), where=avg_losses != 0
        )
        rsi = 100 - (100 / (1 + rs))

        # Prepend NaN for first period
        return np.concatenate([np.full(period, np.nan), rsi[period - 1 :]])

    @staticmethod
    def bollinger_bands(
        prices: np.ndarray, period: int = 20, std_dev: float = 2.0
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Bollinger Bands (vectorized).

        Returns:
            upper, middle, lower bands
        """
        # Calculate middle band (SMA)
        middle = VectorizedIndicators.sma(prices, period)

        # Calculate rolling std
        std = np.array(
            [np.std(prices[i : i + period]) for i in range(len(prices) - period + 1)]
        )

        # Calculate bands
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)

        return upper, middle, lower

    @staticmethod
    def atr(
        high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14
    ) -> np.ndarray:
        """
        Average True Range (vectorized).

        Memory-efficient implementation.
        """
        # Calculate true range
        prev_close = np.roll(close, 1)
        prev_close[0] = close[0]

        tr1 = high - low
        tr2 = np.abs(high - prev_close)
        tr3 = np.abs(low - prev_close)

        tr = np.maximum(tr1, np.maximum(tr2, tr3))

        # Calculate ATR (EMA of TR)
        return VectorizedIndicators.ema(tr, period, adjust=False)


class MemoryPool:
    """
    Memory pool for reusing numpy arrays.

    Reduces allocation overhead and memory fragmentation.
    """

    def __init__(self, max_arrays: int = 50):
        """
        Initialize memory pool.

        Args:
            max_arrays: Maximum number of cached arrays per shape
        """
        self.pools = {}  # (shape, dtype) -> list of arrays
        self.max_arrays = max_arrays

    def get(self, shape: Tuple[int, ...], dtype=np.float64) -> np.ndarray:
        """
        Get array from pool or allocate new one.

        Args:
            shape: Array shape
            dtype: Data type

        Returns:
            numpy array (zeroed)
        """
        key = (shape, dtype)

        if key in self.pools and self.pools[key]:
            arr = self.pools[key].pop()
            arr.fill(0)  # Zero out
            return arr

        return np.zeros(shape, dtype=dtype)

    def release(self, arr: np.ndarray):
        """
        Return array to pool for reuse.

        Args:
            arr: Array to release
        """
        key = (arr.shape, arr.dtype)

        if key not in self.pools:
            self.pools[key] = []

        if len(self.pools[key]) < self.max_arrays:
            self.pools[key].append(arr)

    def clear(self):
        """Clear all pools."""
        self.pools.clear()


# Global memory pool
_memory_pool = MemoryPool(max_arrays=50)


def get_array(shape: Tuple[int, ...], dtype=np.float64) -> np.ndarray:
    """
    Get array from global memory pool.

    Usage:
        arr = get_array((1000,))
        # ... use array ...
        release_array(arr)
    """
    return _memory_pool.get(shape, dtype)


def release_array(arr: np.ndarray):
    """Release array back to global memory pool."""
    _memory_pool.release(arr)


class StreamingStats:
    """
    Memory-efficient streaming statistics.

    Calculates mean, variance, std without storing all values.
    Uses Welford's online algorithm.
    """

    def __init__(self):
        """Initialize streaming stats."""
        self.n = 0
        self.mean = 0.0
        self.m2 = 0.0
        self.min_val = float("inf")
        self.max_val = float("-inf")

    def update(self, value: float):
        """
        Update statistics with new value.

        Args:
            value: New value
        """
        self.n += 1
        delta = value - self.mean
        self.mean += delta / self.n
        delta2 = value - self.mean
        self.m2 += delta * delta2

        self.min_val = min(self.min_val, value)
        self.max_val = max(self.max_val, value)

    def get_mean(self) -> float:
        """Get current mean."""
        return self.mean

    def get_variance(self) -> float:
        """Get current variance."""
        if self.n < 2:
            return 0.0
        return self.m2 / (self.n - 1)

    def get_std(self) -> float:
        """Get current standard deviation."""
        return np.sqrt(self.get_variance())

    def get_min(self) -> float:
        """Get minimum value."""
        return self.min_val

    def get_max(self) -> float:
        """Get maximum value."""
        return self.max_val


def batch_process_patterns(patterns_list: list, batch_size: int = 32) -> list:
    """
    Process patterns in batches for better cache utilization.

    Args:
        patterns_list: List of pattern detection functions
        batch_size: Batch size for processing

    Returns:
        Combined results
    """
    results = []

    for i in range(0, len(patterns_list), batch_size):
        batch = patterns_list[i : i + batch_size]
        batch_results = [pattern() for pattern in batch]
        results.extend(batch_results)

    return results


class ProfileTimer:
    """
    Lightweight profiling timer.

    Usage:
        with ProfileTimer("my_function"):
            # code to profile
            pass
    """

    def __init__(self, name: str, print_result: bool = True):
        """
        Initialize timer.

        Args:
            name: Timer name
            print_result: Whether to print result
        """
        self.name = name
        self.print_result = print_result
        self.start_time = None
        self.elapsed = None

    def __enter__(self):
        """Start timer."""
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, *args):
        """Stop timer and print result."""
        self.elapsed = time.perf_counter() - self.start_time

        if self.print_result:
            print(f"⏱️  {self.name}: {self.elapsed*1000:.2f}ms")


# Optimization helpers
def optimize_ohlcv_memory(data) -> tuple:
    """
    Convert OHLCV to memory-efficient representation.

    Uses float32 instead of float64 where precision allows.

    Args:
        data: OHLCV object

    Returns:
        Tuple of optimized arrays
    """
    # Timestamps need full precision
    timestamps = data.timestamps.astype(np.float64)

    # Prices can use float32 (6-7 decimal digits precision)
    opens = data.open.astype(np.float32)
    highs = data.high.astype(np.float32)
    lows = data.low.astype(np.float32)
    closes = data.close.astype(np.float32)

    # Volume can use float32
    volumes = data.volume.astype(np.float32)

    return timestamps, opens, highs, lows, closes, volumes


def preallocate_results(n: int) -> list:
    """
    Preallocate list for pattern results.

    Reduces reallocation overhead.

    Args:
        n: Expected number of results

    Returns:
        Pre-allocated list
    """
    return [None] * n


# Export key functions
__all__ = [
    "TTLCache",
    "cached_pattern",
    "RollingWindow",
    "VectorizedIndicators",
    "MemoryPool",
    "get_array",
    "release_array",
    "StreamingStats",
    "batch_process_patterns",
    "ProfileTimer",
    "optimize_ohlcv_memory",
    "preallocate_results",
]
