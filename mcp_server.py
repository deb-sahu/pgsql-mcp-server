"""
Generic PostgreSQL MCP Server

Enterprise-grade Model Context Protocol (MCP) server for PostgreSQL databases.
This server provides intelligent database tools for querying, exploring, and analyzing 
PostgreSQL databases through a standardized MCP interface.

The server accepts a database connection string as a configurable property,
making it compatible with any MCP client (Cursor, VS Code Agent, etc.).

The AI client (not this server) handles natural language to SQL conversion
using the schema context provided by these tools.
"""

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field
from typing import Optional
import logging
import os

from db_connection import PostgresConnectionManager
from pg_tools import PostgresTools
from config import app_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MCP server
mcp = FastMCP("postgres-mcp-server")

# Multi-tenant mode: Each client provides their own connection string
# Connection string is passed via environment variable in the MCP client configuration


# ============================================================================
# MCP Tool Request Models
# ============================================================================

# Connection string field description - tells AI to use POSTGRES_CONNECTION_STRING from mcp.json
CONNECTION_STRING_DESC = "PostgreSQL connection URL. IMPORTANT: Use the POSTGRES_CONNECTION_STRING value from your mcp.json env configuration. Format: postgresql://user:password@host:port/database"


class GetTablesRequest(BaseModel):
    """Request model for getting database tables."""
    connection_string: str = Field(
        ...,
        description=CONNECTION_STRING_DESC
    )
    schema_name: Optional[str] = Field(
        None,
        alias="schema",
        description="Optional schema name to filter tables. If not provided, returns tables from all user schemas."
    )
    include_views: bool = Field(
        False,
        description="Whether to include views in the results"
    )
    
    model_config = {"populate_by_name": True}


class GetRoutinesRequest(BaseModel):
    """Request model for getting database routines and functions."""
    connection_string: str = Field(
        ...,
        description=CONNECTION_STRING_DESC
    )
    schema_name: Optional[str] = Field(
        None,
        alias="schema",
        description="Optional schema name to filter functions"
    )
    function_name_pattern: Optional[str] = Field(
        None,
        description="Optional pattern to filter function names (SQL LIKE pattern, e.g., 'calculate%')"
    )
    
    model_config = {"populate_by_name": True}


class GetTableSchemaRequest(BaseModel):
    """Request model for getting detailed table schema."""
    connection_string: str = Field(
        ...,
        description=CONNECTION_STRING_DESC
    )
    table_name: str = Field(
        ...,
        description="Name of the table to get schema information for"
    )
    schema_name: str = Field(
        "public",
        alias="schema",
        description="Schema name (defaults to 'public')"
    )
    
    model_config = {"populate_by_name": True}


class ExecuteQueryRequest(BaseModel):
    """Request model for executing SQL queries."""
    connection_string: str = Field(
        ...,
        description=CONNECTION_STRING_DESC
    )
    query: str = Field(
        ...,
        description="SQL query to execute (read-only queries recommended)"
    )
    limit: Optional[int] = Field(
        1000,
        description="Maximum number of rows to return (safety limit)"
    )


# ============================================================================
# MCP Tool Definitions
# ============================================================================

@mcp.tool()
async def get_connection_status() -> str:
    """
    Check the MCP server status and connection configuration guidance.
    
    Returns information about how to configure your database connection.
    
    For SSE/HTTP mode (Kubernetes deployment), you should configure 
    POSTGRES_CONNECTION_STRING in your mcp.json env block. The AI will 
    automatically use this value for all database operations.
    
    This is a diagnostic tool - use it to verify the server is running.
    """
    import json
    return json.dumps({
        "server_status": "running",
        "mode": "multi-tenant",
        "configuration_guide": {
            "step_1": "Add POSTGRES_CONNECTION_STRING to your mcp.json env block",
            "step_2": "Format: postgresql://user:password@host:port/database",
            "step_3": "The AI will automatically use this value for all tools"
        },
        "example_config": {
            "mcpServers": {
                "stardom-postgres": {
                    "url": "https://stardom-pgsql-mcp-dev.maersk-digital.net/sse",
                    "env": {
                        "POSTGRES_CONNECTION_STRING": "postgresql://user:password@host:5432/database"
                    }
                }
            }
        }
    }, indent=2)


@mcp.tool()
async def get_tables(req: GetTablesRequest) -> str:
    """
    Fetch and return a list of all table names in the PostgreSQL database.
    
    This tool retrieves comprehensive information about tables including:
    - Table name and schema
    - Table type (BASE TABLE or VIEW)
    - Column count
    - Primary key columns
    - Table size
    
    IMPORTANT: For connection_string, use the POSTGRES_CONNECTION_STRING value from the 
    mcp.json env configuration. The AI should automatically use this value.
    
    Returns structured JSON with success status, data, and error information.
    """
    db_manager = None
    try:
        # Create per-client database connection
        db_manager = PostgresConnectionManager(req.connection_string)
        pg_tools = PostgresTools(db_manager)
        
        result = await pg_tools.get_tables(
            schema=req.schema_name,
            include_views=req.include_views
        )
        
        # Convert to JSON string for MCP response
        import json
        return json.dumps(result, indent=2, default=str)
    
    except Exception as e:
        logger.error(f"Error in get_tables tool: {str(e)}")
        import json
        return json.dumps({
            "success": False,
            "data": [],
            "count": 0,
            "error": str(e)
        }, indent=2)
    
    finally:
        if db_manager:
            await db_manager.close_pool()


@mcp.tool()
async def get_routines_and_functions(req: GetRoutinesRequest) -> str:
    """
    Retrieve all stored routines and functions from pg_catalog.pg_proc.
    
    This tool returns detailed information about database functions including:
    - Function name and schema
    - Arguments (parameter list)
    - Return type
    - Routine type (function, procedure, aggregate, window)
    - Volatility (immutable, stable, volatile)
    - Language (plpgsql, sql, etc.)
    - Complete function definition
    
    IMPORTANT: For connection_string, use the POSTGRES_CONNECTION_STRING value from the 
    mcp.json env configuration. The AI should automatically use this value.
    
    Returns structured JSON with success status, data, and error information.
    """
    db_manager = None
    try:
        # Create per-client database connection
        db_manager = PostgresConnectionManager(req.connection_string)
        pg_tools = PostgresTools(db_manager)
        
        result = await pg_tools.get_routines_and_functions(
            schema=req.schema_name,
            function_name_pattern=req.function_name_pattern
        )
        
        import json
        return json.dumps(result, indent=2, default=str)
    
    except Exception as e:
        logger.error(f"Error in get_routines_and_functions tool: {str(e)}")
        import json
        return json.dumps({
            "success": False,
            "data": [],
            "count": 0,
            "error": str(e)
        }, indent=2)
    
    finally:
        if db_manager:
            await db_manager.close_pool()


class GetDatabaseSchemaSummaryRequest(BaseModel):
    """Request model for getting database schema summary."""
    connection_string: str = Field(
        ...,
        description=CONNECTION_STRING_DESC
    )


@mcp.tool()
async def get_database_schema_summary(req: GetDatabaseSchemaSummaryRequest) -> str:
    """
    Get a comprehensive summary of the entire database schema.
    
    This is the most useful tool for understanding the database structure.
    It returns:
    - All tables with their metadata
    - Detailed schema for each table (columns, types, constraints)
    - All functions and stored procedures
    - Database summary statistics
    
    Use this tool first when you need to understand what data is available
    and how tables relate to each other. The AI client can then use this
    context to generate appropriate SQL queries.
    
    IMPORTANT: For connection_string, use the POSTGRES_CONNECTION_STRING value from the 
    mcp.json env configuration. The AI should automatically use this value.
    
    Returns structured JSON with complete database schema information.
    """
    db_manager = None
    try:
        # Create per-client database connection
        db_manager = PostgresConnectionManager(req.connection_string)
        pg_tools = PostgresTools(db_manager)
        
        result = await pg_tools.get_database_schema_summary()
        
        import json
        return json.dumps(result, indent=2, default=str)
    
    except Exception as e:
        logger.error(f"Error in get_database_schema_summary tool: {str(e)}")
        import json
        return json.dumps({
            "success": False,
            "data": {},
            "error": str(e)
        }, indent=2)
    
    finally:
        if db_manager:
            await db_manager.close_pool()


@mcp.tool()
async def get_table_schema(req: GetTableSchemaRequest) -> str:
    """
    Get detailed schema information for a specific table.
    
    This tool provides comprehensive schema details including:
    - Column definitions (name, type, nullable, default, etc.)
    - Constraints (primary key, foreign key, unique, check)
    - Indexes (name, type, columns, uniqueness)
    
    Useful for understanding table structure before writing queries.
    
    IMPORTANT: For connection_string, use the POSTGRES_CONNECTION_STRING value from the 
    mcp.json env configuration. The AI should automatically use this value.
    
    Returns structured JSON with success status, data, and error information.
    """
    db_manager = None
    try:
        # Create per-client database connection
        db_manager = PostgresConnectionManager(req.connection_string)
        pg_tools = PostgresTools(db_manager)
        
        result = await pg_tools.get_table_schema(
            table_name=req.table_name,
            schema=req.schema_name
        )
        
        import json
        return json.dumps(result, indent=2, default=str)
    
    except Exception as e:
        logger.error(f"Error in get_table_schema tool: {str(e)}")
        import json
        return json.dumps({
            "success": False,
            "data": {},
            "error": str(e)
        }, indent=2)
    
    finally:
        if db_manager:
            await db_manager.close_pool()


@mcp.tool()
async def execute_query(req: ExecuteQueryRequest) -> str:
    """
    Execute a SQL query and return results.
    
    This tool allows direct SQL query execution with safety features:
    - Automatic LIMIT clause for SELECT queries (if not present)
    - Blocks destructive operations (DROP, DELETE, UPDATE, etc.)
    - Returns structured results with row count
    
    The AI client should:
    1. First use get_database_schema_summary or get_table_schema to understand the database
    2. Generate the appropriate SQL query based on the user's request
    3. Use this tool to execute the query and get results
    
    IMPORTANT: For connection_string, use the POSTGRES_CONNECTION_STRING value from the 
    mcp.json env configuration. The AI should automatically use this value.
    
    Returns structured JSON with:
    - success: bool
    - data: Query results
    - row_count: Number of rows
    - error: Optional error message
    """
    db_manager = None
    try:
        # Create per-client database connection
        db_manager = PostgresConnectionManager(req.connection_string)
        pg_tools = PostgresTools(db_manager)
        
        result = await pg_tools.execute_query(
            query=req.query,
            limit=req.limit
        )
        
        import json
        return json.dumps(result, indent=2, default=str)
    
    except Exception as e:
        logger.error(f"Error in execute_query tool: {str(e)}")
        import json
        return json.dumps({
            "success": False,
            "data": [],
            "row_count": 0,
            "error": str(e)
        }, indent=2)
    
    finally:
        if db_manager:
            await db_manager.close_pool()


# ============================================================================
# Server Entry Point
# ============================================================================

if __name__ == "__main__":
    import sys
    import os
    
    logger.info("Starting Stardom PostgreSQL MCP Server (Multi-Tenant Mode)...")
    logger.info("Users will provide their own database connection strings")
    
    # Support both stdio and HTTP transports
    # Use HTTP if --http flag is provided, otherwise use stdio
    transport = "sse" if "--http" in sys.argv else "stdio"
    
    if transport == "sse":
        logger.info(f"Running in HTTP mode on http://{app_settings.mcp_server_host}:{app_settings.mcp_server_port}")
        logger.info(f"MCP endpoint: http://{app_settings.mcp_server_host}:{app_settings.mcp_server_port}/sse")
        
        # Monkey patch uvicorn.Config to force host/port binding
        import uvicorn
        original_config_init = uvicorn.Config.__init__
        
        def patched_config_init(self, *args, **kwargs):
            # Force host and port regardless of what was passed
            kwargs['host'] = app_settings.mcp_server_host
            kwargs['port'] = app_settings.mcp_server_port
            return original_config_init(self, *args, **kwargs)
        
        uvicorn.Config.__init__ = patched_config_init
        
        # Monkey patch TransportSecurityMiddleware to disable DNS rebinding protection
        # This is required for Kubernetes deployments where requests come through ingress
        # with external Host headers (e.g., stardom-pgsql-mcp-dev.maersk-digital.net)
        from mcp.server.transport_security import TransportSecurityMiddleware, TransportSecuritySettings
        original_middleware_init = TransportSecurityMiddleware.__init__
        
        def patched_middleware_init(self, settings=None):
            # Always disable DNS rebinding protection for reverse proxy deployments
            disabled_settings = TransportSecuritySettings(enable_dns_rebinding_protection=False)
            return original_middleware_init(self, disabled_settings)
        
        TransportSecurityMiddleware.__init__ = patched_middleware_init
        logger.info("DNS rebinding protection disabled for reverse proxy deployment")
        
        mcp.run(transport=transport)
    else:
        logger.info("Running in stdio mode (for direct MCP client integration)")
        mcp.run(transport=transport)
        