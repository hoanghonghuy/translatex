"""File logging infrastructure for TranslateX."""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


class FileLogger:
    """Manages file and console logging for TranslateX."""
    
    LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(message)s"
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    
    def __init__(
        self,
        log_file: Optional[str] = None,
        level: str = "INFO",
        log_to_file: bool = True
    ):
        self.log_file = log_file
        self.level = getattr(logging, level.upper(), logging.INFO)
        self.log_to_file = log_to_file
        # Use unique logger name to avoid conflicts in tests
        self._logger_name = f"translatex_{id(self)}"
        self.logger = logging.getLogger(self._logger_name)
        self._setup_done = False
        self._file_handler = None
    
    def setup(self, output_dir: str = "output") -> str:
        """Configure file logging. Returns log file path."""
        if self._setup_done:
            return self.log_file
        
        self.logger.setLevel(self.level)
        self.logger.handlers.clear()
        
        formatter = logging.Formatter(self.LOG_FORMAT, self.DATE_FORMAT)
        
        # Console handler - only for WARNING and above to keep CLI clean
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.WARNING)
        self.logger.addHandler(console_handler)
        
        # File handler
        if self.log_to_file:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            if not self.log_file:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                self.log_file = str(Path(output_dir) / f"translatex_{timestamp}.log")
            
            self._file_handler = logging.FileHandler(self.log_file, encoding="utf-8")
            self._file_handler.setFormatter(formatter)
            self.logger.addHandler(self._file_handler)
        
        self._setup_done = True
        return self.log_file
    
    def close(self):
        """Close file handlers to release file locks."""
        if self._file_handler:
            self._file_handler.close()
            self.logger.removeHandler(self._file_handler)
            self._file_handler = None
        # Clear all handlers
        for handler in self.logger.handlers[:]:
            handler.close()
            self.logger.removeHandler(handler)
        self._setup_done = False
    
    def log_summary(self, stats: dict):
        """Log translation summary statistics - file only, no console."""
        # Only log to file, not console (to keep CLI clean)
        if self._file_handler:
            for key, value in stats.items():
                self._file_handler.stream.write(f"{key}: {value}\n")
            self._file_handler.flush()
    
    def debug(self, msg: str):
        self.logger.debug(msg)
    
    def info(self, msg: str):
        self.logger.info(msg)
    
    def warning(self, msg: str):
        self.logger.warning(msg)
    
    def error(self, msg: str):
        self.logger.error(msg)


# Global logger instance
_logger: Optional[FileLogger] = None


def get_logger() -> FileLogger:
    """Get or create global logger instance."""
    global _logger
    if _logger is None:
        _logger = FileLogger()
    return _logger


def setup_logger(
    log_file: Optional[str] = None,
    level: str = "INFO",
    log_to_file: bool = True,
    output_dir: str = "output"
) -> FileLogger:
    """Setup and return global logger."""
    global _logger
    _logger = FileLogger(log_file, level, log_to_file)
    _logger.setup(output_dir)
    return _logger
