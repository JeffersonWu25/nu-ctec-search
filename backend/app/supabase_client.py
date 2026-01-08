"""
Supabase client factory and connection management.

Provides a single, properly configured Supabase client instance.
"""

from supabase import create_client, Client
from .settings import settings

def create_supabase_client() -> Client:
    """Create and configure a Supabase client instance."""
    return create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_SECRET_KEY
    )

# Global client instance
supabase: Client = create_supabase_client()