"""
Application settings and configuration.

Centralizes all environment variables and configuration in one place.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    """Application settings loaded from environment variables."""
    
    # Database settings
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_SECRET_KEY: str = os.getenv("SUPABASE_SECRET_KEY", "")
    
    # Project paths
    PROJECT_ROOT: Path = Path(__file__).parent.parent
    SCRAPED_DATA_DIR: Path = PROJECT_ROOT / "scraped_data"
    UPLOAD_DIR: Path = PROJECT_ROOT.parent / "docs" / "upload"
    SAMPLES_DIR: Path = PROJECT_ROOT.parent / "docs" / "samples"
    
    # Processing settings
    DEFAULT_BATCH_SIZE: int = 100
    DEFAULT_DELAY_SECONDS: float = 0.5
    DEFAULT_MAX_WORKERS: int = 3
    
    # Validation
    def __post_init__(self):
        """Validate required settings."""
        if not self.SUPABASE_URL:
            raise RuntimeError("SUPABASE_URL environment variable is required")
        if not self.SUPABASE_SECRET_KEY:
            raise RuntimeError("SUPABASE_SECRET_KEY environment variable is required")
    
    @classmethod
    def create_directories(cls):
        """Create necessary directories if they don't exist."""
        cls.SCRAPED_DATA_DIR.mkdir(exist_ok=True)

# Global settings instance
settings = Settings()
settings.__post_init__()