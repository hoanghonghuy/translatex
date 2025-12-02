"""
Rate Limiter for WordFlux
Handles rate limiting and auto-retry for different providers
"""
import asyncio
import time
import logging
from functools import wraps

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter with provider-specific limits"""
    
    # Rate limits per provider (requests per minute)
    PROVIDER_LIMITS = {
        "openai": 60,      # Paid tier - high limit
        "openrouter": 15,  # Free tier - 20 RPM but be safe
        "groq": 10,        # Free tier - very limited
        "gemini": 12,      # Free tier - 15 RPM but be safe
    }
    
    def __init__(self, provider: str, max_concurrent: int = 5):
        self.provider = provider
        self.rpm_limit = self.PROVIDER_LIMITS.get(provider, 10)
        self.max_concurrent = min(max_concurrent, self.rpm_limit)
        self.request_times = []
        self.lock = asyncio.Lock()
        
        logger.info(f"RateLimiter initialized: {provider} ({self.rpm_limit} RPM, {self.max_concurrent} concurrent)")
    
    async def acquire(self):
        """Wait until we can make a request without exceeding rate limit"""
        async with self.lock:
            now = time.time()
            
            # Remove requests older than 60 seconds
            self.request_times = [t for t in self.request_times if now - t < 60]
            
            # If at limit, wait until oldest request expires
            if len(self.request_times) >= self.rpm_limit:
                wait_time = 60 - (now - self.request_times[0]) + 0.5
                if wait_time > 0:
                    logger.info(f"⏳ Rate limit reached, waiting {wait_time:.1f}s...")
                    await asyncio.sleep(wait_time)
                    # Clean up again after waiting
                    now = time.time()
                    self.request_times = [t for t in self.request_times if now - t < 60]
            
            # Record this request
            self.request_times.append(time.time())
    
    def get_semaphore(self) -> asyncio.Semaphore:
        """Get semaphore with appropriate concurrency limit"""
        return asyncio.Semaphore(self.max_concurrent)


async def retry_with_backoff(
    func,
    max_retries: int = 3,
    base_delay: float = 5.0,
    max_delay: float = 60.0
):
    """
    Retry a function with exponential backoff on rate limit errors.
    
    Args:
        func: Async function to call
        max_retries: Maximum number of retries
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
    """
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return await func()
        except Exception as e:
            error_str = str(e)
            last_exception = e
            
            # Check if it's a rate limit error
            is_rate_limit = (
                "429" in error_str or 
                "rate limit" in error_str.lower() or
                "quota" in error_str.lower() or
                "RESOURCE_EXHAUSTED" in error_str
            )
            
            if is_rate_limit and attempt < max_retries:
                # Calculate delay with exponential backoff
                delay = min(base_delay * (2 ** attempt), max_delay)
                
                # Try to extract retry delay from error message
                if "retry in" in error_str.lower():
                    try:
                        import re
                        match = re.search(r'retry in (\d+\.?\d*)', error_str.lower())
                        if match:
                            suggested_delay = float(match.group(1))
                            delay = max(delay, suggested_delay + 1)
                    except:
                        pass
                
                logger.warning(f"⏳ Rate limit hit, retrying in {delay:.1f}s (attempt {attempt + 1}/{max_retries})...")
                await asyncio.sleep(delay)
            else:
                # Not a rate limit error or max retries reached
                raise
    
    raise last_exception
