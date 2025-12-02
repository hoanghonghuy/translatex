"""Tests for ContextWindow - Property 6."""

from hypothesis import given, strategies as st, settings

from translatex.utils.context import ContextWindow


class TestContextWindowProperty:
    """Property-based tests for context window.
    
    **Feature: advanced-features, Property 6: Context window includes N segments**
    **Validates: Requirements 4.1**
    """
    
    @given(
        window_size=st.integers(min_value=1, max_value=10),
        segments=st.lists(st.text(min_size=1, max_size=50), min_size=1, max_size=20)
    )
    @settings(max_examples=100)
    def test_context_window_includes_n_segments(self, window_size, segments):
        """For any context_window=N config, exactly N previous segments SHALL be included."""
        context = ContextWindow(window_size=window_size)
        
        # Add all segments
        for seg in segments:
            context.add(seg)
        
        # Get context segments
        context_segments = context.get_context_segments()
        
        # Should have at most window_size segments
        expected_count = min(window_size, len(segments))
        assert len(context_segments) == expected_count, \
            f"Expected {expected_count} segments, got {len(context_segments)}"
        
        # Should be the most recent segments
        if len(segments) >= window_size:
            expected_segments = segments[-window_size:]
            assert context_segments == expected_segments, \
                "Context should contain most recent N segments"
    
    @given(segments=st.lists(st.text(min_size=1, max_size=50), min_size=1, max_size=10))
    @settings(max_examples=100)
    def test_zero_window_returns_empty(self, segments):
        """For context_window=0, no context SHALL be included."""
        context = ContextWindow(window_size=0)
        
        for seg in segments:
            context.add(seg)
        
        assert context.get_context() is None
        assert context.get_context_segments() == []
        assert context.format_for_prompt() == ""
    
    @given(
        window_size=st.integers(min_value=1, max_value=5),
        segment=st.text(min_size=1, max_size=50)
    )
    @settings(max_examples=100)
    def test_context_contains_added_segment(self, window_size, segment):
        """Added segment should appear in context."""
        context = ContextWindow(window_size=window_size)
        context.add(segment)
        
        context_text = context.get_context()
        assert segment in context_text


class TestContextWindowUnit:
    """Unit tests for ContextWindow."""
    
    def test_sliding_window_behavior(self):
        """Window should slide, keeping only recent segments."""
        context = ContextWindow(window_size=2)
        
        context.add("first")
        context.add("second")
        context.add("third")
        
        segments = context.get_context_segments()
        assert segments == ["second", "third"]
        assert "first" not in context.get_context()
    
    def test_clear_removes_all(self):
        """clear() should remove all segments."""
        context = ContextWindow(window_size=3)
        context.add("one")
        context.add("two")
        
        context.clear()
        
        assert context.size() == 0
        assert context.get_context() is None
    
    def test_format_for_prompt_includes_markers(self):
        """Formatted prompt should include reference markers."""
        context = ContextWindow(window_size=2)
        context.add("previous text")
        
        formatted = context.format_for_prompt()
        
        assert "[CONTEXT" in formatted
        assert "reference only" in formatted.lower()
        assert "previous text" in formatted
        assert "[END CONTEXT]" in formatted
    
    def test_size_returns_current_count(self):
        """size() should return current segment count."""
        context = ContextWindow(window_size=5)
        
        assert context.size() == 0
        context.add("one")
        assert context.size() == 1
        context.add("two")
        assert context.size() == 2
