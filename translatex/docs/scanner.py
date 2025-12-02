"""Documentation directory scanner."""

import os
import shutil
import hashlib
from pathlib import Path
from dataclasses import dataclass
from typing import List, Set

from translatex.utils.file_logger import get_logger


@dataclass
class DocFile:
    """A documentation file to be translated."""
    source_path: str
    relative_path: str
    output_path: str
    file_type: str  # "md" or "mdx"
    source_hash: str = ""
    
    def __post_init__(self):
        if not self.source_hash:
            self.source_hash = self._calculate_hash()
    
    def _calculate_hash(self) -> str:
        """Calculate SHA256 hash of file content."""
        try:
            with open(self.source_path, "rb") as f:
                return hashlib.sha256(f.read()).hexdigest()
        except IOError:
            return ""


class DocsScanner:
    """Scan documentation directories for markdown files."""
    
    # File extensions to translate
    TRANSLATABLE_EXTENSIONS = {".md", ".mdx"}
    
    # Extensions to copy without translation
    ASSET_EXTENSIONS = {
        ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp",  # Images
        ".json", ".yaml", ".yml", ".toml",  # Config
        ".css", ".scss", ".less",  # Styles
        ".js", ".ts", ".jsx", ".tsx",  # Scripts (in docs context, usually examples)
    }
    
    # Directories to skip
    SKIP_DIRS = {
        "node_modules", ".git", ".github", "__pycache__",
        ".next", ".nuxt", "dist", "build", ".cache"
    }
    
    def __init__(self, source_dir: str, output_dir: str):
        """Initialize scanner.
        
        Args:
            source_dir: Source documentation directory
            output_dir: Output directory for translated files
        """
        self.source_dir = Path(source_dir).resolve()
        self.output_dir = Path(output_dir).resolve()
        self.logger = get_logger()
    
    def scan(self) -> List[DocFile]:
        """Recursively find all .md and .mdx files.
        
        Returns:
            List of DocFile objects
        """
        files = []
        
        if not self.source_dir.exists():
            self.logger.error(f"Source directory not found: {self.source_dir}")
            return files
        
        for root, dirs, filenames in os.walk(self.source_dir):
            # Skip certain directories
            dirs[:] = [d for d in dirs if d not in self.SKIP_DIRS]
            
            for filename in filenames:
                source_path = Path(root) / filename
                ext = source_path.suffix.lower()
                
                if ext in self.TRANSLATABLE_EXTENSIONS:
                    relative = source_path.relative_to(self.source_dir)
                    output_path = self.output_dir / relative
                    
                    files.append(DocFile(
                        source_path=str(source_path),
                        relative_path=str(relative),
                        output_path=str(output_path),
                        file_type=ext[1:]  # Remove the dot
                    ))
        
        self.logger.info(f"Found {len(files)} documentation files")
        return files
    
    def get_relative_path(self, file_path: str) -> str:
        """Get path relative to source directory.
        
        Args:
            file_path: Absolute file path
            
        Returns:
            Relative path string
        """
        return str(Path(file_path).relative_to(self.source_dir))
    
    def get_output_path(self, file_path: str) -> str:
        """Get corresponding output path for a source file.
        
        Args:
            file_path: Source file path
            
        Returns:
            Output file path
        """
        relative = self.get_relative_path(file_path)
        return str(self.output_dir / relative)
    
    def copy_assets(self, extensions: Set[str] = None) -> int:
        """Copy non-translatable files to output directory.
        
        Args:
            extensions: Set of extensions to copy (default: ASSET_EXTENSIONS)
            
        Returns:
            Number of files copied
        """
        extensions = extensions or self.ASSET_EXTENSIONS
        copied = 0
        
        for root, dirs, filenames in os.walk(self.source_dir):
            dirs[:] = [d for d in dirs if d not in self.SKIP_DIRS]
            
            for filename in filenames:
                source_path = Path(root) / filename
                ext = source_path.suffix.lower()
                
                if ext in extensions:
                    relative = source_path.relative_to(self.source_dir)
                    output_path = self.output_dir / relative
                    
                    # Create parent directories
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Copy file
                    try:
                        shutil.copy2(source_path, output_path)
                        copied += 1
                    except IOError as e:
                        self.logger.warning(f"Failed to copy {source_path}: {e}")
        
        self.logger.info(f"Copied {copied} asset files")
        return copied
    
    def ensure_output_structure(self):
        """Create output directory structure mirroring source."""
        for root, dirs, _ in os.walk(self.source_dir):
            dirs[:] = [d for d in dirs if d not in self.SKIP_DIRS]
            
            for dir_name in dirs:
                source_dir = Path(root) / dir_name
                relative = source_dir.relative_to(self.source_dir)
                output_dir = self.output_dir / relative
                output_dir.mkdir(parents=True, exist_ok=True)
    
    def get_stats(self) -> dict:
        """Get statistics about the documentation directory.
        
        Returns:
            Dict with file counts by type
        """
        stats = {"md": 0, "mdx": 0, "assets": 0, "other": 0}
        
        for root, dirs, filenames in os.walk(self.source_dir):
            dirs[:] = [d for d in dirs if d not in self.SKIP_DIRS]
            
            for filename in filenames:
                ext = Path(filename).suffix.lower()
                if ext == ".md":
                    stats["md"] += 1
                elif ext == ".mdx":
                    stats["mdx"] += 1
                elif ext in self.ASSET_EXTENSIONS:
                    stats["assets"] += 1
                else:
                    stats["other"] += 1
        
        return stats
