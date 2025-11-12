"""
PostgreSQL MCP Server - Configuration Module

This module handles all configuration settings for the MCP server.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class AppSettings(BaseSettings):
    """
    Application settings for PostgreSQL MCP Server.
    
    Configuration is loaded from environment variables.
    See env.example for a complete list of available settings.
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
    postgres_connection_string: Optional[str] = None
    
    # ========================================================================
    # Server Configuration
    # ========================================================================
    mcp_server_host: str = "0.0.0.0"
    mcp_server_port: int = 8000
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
app_settings = AppSettings()

