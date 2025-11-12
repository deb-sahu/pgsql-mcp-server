"""
PostgreSQL Database Connection Manager

This module provides a generic, reusable connection manager for PostgreSQL databases.
It supports connection string configuration and async operations.
"""

import asyncpg
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager
import logging

logger = logging.getLogger(__name__)


class PostgresConnectionManager:
    """
    A generic PostgreSQL connection manager that accepts connection strings
    and provides async database operations.
    """
    
    def __init__(self, connection_string: str):
        """
        Initialize the connection manager with a database connection string.
        
        Args:
            connection_string: PostgreSQL connection string in format:
                postgresql://user:password@host:port/database
                or individual components can be parsed from the string
        """
        self.connection_string = connection_string
        self._pool: Optional[asyncpg.Pool] = None
    
    async def initialize_pool(self, min_size: int = 5, max_size: int = 20) -> None:
        """
        Initialize the connection pool.
        
        Args:
            min_size: Minimum number of connections in the pool
            max_size: Maximum number of connections in the pool
        """
        if self._pool is None:
            try:
                self._pool = await asyncpg.create_pool(
                    self.connection_string,
                    min_size=min_size,
                    max_size=max_size,
                    command_timeout=60
                )
                logger.info("Database connection pool initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize database pool: {str(e)}")
                raise
    
    async def close_pool(self) -> None:
        """Close the connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None
            logger.info("Database connection pool closed")
    
    @asynccontextmanager
    async def get_connection(self):
        """
        Get a database connection from the pool as a context manager.
        
        Yields:
            asyncpg.Connection: Database connection
        """
        if self._pool is None:
            await self.initialize_pool()
        
        async with self._pool.acquire() as connection:
            yield connection
    
    async def fetch(self, query: str, *args) -> List[asyncpg.Record]:
        """
        Execute a SELECT query and fetch all results.
        
        Args:
            query: SQL query to execute
            *args: Query parameters
            
        Returns:
            List of records
            
        Raises:
            Exception: If query execution fails
        """
        try:
            async with self.get_connection() as conn:
                return await conn.fetch(query, *args)
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            raise
    
    async def fetchrow(self, query: str, *args) -> Optional[asyncpg.Record]:
        """
        Execute a SELECT query and fetch a single row.
        
        Args:
            query: SQL query to execute
            *args: Query parameters
            
        Returns:
            Single record or None
            
        Raises:
            Exception: If query execution fails
        """
        try:
            async with self.get_connection() as conn:
                return await conn.fetchrow(query, *args)
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            raise
    
    async def execute(self, query: str, *args) -> str:
        """
        Execute a query that doesn't return results (INSERT, UPDATE, DELETE).
        
        Args:
            query: SQL query to execute
            *args: Query parameters
            
        Returns:
            Status string from the query execution
            
        Raises:
            Exception: If query execution fails
        """
        try:
            async with self.get_connection() as conn:
                return await conn.execute(query, *args)
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            raise
    
    async def fetch_as_dict(self, query: str, *args) -> List[Dict[str, Any]]:
        """
        Execute a SELECT query and return results as a list of dictionaries.
        
        Args:
            query: SQL query to execute
            *args: Query parameters
            
        Returns:
            List of dictionaries representing rows
            
        Raises:
            Exception: If query execution fails
        """
        try:
            records = await self.fetch(query, *args)
            return [dict(record) for record in records]
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            raise

