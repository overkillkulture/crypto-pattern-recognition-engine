"""Performance optimization utilities."""

import time
import asyncio
import functools
import logging
from typing import Callable, Any, Optional, Dict, List, TypeVar, Coroutine
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import OrderedDict
import threading

logger = logging.getLogger(__name__)

T = TypeVar('T')


# ============================================================================
# Timing and Profiling
# ============================================================================

def timeit(func: Callable) -> Callable:
    """
    Decorator to measure function execution time.

    Example:
        @timeit
        def slow_function():
            time.sleep(1)
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        logger.info(f"{func.__name__} took {end - start:.4f} seconds")
        return result

    return wrapper


def timeit_async(func: Callable) -> Callable:
    """
    Decorator to measure async function execution time.

    Example:
        @timeit_async
        async def slow_async_function():
            await asyncio.sleep(1)
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = await func(*args, **kwargs)
        end = time.perf_counter()
        logger.info(f"{func.__name__} took {end - start:.4f} seconds")
        return result

    return wrapper


class PerformanceMonitor:
    """
    Monitor and track performance metrics for function calls.

    Example:
        monitor = PerformanceMonitor()

        @monitor.track
        def my_function():
            pass

        stats = monitor.get_stats('my_function')
    """

    def __init__(self):
        self._metrics: Dict[str, List[float]] = {}
        self._lock = threading.Lock()

    def track(self, func: Callable) -> Callable:
        """Decorator to track function performance."""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.perf_counter() - start
                with self._lock:
                    if func.__name__ not in self._metrics:
                        self._metrics[func.__name__] = []
                    self._metrics[func.__name__].append(duration)

        return wrapper

    def track_async(self, func: Callable) -> Callable:
        """Decorator to track async function performance."""
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.perf_counter() - start
                with self._lock:
                    if func.__name__ not in self._metrics:
                        self._metrics[func.__name__] = []
                    self._metrics[func.__name__].append(duration)

        return wrapper

    def get_stats(self, func_name: str) -> Optional[Dict[str, float]]:
        """Get statistics for a tracked function."""
        with self._lock:
            if func_name not in self._metrics or not self._metrics[func_name]:
                return None

            durations = self._metrics[func_name]
            return {
                'count': len(durations),
                'total': sum(durations),
                'avg': sum(durations) / len(durations),
                'min': min(durations),
                'max': max(durations),
            }

    def get_all_stats(self) -> Dict[str, Dict[str, float]]:
        """Get statistics for all tracked functions."""
        return {
            func_name: self.get_stats(func_name)
            for func_name in self._metrics.keys()
        }

    def reset(self, func_name: Optional[str] = None):
        """Reset metrics for a function or all functions."""
        with self._lock:
            if func_name:
                self._metrics.pop(func_name, None)
            else:
                self._metrics.clear()


# ============================================================================
# Caching
# ============================================================================

class LRUCache:
    """
    Thread-safe Least Recently Used (LRU) cache.

    Example:
        cache = LRUCache(max_size=100, ttl=300)
        cache.set('key', 'value')
        value = cache.get('key')
    """

    @dataclass
    class CacheEntry:
        value: Any
        expires_at: Optional[datetime] = None

    def __init__(self, max_size: int = 100, ttl: Optional[int] = None):
        """
        Initialize LRU cache.

        Args:
            max_size: Maximum number of items to cache
            ttl: Time-to-live in seconds (None for no expiration)
        """
        self.max_size = max_size
        self.ttl = ttl
        self._cache: OrderedDict = OrderedDict()
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        with self._lock:
            if key not in self._cache:
                return None

            entry = self._cache[key]

            # Check expiration
            if entry.expires_at and datetime.utcnow() > entry.expires_at:
                del self._cache[key]
                return None

            # Move to end (most recently used)
            self._cache.move_to_end(key)
            return entry.value

    def set(self, key: str, value: Any):
        """Set value in cache."""
        with self._lock:
            # Remove oldest if at capacity
            if len(self._cache) >= self.max_size and key not in self._cache:
                self._cache.popitem(last=False)

            # Calculate expiration
            expires_at = None
            if self.ttl:
                expires_at = datetime.utcnow() + timedelta(seconds=self.ttl)

            # Add or update entry
            self._cache[key] = self.CacheEntry(value=value, expires_at=expires_at)
            self._cache.move_to_end(key)

    def delete(self, key: str):
        """Delete key from cache."""
        with self._lock:
            self._cache.pop(key, None)

    def clear(self):
        """Clear entire cache."""
        with self._lock:
            self._cache.clear()

    def size(self) -> int:
        """Get current cache size."""
        with self._lock:
            return len(self._cache)


def cached(cache: LRUCache, key_func: Optional[Callable] = None):
    """
    Decorator to cache function results.

    Args:
        cache: Cache instance
        key_func: Function to generate cache key from args/kwargs

    Example:
        my_cache = LRUCache(max_size=100)

        @cached(my_cache)
        def expensive_function(x, y):
            return x + y
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                key = key_func(*args, **kwargs)
            else:
                key = f"{func.__name__}:{args}:{kwargs}"

            # Check cache
            result = cache.get(key)
            if result is not None:
                return result

            # Execute and cache
            result = func(*args, **kwargs)
            cache.set(key, result)
            return result

        return wrapper

    return decorator


# ============================================================================
# Batch Processing
# ============================================================================

async def batch_process(
    items: List[T],
    process_func: Callable[[T], Coroutine],
    batch_size: int = 10,
    max_concurrent: int = 5,
) -> List[Any]:
    """
    Process items in batches with controlled concurrency.

    Args:
        items: List of items to process
        process_func: Async function to process each item
        batch_size: Number of items per batch
        max_concurrent: Maximum concurrent tasks

    Returns:
        List of results

    Example:
        async def process_item(item):
            return item * 2

        results = await batch_process(items, process_item, batch_size=10)
    """
    results = []
    semaphore = asyncio.Semaphore(max_concurrent)

    async def process_with_semaphore(item):
        async with semaphore:
            return await process_func(item)

    # Process in batches
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        batch_results = await asyncio.gather(
            *[process_with_semaphore(item) for item in batch],
            return_exceptions=True,
        )
        results.extend(batch_results)

    return results


async def parallel_map(
    func: Callable[[T], Coroutine],
    items: List[T],
    max_concurrent: int = 10,
) -> List[Any]:
    """
    Map async function over items with concurrency control.

    Args:
        func: Async function to apply
        items: List of items
        max_concurrent: Maximum concurrent tasks

    Returns:
        List of results

    Example:
        async def square(x):
            return x ** 2

        results = await parallel_map(square, [1, 2, 3, 4, 5])
    """
    semaphore = asyncio.Semaphore(max_concurrent)

    async def run_with_semaphore(item):
        async with semaphore:
            return await func(item)

    return await asyncio.gather(*[run_with_semaphore(item) for item in items])


# ============================================================================
# Rate Limiting
# ============================================================================

class RateLimiter:
    """
    Token bucket rate limiter.

    Example:
        limiter = RateLimiter(rate=10, per=1.0)  # 10 requests per second

        async def make_request():
            await limiter.acquire()
            # Make request
    """

    def __init__(self, rate: int, per: float = 1.0):
        """
        Initialize rate limiter.

        Args:
            rate: Number of operations allowed
            per: Time period in seconds
        """
        self.rate = rate
        self.per = per
        self.allowance = rate
        self.last_check = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self, tokens: int = 1):
        """Acquire tokens, waiting if necessary."""
        async with self._lock:
            current = time.monotonic()
            time_passed = current - self.last_check
            self.last_check = current

            # Add new allowance based on time passed
            self.allowance += time_passed * (self.rate / self.per)

            # Cap at rate
            if self.allowance > self.rate:
                self.allowance = self.rate

            # Wait if not enough allowance
            if self.allowance < tokens:
                sleep_time = (tokens - self.allowance) * (self.per / self.rate)
                await asyncio.sleep(sleep_time)
                self.allowance = 0
            else:
                self.allowance -= tokens


def rate_limited(rate: int, per: float = 1.0):
    """
    Decorator for rate limiting async functions.

    Args:
        rate: Number of calls allowed
        per: Time period in seconds

    Example:
        @rate_limited(rate=10, per=1.0)
        async def api_call():
            pass
    """
    limiter = RateLimiter(rate, per)

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            await limiter.acquire()
            return await func(*args, **kwargs)

        return wrapper

    return decorator


# ============================================================================
# Retry Logic
# ============================================================================

async def retry_async(
    func: Callable[..., Coroutine[Any, Any, T]],
    *args,
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
    **kwargs,
) -> T:
    """
    Retry async function with exponential backoff.

    Args:
        func: Async function to retry
        args: Positional arguments for func
        max_attempts: Maximum number of attempts
        delay: Initial delay between retries in seconds
        backoff: Backoff multiplier
        exceptions: Tuple of exceptions to catch
        kwargs: Keyword arguments for func

    Returns:
        Function result

    Example:
        result = await retry_async(
            api_call,
            max_attempts=3,
            delay=1.0,
            backoff=2.0,
        )
    """
    last_exception = None

    for attempt in range(max_attempts):
        try:
            return await func(*args, **kwargs)
        except exceptions as e:
            last_exception = e
            if attempt < max_attempts - 1:
                sleep_time = delay * (backoff ** attempt)
                logger.warning(
                    f"Attempt {attempt + 1}/{max_attempts} failed: {e}. "
                    f"Retrying in {sleep_time:.2f}s..."
                )
                await asyncio.sleep(sleep_time)
            else:
                logger.error(f"All {max_attempts} attempts failed")

    raise last_exception


# ============================================================================
# Memory Management
# ============================================================================

class MemoryPool:
    """
    Simple object pool for memory optimization.

    Example:
        pool = MemoryPool(lambda: [], max_size=10)
        obj = pool.acquire()
        # Use object
        pool.release(obj)
    """

    def __init__(self, factory: Callable[[], T], max_size: int = 10):
        """
        Initialize memory pool.

        Args:
            factory: Function to create new objects
            max_size: Maximum pool size
        """
        self.factory = factory
        self.max_size = max_size
        self._pool: List[T] = []
        self._lock = threading.Lock()

    def acquire(self) -> T:
        """Acquire object from pool or create new one."""
        with self._lock:
            if self._pool:
                return self._pool.pop()
            return self.factory()

    def release(self, obj: T):
        """Release object back to pool."""
        with self._lock:
            if len(self._pool) < self.max_size:
                # Clear object if it has a clear method
                if hasattr(obj, 'clear'):
                    obj.clear()
                self._pool.append(obj)

    def size(self) -> int:
        """Get current pool size."""
        with self._lock:
            return len(self._pool)


# ============================================================================
# Global Performance Monitor
# ============================================================================

# Global monitor instance for convenience
global_monitor = PerformanceMonitor()
