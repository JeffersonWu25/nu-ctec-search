"""
Standardized logging configuration for the application.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

def setup_logger(
    name: str,
    log_file: Optional[Path] = None,
    level: int = logging.INFO,
    console: bool = True
) -> logging.Logger:
    """
    Setup a standardized logger.
    
    Args:
        name: Logger name (usually __name__)
        log_file: Optional file to write logs to
        level: Logging level
        console: Whether to also log to console
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_job_logger(job_name: str) -> logging.Logger:
    """Get a logger configured for job scripts."""
    from ..settings import settings
    
    log_file = settings.SCRAPED_DATA_DIR / f"{job_name}.log"
    return setup_logger(
        name=f"app.jobs.{job_name}",
        log_file=log_file,
        console=True
    )