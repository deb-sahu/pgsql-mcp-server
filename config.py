"""
PostgreSQL MCP Server - Configuration Module

This module handles all configuration settings for the MCP server.
The .env file is loaded from the MCP server's installation directory,
allowing users to configure their database connection once and have it
work automatically without any additional prompts.
"""

from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path

# Get the directory where this config.py file is located
# This ensures .env is always found relative to the MCP server installation,
# not the current working directory (which varies by MCP client)
_CONFIG_DIR = Path(__file__).parent.resolve()
_ENV_FILE_PATH = _CONFIG_DIR / ".env"


class AppSettings(BaseSettings):
    """
    Application settings for PostgreSQL MCP Server.
    
    Configuration is automatically loaded from the .env file located
    in the same directory as the MCP server installation.
    """
    
    # ========================================================================
    # Database Configuration
    # ========================================================================
    db_user_name: str = ""
    db_password: str = ""
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = ""
    
    # Connection string takes precedence if provided
    # Supports both POSTGRES_CONNECTION_STRING and DATABASE_URL (common in cloud platforms)
    postgres_connection_string: Optional[str] = None
    database_url: Optional[str] = None
    
    @property
    def effective_connection_string(self) -> Optional[str]:
        """
        Returns the effective connection string, checking multiple sources.
        
        Priority:
        1. postgres_connection_string (explicit PostgreSQL connection)
        2. database_url (common in cloud platforms like Railway, Heroku)
        3. None (fall back to individual DB_* components)
        """
        return self.postgres_connection_string or self.database_url
    
    # ========================================================================
    # Server Configuration
    # ========================================================================
    mcp_server_host: str = "0.0.0.0"
    mcp_server_port: int = 8000
    
    class Config:
        env_file = str(_ENV_FILE_PATH)
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


# Global settings instance
app_settings = AppSettings()

