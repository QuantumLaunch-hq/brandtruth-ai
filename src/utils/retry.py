# src/utils/retry.py
"""Retry utilities with exponential backoff for API calls."""

import asyncio
import functools
import logging
import random
import time
from typing import Callable, TypeVar

logger = logging.getLogger("brandtruth")

T = TypeVar("T")


class RetryConfig:
    """Configuration for retry behavior."""
    
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_status_codes: tuple = (429, 500, 502, 503, 504, 529),
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retryable_status_codes = retryable_status_codes


DEFAULT_RETRY_CONFIG = RetryConfig(
    max_attempts=5,
    base_delay=2.0,
    max_delay=60.0,
)


def calculate_delay(attempt: int, config: RetryConfig) -> float:
    """Calculate delay with exponential backoff and optional jitter."""
    delay = min(
        config.base_delay * (config.exponential_base ** attempt),
        config.max_delay
    )
    if config.jitter:
        delay = delay * (0.5 + random.random())
    return delay


def is_retryable_error(error: Exception, config: RetryConfig) -> bool:
    """Check if an error is retryable."""
    error_str = str(error).lower()
    
    # Overloaded error
    if "overloaded" in error_str or "529" in error_str:
        return True
    
    # Rate limit
    if "rate" in error_str and "limit" in error_str:
        return True
    
    # Check status codes in error message
    for code in config.retryable_status_codes:
        if str(code) in error_str:
            return True
    
    return False


def retry_sync(config: RetryConfig = None):
    """Decorator for synchronous functions with retry logic."""
    if config is None:
        config = DEFAULT_RETRY_CONFIG
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_error = None
            
            for attempt in range(config.max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    
                    if not is_retryable_error(e, config):
                        logger.error(f"Non-retryable error in {func.__name__}: {e}")
                        raise
                    
                    if attempt < config.max_attempts - 1:
                        delay = calculate_delay(attempt, config)
                        logger.warning(
                            f"⚠️  Retryable error (attempt {attempt + 1}/{config.max_attempts}): {type(e).__name__}. "
                            f"Retrying in {delay:.1f}s..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"❌ Max retries ({config.max_attempts}) exceeded: {e}"
                        )
            
            raise last_error
        
        return wrapper
    return decorator


def retry_async(config: RetryConfig = None):
    """Decorator for async functions with retry logic."""
    if config is None:
        config = DEFAULT_RETRY_CONFIG
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_error = None
            
            for attempt in range(config.max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    
                    if not is_retryable_error(e, config):
                        logger.error(f"Non-retryable error in {func.__name__}: {e}")
                        raise
                    
                    if attempt < config.max_attempts - 1:
                        delay = calculate_delay(attempt, config)
                        logger.warning(
                            f"⚠️  Retryable error (attempt {attempt + 1}/{config.max_attempts}): {type(e).__name__}. "
                            f"Retrying in {delay:.1f}s..."
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            f"❌ Max retries ({config.max_attempts}) exceeded: {e}"
                        )
            
            raise last_error
        
        return wrapper
    return decorator


def retry_with_backoff(
    max_attempts: int = None,
    max_retries: int = None,  # Alias for max_attempts
    base_delay: float = 1.0,
    max_delay: float = 30.0,
):
    """
    Decorator for async functions with exponential backoff retry.
    
    Args:
        max_attempts: Maximum number of retry attempts
        max_retries: Alias for max_attempts (for backward compatibility)
        base_delay: Initial delay between retries
        max_delay: Maximum delay between retries
    
    Usage:
        @retry_with_backoff(max_attempts=3)
        async def my_api_call():
            ...
        
        # Or with alias:
        @retry_with_backoff(max_retries=3)
        async def my_api_call():
            ...
    """
    # Handle both parameter names
    attempts = max_attempts or max_retries or 3
    
    config = RetryConfig(
        max_attempts=attempts,
        base_delay=base_delay,
        max_delay=max_delay,
    )
    return retry_async(config)
