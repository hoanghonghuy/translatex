"""Tests for TranslationCache - Properties 4 & 5."""

import os
import tempfile
from hypothesis import given, strategies as st, settings

from translatex.utils.cache import TranslationCache


class TestCacheHashProperty:
    """Property-based tests for cache hash consistency.
    
    **Feature: advanced-features, Property 4: Cache lookup by hash**
    **Validates: Requirements 6.1, 6.4**
    """
    
    @given(text=st.text(min_size=1, max_size=1000))
    @settings(max_examples=100)
    def test_hash_consistency(self, text):
        """For any source text, cache lookup SHALL use consistent hash as key."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_file = os.path.join(tmpdir, "cache.json")
            cache = TranslationCache(cache_file=cache_file, enabled=True)
            
            # Hash should be consistent
            hash1 = cache._hash(text)
            hash2 = cache._hash(text)
            assert hash1 == hash2, "Hash should be consistent for same text"
    
    @given(
        text1=st.text(min_size=1, max_size=100),
        text2=st.text(min_size=1, max_size=100)
    )
    @settings(max_examples=100)
    def test_different_texts_different_hashes(self, text1, text2):
        """Different texts should produce different hashes (with high probability)."""
        if text1 == text2:
            return  # Skip if texts are same
        
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_file = os.path.join(tmpdir, "cache.json")
            cache = TranslationCache(cache_file=cache_file, enabled=True)
            
            hash1 = cache._hash(text1)
            hash2 = cache._hash(text2)
            assert hash1 != hash2, "Different texts should have different hashes"
    
    @given(
        source=st.text(min_size=1, max_size=100),
        translated=st.text(min_size=1, max_size=100)
    )
    @settings(max_examples=100)
    def test_cache_roundtrip(self, source, translated):
        """For any text, set then get should return the same translation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_file = os.path.join(tmpdir, "cache.json")
            cache = TranslationCache(cache_file=cache_file, enabled=True)
            
            cache.set(source, translated)
            result = cache.get(source)
            assert result == translated, "Cache roundtrip should preserve translation"


class TestCacheHitProperty:
    """Property-based tests for cache hit behavior.
    
    **Feature: advanced-features, Property 5: Cache hit prevents API call**
    **Validates: Requirements 6.2**
    """
    
    @given(
        source=st.text(min_size=1, max_size=100),
        translated=st.text(min_size=1, max_size=100)
    )
    @settings(max_examples=100)
    def test_cache_hit_returns_cached_value(self, source, translated):
        """For any cached translation, get SHALL return cached value without needing API."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_file = os.path.join(tmpdir, "cache.json")
            cache = TranslationCache(cache_file=cache_file, enabled=True)
            
            # Store translation
            cache.set(source, translated)
            
            # Cache hit should return value
            result = cache.get(source)
            assert result is not None, "Cache hit should return value"
            assert result == translated, "Cache hit should return correct translation"


class TestCacheUnit:
    """Unit tests for TranslationCache."""
    
    def test_disabled_cache_returns_none(self):
        """Disabled cache should always return None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_file = os.path.join(tmpdir, "cache.json")
            cache = TranslationCache(cache_file=cache_file, enabled=False)
            
            cache.set("hello", "xin chao")
            assert cache.get("hello") is None
    
    def test_cache_persistence(self):
        """Cache should persist across instances."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_file = os.path.join(tmpdir, "cache.json")
            
            # First instance
            cache1 = TranslationCache(cache_file=cache_file, enabled=True)
            cache1.set("hello", "xin chao")
            
            # Second instance should load from file
            cache2 = TranslationCache(cache_file=cache_file, enabled=True)
            assert cache2.get("hello") == "xin chao"
    
    def test_cache_clear(self):
        """Clear should remove all entries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_file = os.path.join(tmpdir, "cache.json")
            cache = TranslationCache(cache_file=cache_file, enabled=True)
            
            cache.set("hello", "xin chao")
            assert cache.size() == 1
            
            cache.clear()
            assert cache.size() == 0
            assert cache.get("hello") is None
