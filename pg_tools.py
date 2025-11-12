"""
PostgreSQL MCP Tools

This module contains all the MCP tools for interacting with PostgreSQL databases.
Each tool is designed to be generic, reusable, and provide structured JSON responses.

These tools provide context to the AI client (Cursor, VS Code, etc.) which will
use them to understand the database and generate appropriate SQL queries.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from db_connection import PostgresConnectionManager

logger = logging.getLogger(__name__)


class PostgresTools:
    """
    A collection of PostgreSQL database tools for MCP server.
    """
    
    def __init__(self, db_manager: PostgresConnectionManager):
        """
        Initialize PostgreSQL tools with a database connection manager.
        
        Args:
            db_manager: PostgresConnectionManager instance
        """
        self.db_manager = db_manager
    
    async def get_tables(
        self, 
        schema: Optional[str] = None,
        include_views: bool = False
    ) -> Dict[str, Any]:
        """
        Fetch and return a list of all table names in the PostgreSQL database.
        
        Args:
            schema: Optional schema name to filter tables. If None, returns tables from all schemas.
            include_views: Whether to include views in the results
            
        Returns:
            Dictionary containing:
                - success: bool
                - data: List of tables with metadata
                - error: Optional error message
        """
        try:
            # Build the query based on parameters
            if include_views:
                table_condition = "table_type IN ('BASE TABLE', 'VIEW')"
            else:
                table_condition = "table_type = 'BASE TABLE'"
            
            if schema:
                schema_condition = f"AND table_schema = '{schema}'"
            else:
                # Exclude system schemas
                schema_condition = "AND table_schema NOT IN ('pg_catalog', 'information_schema')"
            
            query = f"""
                SELECT 
                    t.table_schema,
                    t.table_name,
                    t.table_type,
                    (
                        SELECT COUNT(*)
                        FROM information_schema.columns c
                        WHERE c.table_schema = t.table_schema 
                        AND c.table_name = t.table_name
                    ) as column_count,
                    (
                        SELECT string_agg(column_name, ', ')
                        FROM information_schema.key_column_usage kcu
                        INNER JOIN information_schema.table_constraints tc
                        ON kcu.constraint_name = tc.constraint_name
                        AND kcu.table_schema = tc.table_schema
                        WHERE tc.constraint_type = 'PRIMARY KEY'
                        AND kcu.table_schema = t.table_schema
                        AND kcu.table_name = t.table_name
                    ) as primary_key_columns,
                    pg_size_pretty(pg_total_relation_size(
                        quote_ident(t.table_schema) || '.' || quote_ident(t.table_name)
                    )) as table_size
                FROM information_schema.tables t
                WHERE {table_condition}
                {schema_condition}
                ORDER BY t.table_schema, t.table_name;
            """
            
            results = await self.db_manager.fetch_as_dict(query)
            
            return {
                "success": True,
                "data": results,
                "count": len(results),
                "error": None
            }
        
        except Exception as e:
            logger.error(f"Error fetching tables: {str(e)}")
            return {
                "success": False,
                "data": [],
                "count": 0,
                "error": str(e)
            }
    
    async def get_routines_and_functions(
        self, 
        schema: Optional[str] = None,
        function_name_pattern: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieve all stored routines and functions from pg_catalog.pg_proc.
        
        Args:
            schema: Optional schema name to filter functions
            function_name_pattern: Optional pattern to filter function names (SQL LIKE pattern)
            
        Returns:
            Dictionary containing:
                - success: bool
                - data: List of functions with metadata
                - error: Optional error message
        """
        try:
            schema_condition = ""
            if schema:
                schema_condition = f"AND n.nspname = '{schema}'"
            else:
                schema_condition = "AND n.nspname NOT IN ('pg_catalog', 'information_schema')"
            
            name_condition = ""
            if function_name_pattern:
                name_condition = f"AND p.proname LIKE '{function_name_pattern}'"
            
            query = f"""
                SELECT 
                    n.nspname as schema_name,
                    p.proname as function_name,
                    pg_get_function_identity_arguments(p.oid) as arguments,
                    pg_get_function_result(p.oid) as return_type,
                    CASE p.prokind
                        WHEN 'f' THEN 'function'
                        WHEN 'p' THEN 'procedure'
                        WHEN 'a' THEN 'aggregate'
                        WHEN 'w' THEN 'window'
                        ELSE 'unknown'
                    END as routine_type,
                    CASE p.provolatile
                        WHEN 'i' THEN 'immutable'
                        WHEN 's' THEN 'stable'
                        WHEN 'v' THEN 'volatile'
                    END as volatility,
                    l.lanname as language,
                    pg_get_functiondef(p.oid) as definition
                FROM pg_proc p
                JOIN pg_namespace n ON p.pronamespace = n.oid
                JOIN pg_language l ON p.prolang = l.oid
                WHERE TRUE
                {schema_condition}
                {name_condition}
                ORDER BY n.nspname, p.proname;
            """
            
            results = await self.db_manager.fetch_as_dict(query)
            
            return {
                "success": True,
                "data": results,
                "count": len(results),
                "error": None
            }
        
        except Exception as e:
            logger.error(f"Error fetching routines and functions: {str(e)}")
            return {
                "success": False,
                "data": [],
                "count": 0,
                "error": str(e)
            }
    
    async def get_table_schema(
        self, 
        table_name: str,
        schema: str = "public"
    ) -> Dict[str, Any]:
        """
        Get detailed schema information for a specific table.
        
        Args:
            table_name: Name of the table
            schema: Schema name (defaults to 'public')
            
        Returns:
            Dictionary containing:
                - success: bool
                - data: Table schema details including columns, constraints, indexes
                - error: Optional error message
        """
        try:
            # Get column information
            columns_query = """
                SELECT 
                    column_name,
                    data_type,
                    character_maximum_length,
                    is_nullable,
                    column_default,
                    ordinal_position
                FROM information_schema.columns
                WHERE table_schema = $1
                AND table_name = $2
                ORDER BY ordinal_position;
            """
            
            columns = await self.db_manager.fetch_as_dict(columns_query, schema, table_name)
            
            # Get constraints
            constraints_query = """
                SELECT 
                    tc.constraint_name,
                    tc.constraint_type,
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints tc
                LEFT JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                LEFT JOIN information_schema.constraint_column_usage ccu
                    ON ccu.constraint_name = tc.constraint_name
                    AND ccu.table_schema = tc.table_schema
                WHERE tc.table_schema = $1
                AND tc.table_name = $2;
            """
            
            constraints = await self.db_manager.fetch_as_dict(constraints_query, schema, table_name)
            
            # Get indexes
            indexes_query = """
                SELECT
                    i.relname as index_name,
                    a.attname as column_name,
                    am.amname as index_type,
                    ix.indisunique as is_unique,
                    ix.indisprimary as is_primary
                FROM pg_index ix
                JOIN pg_class i ON i.oid = ix.indexrelid
                JOIN pg_class t ON t.oid = ix.indrelid
                JOIN pg_namespace n ON n.oid = t.relnamespace
                JOIN pg_am am ON am.oid = i.relam
                JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(ix.indkey)
                WHERE n.nspname = $1
                AND t.relname = $2;
            """
            
            indexes = await self.db_manager.fetch_as_dict(indexes_query, schema, table_name)
            
            return {
                "success": True,
                "data": {
                    "table_name": table_name,
                    "schema": schema,
                    "columns": columns,
                    "constraints": constraints,
                    "indexes": indexes
                },
                "error": None
            }
        
        except Exception as e:
            logger.error(f"Error fetching table schema: {str(e)}")
            return {
                "success": False,
                "data": {},
                "error": str(e)
            }
    
    async def execute_query(
        self, 
        query: str,
        limit: Optional[int] = 1000
    ) -> Dict[str, Any]:
        """
        Execute a SQL query and return results.
        
        Args:
            query: SQL query to execute
            limit: Maximum number of rows to return (safety limit)
            
        Returns:
            Dictionary containing:
                - success: bool
                - data: Query results
                - row_count: Number of rows returned
                - error: Optional error message
        """
        try:
            # Add limit to SELECT queries if not already present
            query_lower = query.lower().strip()
            if query_lower.startswith('select') and 'limit' not in query_lower:
                query = f"{query.rstrip(';')} LIMIT {limit}"
            
            # Prevent destructive operations (optional safety check)
            dangerous_keywords = ['drop', 'truncate', 'delete', 'update', 'insert', 'alter']
            if any(keyword in query_lower for keyword in dangerous_keywords):
                return {
                    "success": False,
                    "data": [],
                    "row_count": 0,
                    "error": "Destructive operations (DROP, DELETE, UPDATE, etc.) are not allowed through this tool"
                }
            
            results = await self.db_manager.fetch_as_dict(query)
            
            return {
                "success": True,
                "data": results,
                "row_count": len(results),
                "error": None
            }
        
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            return {
                "success": False,
                "data": [],
                "row_count": 0,
                "error": str(e)
            }
    
    async def get_database_schema_summary(self) -> Dict[str, Any]:
        """
        Get a comprehensive summary of the entire database schema.
        
        This tool provides all the context an AI needs to understand the database
        structure and generate appropriate SQL queries.
        
        Returns:
            Dictionary containing:
                - success: bool
                - data: Complete database schema summary
                - error: Optional error message
        """
        try:
            # Get all tables
            tables_result = await self.get_tables(include_views=False)
            
            if not tables_result["success"]:
                return tables_result
            
            # Get detailed schema for each table
            table_schemas = []
            for table in tables_result["data"]:
                schema_result = await self.get_table_schema(
                    table["table_name"],
                    table["table_schema"]
                )
                if schema_result["success"]:
                    table_schemas.append(schema_result["data"])
            
            # Get all functions
            functions_result = await self.get_routines_and_functions()
            
            return {
                "success": True,
                "data": {
                    "tables": tables_result["data"],
                    "detailed_schemas": table_schemas,
                    "functions": functions_result.get("data", []),
                    "summary": {
                        "total_tables": tables_result["count"],
                        "total_functions": functions_result.get("count", 0)
                    }
                },
                "error": None
            }
        
        except Exception as e:
            logger.error(f"Error getting database schema summary: {str(e)}")
            return {
                "success": False,
                "data": {},
                "error": str(e)
            }

