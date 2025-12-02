"""Tests for BatchProcessor - Property 3."""

import os
import tempfile
from pathlib import Path
from hypothesis import given, strategies as st, settings

from translatex.batch import BatchProcessor


class TestBatchFileDiscoveryProperty:
    """Property-based tests for batch file discovery.
    
    **Feature: advanced-features, Property 3: Batch finds all DOCX files**
    **Validates: Requirements 2.1**
    """
    
    @given(
        docx_count=st.integers(min_value=0, max_value=10),
        other_count=st.integers(min_value=0, max_value=10)
    )
    @settings(max_examples=100)
    def test_finds_exactly_docx_files(self, docx_count, other_count):
        """For any directory, BatchProcessor SHALL return exactly the .docx files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create .docx files
            docx_files = []
            for i in range(docx_count):
                path = Path(tmpdir) / f"document_{i}.docx"
                path.touch()
                docx_files.append(str(path))
            
            # Create other files
            other_extensions = [".pdf", ".txt", ".doc", ".xlsx", ".pptx"]
            for i in range(other_count):
                ext = other_extensions[i % len(other_extensions)]
                path = Path(tmpdir) / f"other_{i}{ext}"
                path.touch()
            
            # Find files
            processor = BatchProcessor(translator_factory=lambda: None)
            found = processor.find_docx_files(tmpdir)
            
            # Verify count
            assert len(found) == docx_count, \
                f"Expected {docx_count} .docx files, found {len(found)}"
            
            # Verify all found files are .docx
            for f in found:
                assert f.endswith(".docx"), f"Non-docx file found: {f}"
    
    @given(filenames=st.lists(
        st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789_", min_size=1, max_size=20),
        min_size=1,
        max_size=10,
        unique=True
    ))
    @settings(max_examples=100)
    def test_finds_all_docx_regardless_of_name(self, filenames):
        """All .docx files should be found regardless of filename."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create files with various names
            created = []
            for name in filenames:
                path = Path(tmpdir) / f"{name}.docx"
                path.touch()
                created.append(str(path))
            
            processor = BatchProcessor(translator_factory=lambda: None)
            found = processor.find_docx_files(tmpdir)
            
            assert len(found) == len(created), \
                f"Expected {len(created)} files, found {len(found)}"
    
    @given(docx_count=st.integers(min_value=1, max_value=5))
    @settings(max_examples=100)
    def test_excludes_temp_files(self, docx_count):
        """Temp files starting with ~$ should be excluded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create normal .docx files
            for i in range(docx_count):
                path = Path(tmpdir) / f"document_{i}.docx"
                path.touch()
            
            # Create temp files (Word creates these)
            for i in range(3):
                path = Path(tmpdir) / f"~$document_{i}.docx"
                path.touch()
            
            processor = BatchProcessor(translator_factory=lambda: None)
            found = processor.find_docx_files(tmpdir)
            
            # Should only find normal files
            assert len(found) == docx_count
            for f in found:
                assert not Path(f).name.startswith("~$")


class TestBatchProcessorUnit:
    """Unit tests for BatchProcessor."""
    
    def test_empty_directory(self):
        """Empty directory should return empty list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            processor = BatchProcessor(translator_factory=lambda: None)
            found = processor.find_docx_files(tmpdir)
            assert found == []
    
    def test_nonexistent_directory_raises(self):
        """Non-existent directory should raise BatchError."""
        from translatex.utils.exceptions import BatchError
        
        processor = BatchProcessor(translator_factory=lambda: None)
        
        try:
            processor.find_docx_files("/nonexistent/path")
            assert False, "Should have raised BatchError"
        except BatchError:
            pass
    
    def test_file_path_raises(self):
        """File path (not directory) should raise BatchError."""
        from translatex.utils.exceptions import BatchError
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a file in the temp directory
            file_path = os.path.join(tmpdir, "test.docx")
            with open(file_path, "w") as f:
                f.write("test")
            
            try:
                processor = BatchProcessor(translator_factory=lambda: None)
                processor.find_docx_files(file_path)
                assert False, "Should have raised BatchError"
            except BatchError:
                pass
    
    def test_get_summary(self):
        """get_summary should return correct counts."""
        from translatex.batch import BatchResult
        
        processor = BatchProcessor(translator_factory=lambda: None)
        
        results = {
            "file1.docx": BatchResult("file1.docx", "success", "out1.docx"),
            "file2.docx": BatchResult("file2.docx", "success", "out2.docx"),
            "file3.docx": BatchResult("file3.docx", "failed", error="API error"),
        }
        
        summary = processor.get_summary(results)
        
        assert summary["total"] == 3
        assert summary["success_count"] == 2
        assert summary["failed_count"] == 1
