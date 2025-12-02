"""Tests for FileLogger - Property 8: Log file contains required fields."""

import os
import re
import tempfile
from hypothesis import given, strategies as st, settings

from translatex.utils.file_logger import FileLogger


class TestFileLoggerProperties:
    """Property-based tests for FileLogger.
    
    **Feature: advanced-features, Property 8: Log file contains required fields**
    **Validates: Requirements 8.2**
    """
    
    @given(message=st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ", min_size=1, max_size=50))
    @settings(max_examples=100)
    def test_log_entry_contains_required_fields(self, message):
        """For any log message, the log entry SHALL contain timestamp, level, and message."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")
            logger = FileLogger(log_file=log_file, level="DEBUG", log_to_file=True)
            logger.setup(tmpdir)
            
            # Log the message
            logger.info(message)
            
            # Close logger to release file lock
            logger.close()
            
            # Read log file
            with open(log_file, "r", encoding="utf-8") as f:
                log_content = f.read()
            
            # Verify required fields
            # Format: "2024-01-01 12:00:00 | INFO     | message"
            timestamp_pattern = r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}"
            level_pattern = r"INFO\s*"
            
            assert re.search(timestamp_pattern, log_content), "Log entry missing timestamp"
            assert re.search(level_pattern, log_content), "Log entry missing level"
            assert message.strip() in log_content, "Log entry missing message"
    
    @given(level=st.sampled_from(["DEBUG", "INFO", "WARNING", "ERROR"]))
    @settings(max_examples=100)
    def test_log_level_appears_in_output(self, level):
        """For any log level, the level SHALL appear in the log entry."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")
            logger = FileLogger(log_file=log_file, level="DEBUG", log_to_file=True)
            logger.setup(tmpdir)
            
            # Log at specified level
            log_method = getattr(logger, level.lower())
            log_method("test message")
            
            # Close logger to release file lock
            logger.close()
            
            # Read and verify
            with open(log_file, "r", encoding="utf-8") as f:
                log_content = f.read()
            
            assert level in log_content, f"Log level {level} not found in output"


class TestFileLoggerUnit:
    """Unit tests for FileLogger."""
    
    def test_setup_creates_log_file(self):
        """Log file should be created when setup is called."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = FileLogger(level="INFO", log_to_file=True)
            log_path = logger.setup(tmpdir)
            
            assert log_path is not None
            logger.info("test")
            logger.close()
            assert os.path.exists(log_path)
    
    def test_log_summary_format(self):
        """Log summary should include all stats."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")
            logger = FileLogger(log_file=log_file, level="INFO", log_to_file=True)
            logger.setup(tmpdir)
            
            stats = {"Total segments": 10, "Translated": 8, "Cached": 2}
            logger.log_summary(stats)
            logger.close()
            
            with open(log_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            assert "Total segments: 10" in content
            assert "Translated: 8" in content
            assert "Cached: 2" in content
