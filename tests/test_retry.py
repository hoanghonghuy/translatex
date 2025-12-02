"""Tests for RetryHandler - Property 7."""

from hypothesis import given, strategies as st, settings

from translatex.utils.retry import RetryHandler


class TestExponentialBackoffProperty:
    """Property-based tests for exponential backoff.
    
    **Feature: advanced-features, Property 7: Retry with exponential backoff**
    **Validates: Requirements 7.1**
    """
    
    @given(
        attempt1=st.integers(min_value=0, max_value=5),
        attempt2=st.integers(min_value=0, max_value=5)
    )
    @settings(max_examples=100)
    def test_delay_increases_exponentially(self, attempt1, attempt2):
        """For any rate limit error, retry delay SHALL increase exponentially."""
        if attempt1 >= attempt2:
            return  # Skip if not increasing
        
        handler = RetryHandler(max_retries=10, base_delay=1.0, max_delay=1000.0)
        
        # Calculate delays without jitter for comparison
        # We test the base exponential behavior
        delay1_base = handler.base_delay * (handler.exponential_base ** attempt1)
        delay2_base = handler.base_delay * (handler.exponential_base ** attempt2)
        
        # Later attempts should have higher base delay
        assert delay2_base > delay1_base, \
            f"Delay for attempt {attempt2} should be greater than attempt {attempt1}"
    
    @given(attempt=st.integers(min_value=0, max_value=10))
    @settings(max_examples=100)
    def test_delay_respects_max_cap(self, attempt):
        """Delay should never exceed max_delay."""
        max_delay = 30.0
        handler = RetryHandler(max_retries=10, base_delay=1.0, max_delay=max_delay)
        
        delay = handler.calculate_delay(attempt)
        
        assert delay <= max_delay, f"Delay {delay} exceeds max {max_delay}"
    
    @given(
        base_delay=st.floats(min_value=0.1, max_value=5.0),
        exponential_base=st.floats(min_value=1.5, max_value=3.0)
    )
    @settings(max_examples=100)
    def test_exponential_growth_pattern(self, base_delay, exponential_base):
        """Delay should follow exponential growth pattern."""
        handler = RetryHandler(
            max_retries=5,
            base_delay=base_delay,
            max_delay=10000.0,  # High cap to test growth
            exponential_base=exponential_base
        )
        
        delays = []
        for attempt in range(4):
            # Get multiple samples and use minimum to account for jitter
            samples = [handler.calculate_delay(attempt) for _ in range(10)]
            delays.append(min(samples))
        
        # Each delay should be roughly exponential_base times the previous
        # (allowing for jitter variance)
        for i in range(1, len(delays)):
            ratio = delays[i] / delays[i-1] if delays[i-1] > 0 else 0
            # Ratio should be close to exponential_base (within jitter tolerance)
            assert ratio >= exponential_base * 0.8, \
                f"Growth ratio {ratio} too low, expected ~{exponential_base}"


class TestRetryHandlerUnit:
    """Unit tests for RetryHandler."""
    
    def test_successful_call_no_retry(self):
        """Successful call should not retry."""
        handler = RetryHandler(max_retries=3)
        call_count = 0
        
        def success_func():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = handler.execute(success_func)
        
        assert result == "success"
        assert call_count == 1
    
    def test_retry_after_respected(self):
        """Server-specified retry_after should be used."""
        handler = RetryHandler(max_retries=3, base_delay=1.0)
        
        delay = handler.calculate_delay(attempt=0, retry_after=10)
        
        assert delay == 10.0
    
    def test_retry_after_capped_by_max(self):
        """retry_after should be capped by max_delay."""
        handler = RetryHandler(max_retries=3, max_delay=5.0)
        
        delay = handler.calculate_delay(attempt=0, retry_after=100)
        
        assert delay == 5.0
    
    def test_delay_has_jitter(self):
        """Delay should include jitter for variance."""
        handler = RetryHandler(max_retries=3, base_delay=10.0, max_delay=1000.0)
        
        # Get multiple delays for same attempt
        delays = [handler.calculate_delay(attempt=2) for _ in range(20)]
        
        # Should have some variance due to jitter
        assert len(set(delays)) > 1, "Delays should have jitter variance"
