# src/utils/logging.py
"""Logging configuration for BrandTruth AI."""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for terminal output."""
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        # Add color to level name
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"
        
        # Add timestamp
        record.timestamp = datetime.now().strftime('%H:%M:%S')
        
        return super().format(record)


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    name: str = "brandtruth",
) -> logging.Logger:
    """
    Set up logging for the application.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional file path to write logs
        name: Logger name
        
    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers
    logger.handlers = []
    
    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_format = ColoredFormatter(
        '%(timestamp)s │ %(levelname)-8s │ %(message)s'
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str = "brandtruth") -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)


# Module-level logger
_logger: Optional[logging.Logger] = None


def init_logging(level: str = "INFO", log_file: Optional[str] = None):
    """Initialize global logging."""
    global _logger
    _logger = setup_logging(level=level, log_file=log_file)
    return _logger


def log_step(step: str, message: str):
    """Log a pipeline step with formatting."""
    logger = get_logger()
    logger.info(f"[{step}] {message}")


def log_progress(current: int, total: int, message: str):
    """Log progress with formatting."""
    logger = get_logger()
    pct = int((current / total) * 100) if total > 0 else 0
    bar_len = 20
    filled = int(bar_len * current / total) if total > 0 else 0
    bar = '█' * filled + '░' * (bar_len - filled)
    logger.info(f"[{bar}] {pct}% - {message}")


def log_success(message: str):
    """Log success message."""
    logger = get_logger()
    logger.info(f"✅ {message}")


def log_warning(message: str):
    """Log warning message."""
    logger = get_logger()
    logger.warning(f"⚠️  {message}")


def log_error(message: str):
    """Log error message."""
    logger = get_logger()
    logger.error(f"❌ {message}")
