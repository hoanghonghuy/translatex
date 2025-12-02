"""Checkpoint management for resume functionality."""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional

from .exceptions import CheckpointError


class CheckpointManager:
    """Manages translation checkpoints for resume functionality."""
    
    def __init__(self, checkpoint_file: str):
        self.checkpoint_file = checkpoint_file
    
    def save(self, segments: list, translated_indices: set, translations: dict = None):
        """Save current progress to checkpoint file.
        
        Args:
            segments: List of all segments
            translated_indices: Set of indices that have been translated
            translations: Dict mapping index to translated text
        """
        try:
            data = {
                "timestamp": datetime.now().isoformat(),
                "total_segments": len(segments),
                "translated_indices": list(translated_indices),
                "translations": translations or {},
                "segments_hash": self._hash_segments(segments)
            }
            with open(self.checkpoint_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except IOError as e:
            raise CheckpointError(f"Failed to save checkpoint: {e}")
    
    def load(self) -> tuple[set, dict]:
        """Load existing checkpoint.
        
        Returns:
            Tuple of (translated_indices set, translations dict)
        """
        if not self.exists():
            return set(), {}
        
        try:
            with open(self.checkpoint_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            translated_indices = set(data.get("translated_indices", []))
            translations = data.get("translations", {})
            # Convert string keys back to int
            translations = {int(k): v for k, v in translations.items()}
            return translated_indices, translations
        except (json.JSONDecodeError, IOError) as e:
            raise CheckpointError(f"Failed to load checkpoint: {e}")
    
    def exists(self) -> bool:
        """Check if checkpoint file exists."""
        return Path(self.checkpoint_file).exists()
    
    def clear(self):
        """Remove checkpoint file."""
        path = Path(self.checkpoint_file)
        if path.exists():
            path.unlink()
    
    def get_progress(self) -> Optional[dict]:
        """Get checkpoint progress info without full load."""
        if not self.exists():
            return None
        
        try:
            with open(self.checkpoint_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {
                "timestamp": data.get("timestamp"),
                "total": data.get("total_segments", 0),
                "completed": len(data.get("translated_indices", []))
            }
        except (json.JSONDecodeError, IOError):
            return None
    
    def _hash_segments(self, segments: list) -> str:
        """Create hash of segments for validation."""
        import hashlib
        content = "".join(str(s) for s in segments)
        return hashlib.md5(content.encode()).hexdigest()
    
    def validate(self, segments: list) -> bool:
        """Validate checkpoint matches current segments."""
        if not self.exists():
            return False
        
        try:
            with open(self.checkpoint_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            stored_hash = data.get("segments_hash")
            current_hash = self._hash_segments(segments)
            return stored_hash == current_hash
        except (json.JSONDecodeError, IOError):
            return False
