"""Custom exceptions for TranslateX."""


class TranslateXError(Exception):
    """Base exception for TranslateX."""
    pass


class ConfigError(TranslateXError):
    """Configuration related errors."""
    pass


class CheckpointError(TranslateXError):
    """Checkpoint related errors."""
    pass


class CacheError(TranslateXError):
    """Cache related errors."""
    pass


class APIError(TranslateXError):
    """API related errors."""
    
    def __init__(self, message: str, status_code: int = None, retryable: bool = False):
        super().__init__(message)
        self.status_code = status_code
        self.retryable = retryable


class RateLimitError(APIError):
    """Rate limit (429) error."""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = None):
        super().__init__(message, status_code=429, retryable=True)
        self.retry_after = retry_after


class ServerError(APIError):
    """Server (5xx) error."""
    
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message, status_code=status_code, retryable=True)


class ClientError(APIError):
    """Client (4xx) error - not retryable."""
    
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message, status_code=status_code, retryable=False)


class GlossaryError(TranslateXError):
    """Glossary related errors."""
    pass


class BatchError(TranslateXError):
    """Batch processing related errors."""
    pass
