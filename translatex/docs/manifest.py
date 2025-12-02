"""Manifest manager for incremental documentation translation."""

import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional

from translatex.utils.file_logger import get_logger


class ManifestManager:
    """Manage translation manifest for incremental updates."""
    
    MANIFEST_VERSION = "1.0"
    
    def __init__(self, manifest_file: str):
        """Initialize manifest manager.
        
        Args:
            manifest_file: Path to manifest JSON file
        """
        self.manifest_file = Path(manifest_file)
        self.manifest = {
            "version": self.MANIFEST_VERSION,
            "source_dir": "",
            "output_dir": "",
            "created_at": "",
            "updated_at": "",
            "files": {}
        }
        self.logger = get_logger()
    
    def load(self) -> bool:
        """Load existing manifest from file.
        
        Returns:
            True if loaded successfully, False otherwise
        """
        if not self.manifest_file.exists():
            return False
        
        try:
            with open(self.manifest_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Validate version
            if data.get("version") != self.MANIFEST_VERSION:
                self.logger.warning("Manifest version mismatch, starting fresh")
                return False
            
            self.manifest = data
            self.logger.info(f"Loaded manifest with {len(self.manifest['files'])} entries")
            return True
        except (json.JSONDecodeError, IOError) as e:
            self.logger.warning(f"Failed to load manifest: {e}")
            return False
    
    def save(self):
        """Save manifest to file."""
        self.manifest["updated_at"] = datetime.now().isoformat()
        
        # Ensure parent directory exists
        self.manifest_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(self.manifest_file, "w", encoding="utf-8") as f:
                json.dump(self.manifest, f, ensure_ascii=False, indent=2)
            self.logger.debug(f"Saved manifest to {self.manifest_file}")
        except IOError as e:
            self.logger.error(f"Failed to save manifest: {e}")
    
    def set_directories(self, source_dir: str, output_dir: str):
        """Set source and output directories in manifest.
        
        Args:
            source_dir: Source documentation directory
            output_dir: Output directory
        """
        self.manifest["source_dir"] = str(source_dir)
        self.manifest["output_dir"] = str(output_dir)
        if not self.manifest["created_at"]:
            self.manifest["created_at"] = datetime.now().isoformat()
    
    def get_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of file content.
        
        Args:
            file_path: Path to file
            
        Returns:
            Hash string
        """
        try:
            with open(file_path, "rb") as f:
                return hashlib.sha256(f.read()).hexdigest()
        except IOError:
            return ""
    
    def is_changed(self, relative_path: str, source_path: str) -> bool:
        """Check if file has changed since last translation.
        
        Args:
            relative_path: Relative path (used as key)
            source_path: Absolute source path
            
        Returns:
            True if file is new or changed, False if unchanged
        """
        entry = self.manifest["files"].get(relative_path)
        if not entry:
            return True  # New file
        
        current_hash = self.get_file_hash(source_path)
        return entry.get("source_hash") != current_hash
    
    def update(self, relative_path: str, source_hash: str, output_path: str):
        """Update manifest entry for a file.
        
        Args:
            relative_path: Relative path (used as key)
            source_hash: Hash of source file
            output_path: Path to translated output file
        """
        self.manifest["files"][relative_path] = {
            "source_hash": source_hash,
            "output_path": output_path,
            "translated_at": datetime.now().isoformat()
        }
    
    def remove(self, relative_path: str):
        """Remove a file entry from manifest.
        
        Args:
            relative_path: Relative path to remove
        """
        self.manifest["files"].pop(relative_path, None)
    
    def get_entry(self, relative_path: str) -> Optional[dict]:
        """Get manifest entry for a file.
        
        Args:
            relative_path: Relative path
            
        Returns:
            Entry dict or None
        """
        return self.manifest["files"].get(relative_path)
    
    def get_all_entries(self) -> dict:
        """Get all file entries.
        
        Returns:
            Dict of all file entries
        """
        return self.manifest["files"].copy()
    
    def get_stats(self) -> dict:
        """Get manifest statistics.
        
        Returns:
            Dict with statistics
        """
        return {
            "total_files": len(self.manifest["files"]),
            "source_dir": self.manifest["source_dir"],
            "output_dir": self.manifest["output_dir"],
            "created_at": self.manifest["created_at"],
            "updated_at": self.manifest["updated_at"]
        }
    
    def clear(self):
        """Clear all file entries from manifest."""
        self.manifest["files"] = {}
