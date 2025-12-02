"""Tests for ManifestManager - Properties 10-11."""

import os
import tempfile
from pathlib import Path
from hypothesis import given, strategies as st, settings

from translatex.docs.manifest import ManifestManager


class TestFileChangeDetection:
    """Property-based tests for file change detection.
    
    **Feature: dev-docs-translator, Property 10: File change detection**
    **Validates: Requirements 5.1, 5.2**
    """
    
    @given(content=st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789 \n", min_size=10, max_size=100))
    @settings(max_examples=50)
    def test_unchanged_file_detected(self, content):
        """For any unchanged file, is_changed SHALL return False."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create manifest
            manifest_file = Path(tmpdir) / "manifest.json"
            manifest = ManifestManager(str(manifest_file))
            
            # Create a file
            test_file = Path(tmpdir) / "test.md"
            test_file.write_text(content, encoding="utf-8")
            
            # Record in manifest
            file_hash = manifest.get_file_hash(str(test_file))
            manifest.update("test.md", file_hash, str(test_file))
            manifest.save()
            
            # Load fresh manifest
            manifest2 = ManifestManager(str(manifest_file))
            manifest2.load()
            
            # File should be detected as unchanged
            assert not manifest2.is_changed("test.md", str(test_file))
    
    @given(
        content1=st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789 ", min_size=10, max_size=50),
        content2=st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789 ", min_size=10, max_size=50)
    )
    @settings(max_examples=50)
    def test_changed_file_detected(self, content1, content2):
        """For any changed file, is_changed SHALL return True."""
        if content1 == content2:
            return  # Skip if same content
        
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_file = Path(tmpdir) / "manifest.json"
            manifest = ManifestManager(str(manifest_file))
            
            test_file = Path(tmpdir) / "test.md"
            
            # Write initial content
            test_file.write_text(content1, encoding="utf-8")
            file_hash = manifest.get_file_hash(str(test_file))
            manifest.update("test.md", file_hash, str(test_file))
            manifest.save()
            
            # Change file content
            test_file.write_text(content2, encoding="utf-8")
            
            # Load fresh manifest
            manifest2 = ManifestManager(str(manifest_file))
            manifest2.load()
            
            # File should be detected as changed
            assert manifest2.is_changed("test.md", str(test_file))


class TestManifestAccuracy:
    """Property-based tests for manifest accuracy.
    
    **Feature: dev-docs-translator, Property 11: Manifest accuracy**
    **Validates: Requirements 5.4**
    """
    
    @given(
        files=st.lists(
            st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=3, max_size=10),
            min_size=1,
            max_size=10,
            unique=True
        )
    )
    @settings(max_examples=50)
    def test_manifest_contains_all_files(self, files):
        """For any set of files, manifest SHALL contain accurate entries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_file = Path(tmpdir) / "manifest.json"
            manifest = ManifestManager(str(manifest_file))
            
            # Create files and add to manifest
            for filename in files:
                filepath = Path(tmpdir) / f"{filename}.md"
                filepath.write_text(f"# {filename}")
                
                file_hash = manifest.get_file_hash(str(filepath))
                manifest.update(f"{filename}.md", file_hash, str(filepath))
            
            manifest.save()
            
            # Load and verify
            manifest2 = ManifestManager(str(manifest_file))
            manifest2.load()
            
            entries = manifest2.get_all_entries()
            assert len(entries) == len(files)
            
            for filename in files:
                assert f"{filename}.md" in entries


class TestManifestManagerUnit:
    """Unit tests for ManifestManager."""
    
    def test_new_manifest(self):
        """New manifest should have empty files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = ManifestManager(str(Path(tmpdir) / "manifest.json"))
            
            assert manifest.get_all_entries() == {}
    
    def test_save_and_load(self):
        """Manifest should persist correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_file = Path(tmpdir) / "manifest.json"
            
            # Save
            manifest = ManifestManager(str(manifest_file))
            manifest.set_directories("/source", "/output")
            manifest.update("test.md", "abc123", "/output/test.md")
            manifest.save()
            
            # Load
            manifest2 = ManifestManager(str(manifest_file))
            loaded = manifest2.load()
            
            assert loaded
            assert manifest2.get_entry("test.md") is not None
            assert manifest2.get_entry("test.md")["source_hash"] == "abc123"
    
    def test_remove_entry(self):
        """Entry should be removable."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = ManifestManager(str(Path(tmpdir) / "manifest.json"))
            
            manifest.update("test.md", "hash", "/path")
            assert manifest.get_entry("test.md") is not None
            
            manifest.remove("test.md")
            assert manifest.get_entry("test.md") is None
    
    def test_clear(self):
        """Clear should remove all entries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = ManifestManager(str(Path(tmpdir) / "manifest.json"))
            
            manifest.update("a.md", "hash1", "/a")
            manifest.update("b.md", "hash2", "/b")
            
            manifest.clear()
            
            assert manifest.get_all_entries() == {}
    
    def test_get_stats(self):
        """Stats should be accurate."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = ManifestManager(str(Path(tmpdir) / "manifest.json"))
            manifest.set_directories("/source", "/output")
            manifest.update("a.md", "h1", "/a")
            manifest.update("b.md", "h2", "/b")
            
            stats = manifest.get_stats()
            
            assert stats["total_files"] == 2
            assert stats["source_dir"] == "/source"
    
    def test_new_file_is_changed(self):
        """New file should be detected as changed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = ManifestManager(str(Path(tmpdir) / "manifest.json"))
            
            test_file = Path(tmpdir) / "new.md"
            test_file.write_text("# New")
            
            # File not in manifest should be "changed" (needs translation)
            assert manifest.is_changed("new.md", str(test_file))
