"""
Logging configuration for the application.
"""
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

from pythonjsonlogger.json import JsonFormatter


def setup_logger(name: str, log_file: Optional[str] = None, level: int = logging.DEBUG):
    """
    Setup logger with both console and file handlers.
    
    Args:
        name: Logger name
        log_file: Path to log file (optional)
        level: Logging level
    
    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers
    logger.handlers = []
    
    # Console handler (human-readable)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # File handler (JSON format for parsing)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        json_format = JsonFormatter(
            '%(asctime)s %(name)s %(levelname)s %(message)s'
        )
        file_handler.setFormatter(json_format)
        logger.addHandler(file_handler)
    
    return logger


# Create default logger
default_logger = setup_logger(
    "subu_chatbot",
    log_file=f"./logs/app_{datetime.now().strftime('%Y%m%d')}.log"
)
