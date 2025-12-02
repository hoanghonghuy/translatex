"""Tests for DocsScanner - Properties 7-8."""

import os
import tempfile
from pathlib import Path
from hypothesis import given, strategies as st, settings

from translatex.docs.scanner import DocsScanner


class TestFileDiscovery:
    """Property-based tests for file discovery.
    
    **Feature: dev-docs-translator, Property 8: All markdown files found**
    **Validates: Requirements 3.1**
    """
    
    @given(
        md_count=st.integers(min_value=0, max_value=10),
        mdx_count=st.integers(min_value=0, max_value=10)
    )
    @settings(max_examples=50)
    def test_finds_all_markdown_files(self, md_count, mdx_count):
        """For any directory, scanner SHALL find all .md and .mdx files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            output_dir = Path(tmpdir) / "output"
            source_dir.mkdir()
            output_dir.mkdir()
            
            # Create .md files
            for i in range(md_count):
                (source_dir / f"doc_{i}.md").write_text(f"# Doc {i}")
            
            # Create .mdx files
            for i in range(mdx_count):
                (source_dir / f"page_{i}.mdx").write_text(f"# Page {i}")
            
            # Create some non-markdown files
            (source_dir / "image.png").write_bytes(b"fake image")
            (source_dir / "config.json").write_text("{}")
            
            # Scan
            scanner = DocsScanner(str(source_dir), str(output_dir))
            files = scanner.scan()
            
            # Verify counts
            assert len(files) == md_count + mdx_count
            
            # Verify types
            md_files = [f for f in files if f.file_type == "md"]
            mdx_files = [f for f in files if f.file_type == "mdx"]
            assert len(md_files) == md_count
            assert len(mdx_files) == mdx_count


class TestDirectoryStructure:
    """Property-based tests for directory structure.
    
    **Feature: dev-docs-translator, Property 7: Directory structure mirrored**
    **Validates: Requirements 3.2, 3.4**
    """
    
    @given(depth=st.integers(min_value=1, max_value=3))
    @settings(max_examples=20)
    def test_directory_structure_mirrored(self, depth):
        """For any source directory, output SHALL have identical structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            output_dir = Path(tmpdir) / "output"
            source_dir.mkdir()
            
            # Create nested structure
            current = source_dir
            for i in range(depth):
                current = current / f"level_{i}"
                current.mkdir()
                (current / f"doc_{i}.md").write_text(f"# Level {i}")
            
            # Scan and ensure structure
            scanner = DocsScanner(str(source_dir), str(output_dir))
            scanner.ensure_output_structure()
            
            # Verify structure is mirrored
            for root, dirs, _ in os.walk(source_dir):
                rel_path = Path(root).relative_to(source_dir)
                expected_output = output_dir / rel_path
                assert expected_output.exists(), f"Directory not mirrored: {rel_path}"


class TestDocsScannerUnit:
    """Unit tests for DocsScanner."""
    
    def test_scan_empty_directory(self):
        """Empty directory should return empty list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scanner = DocsScanner(tmpdir, tmpdir + "_out")
            files = scanner.scan()
            assert files == []
    
    def test_skip_node_modules(self):
        """node_modules should be skipped."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source"
            source.mkdir()
            
            # Create file in root
            (source / "readme.md").write_text("# Root")
            
            # Create file in node_modules (should be skipped)
            nm = source / "node_modules"
            nm.mkdir()
            (nm / "package.md").write_text("# Package")
            
            scanner = DocsScanner(str(source), str(source) + "_out")
            files = scanner.scan()
            
            assert len(files) == 1
            assert files[0].relative_path == "readme.md"
    
    def test_copy_assets(self):
        """Assets should be copied to output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source"
            output = Path(tmpdir) / "output"
            source.mkdir()
            output.mkdir()
            
            # Create assets
            (source / "logo.png").write_bytes(b"fake png")
            (source / "config.json").write_text('{"key": "value"}')
            
            scanner = DocsScanner(str(source), str(output))
            copied = scanner.copy_assets()
            
            assert copied == 2
            assert (output / "logo.png").exists()
            assert (output / "config.json").exists()
    
    def test_get_stats(self):
        """Stats should be accurate."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source"
            source.mkdir()
            
            (source / "doc1.md").write_text("# Doc 1")
            (source / "doc2.md").write_text("# Doc 2")
            (source / "page.mdx").write_text("# Page")
            (source / "image.png").write_bytes(b"img")
            
            scanner = DocsScanner(str(source), str(source) + "_out")
            stats = scanner.get_stats()
            
            assert stats["md"] == 2
            assert stats["mdx"] == 1
            assert stats["assets"] == 1
    
    def test_relative_path(self):
        """Relative paths should be correct."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source"
            output = Path(tmpdir) / "output"
            source.mkdir()
            
            # Create nested file
            nested = source / "docs" / "guide"
            nested.mkdir(parents=True)
            (nested / "intro.md").write_text("# Intro")
            
            scanner = DocsScanner(str(source), str(output))
            files = scanner.scan()
            
            assert len(files) == 1
            assert files[0].relative_path == os.path.join("docs", "guide", "intro.md")
