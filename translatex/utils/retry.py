"""Retry handler with exponential backoff."""

import time
import random
from typing import Callable, TypeVar, Any
from functools import wraps

from .exceptions import RateLimitError, ServerError, ClientError, APIError
from .file_logger import get_logger

T = TypeVar("T")


class RetryHandler:
    """Handles retries with exponential backoff for API calls."""
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0
    ):
        """Initialize retry handler.
        
        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Initial delay in seconds
            max_delay: Maximum delay cap in seconds
            exponential_base: Base for exponential backoff
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
    
    def calculate_delay(self, attempt: int, retry_after: int = None) -> float:
        """Calculate delay for given attempt using exponential backoff.
        
        Args:
            attempt: Current attempt number (0-indexed)
            retry_after: Optional server-specified retry delay
            
        Returns:
            Delay in seconds
        """
        if retry_after:
            return min(retry_after, self.max_delay)
        
        # Exponential backoff with jitter
        delay = self.base_delay * (self.exponential_base ** attempt)
        # Add jitter (0-25% of delay)
        jitter = delay * random.uniform(0, 0.25)
        delay = delay + jitter
        
        return min(delay, self.max_delay)
    
    def execute(self, func: Callable[[], T], context: str = "") -> T:
        """Execute function with retry logic.
        
        Args:
            func: Function to execute
            context: Context string for logging
            
        Returns:
            Result of function
            
        Raises:
            Last exception if all retries exhausted
        """
        logger = get_logger()
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return func()
            except RateLimitError as e:
                last_exception = e
                if attempt < self.max_retries:
                    delay = self.calculate_delay(attempt, e.retry_after)
                    logger.warning(f"Rate limit hit{context}. Retrying in {delay:.1f}s (attempt {attempt + 1}/{self.max_retries})")
                    time.sleep(delay)
                else:
                    logger.error(f"Rate limit exceeded after {self.max_retries} retries{context}")
            except ServerError as e:
                last_exception = e
                if attempt < self.max_retries:
                    delay = self.calculate_delay(attempt)
                    logger.warning(f"Server error ({e.status_code}){context}. Retrying in {delay:.1f}s (attempt {attempt + 1}/{self.max_retries})")
                    time.sleep(delay)
                else:
                    logger.error(f"Server error after {self.max_retries} retries{context}")
            except ClientError as e:
                # Client errors are not retryable
                logger.error(f"Client error ({e.status_code}){context}: {e}")
                raise
            except Exception as e:
                # Unknown errors - retry with backoff
                last_exception = e
                if attempt < self.max_retries:
                    delay = self.calculate_delay(attempt)
                    logger.warning(f"Error{context}: {e}. Retrying in {delay:.1f}s")
                    time.sleep(delay)
                else:
                    logger.error(f"Failed after {self.max_retries} retries{context}: {e}")
        
        raise last_exception


def with_retry(max_retries: int = 3, base_delay: float = 1.0):
    """Decorator for adding retry logic to functions."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            handler = RetryHandler(max_retries=max_retries, base_delay=base_delay)
            return handler.execute(lambda: func(*args, **kwargs))
        return wrapper
    return decorator
