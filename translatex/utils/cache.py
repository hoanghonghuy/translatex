"""Translation caching for TranslateX."""

import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional

from .exceptions import CacheError


class TranslationCache:
    """Cache for storing and retrieving translations."""
    
    def __init__(self, cache_file: str = ".translatex_cache.json", enabled: bool = True):
        self.cache_file = cache_file
        self.enabled = enabled
        self.cache: dict = {}
        self._load()
    
    def _hash(self, text: str) -> str:
        """Generate SHA256 hash key for text."""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()
    
    def _load(self):
        """Load cache from file."""
        if not self.enabled:
            return
        
        path = Path(self.cache_file)
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self.cache = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                # Cache corrupted, start fresh
                self.cache = {}
    
    def _save(self):
        """Save cache to file."""
        if not self.enabled:
            return
        
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except IOError as e:
            raise CacheError(f"Failed to save cache: {e}")
    
    def get(self, source_text: str) -> Optional[str]:
        """Get cached translation by hash. Returns None if not found."""
        if not self.enabled:
            return None
        
        key = self._hash(source_text)
        entry = self.cache.get(key)
        if entry:
            return entry.get("translated")
        return None
    
    def set(self, source_text: str, translated: str):
        """Store translation in cache."""
        if not self.enabled:
            return
        
        key = self._hash(source_text)
        self.cache[key] = {
            "source": source_text,
            "translated": translated,
            "timestamp": datetime.now().isoformat()
        }
        self._save()
    
    def clear(self):
        """Clear all cached translations."""
        self.cache = {}
        path = Path(self.cache_file)
        if path.exists():
            path.unlink()
    
    def size(self) -> int:
        """Return number of cached entries."""
        return len(self.cache)
