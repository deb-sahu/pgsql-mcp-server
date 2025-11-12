"""
Generic PostgreSQL MCP Server

A reusable Model Context Protocol (MCP) server for PostgreSQL databases.
This server provides tools for querying, exploring, and analyzing PostgreSQL databases
through a standardized MCP interface.

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

# Initialize database manager and tools
# Connection string can be provided via environment variable or MCP client configuration
DB_CONNECTION_STRING = os.getenv(
    "POSTGRES_CONNECTION_STRING",
    os.getenv("DATABASE_URL", "")
)

# If connection string is not in URL format, build it from components
if not DB_CONNECTION_STRING or not DB_CONNECTION_STRING.startswith("postgresql://"):
    DB_CONNECTION_STRING = (
        f"postgresql://{app_settings.db_user_name}:{app_settings.db_password}"
        f"@{app_settings.db_host}:{app_settings.db_port}/{app_settings.db_name}"
    )

db_manager = PostgresConnectionManager(DB_CONNECTION_STRING)
pg_tools = PostgresTools(db_manager)


# ============================================================================
# MCP Tool Request Models
# ============================================================================

class GetTablesRequest(BaseModel):
    """Request model for getting database tables."""
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
async def get_tables(req: GetTablesRequest) -> str:
    """
    Fetch and return a list of all table names in the PostgreSQL database.
    
    This tool retrieves comprehensive information about tables including:
    - Table name and schema
    - Table type (BASE TABLE or VIEW)
    - Column count
    - Primary key columns
    - Table size
    
    Returns structured JSON with success status, data, and error information.
    """
    try:
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
    
    Returns structured JSON with success status, data, and error information.
    """
    try:
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


@mcp.tool()
async def get_database_schema_summary() -> str:
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
    
    Returns structured JSON with complete database schema information.
    """
    try:
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


@mcp.tool()
async def get_table_schema(req: GetTableSchemaRequest) -> str:
    """
    Get detailed schema information for a specific table.
    
    This tool provides comprehensive schema details including:
    - Column definitions (name, type, nullable, default, etc.)
    - Constraints (primary key, foreign key, unique, check)
    - Indexes (name, type, columns, uniqueness)
    
    Useful for understanding table structure before writing queries.
    
    Returns structured JSON with success status, data, and error information.
    """
    try:
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
    
    Returns structured JSON with:
    - success: bool
    - data: Query results
    - row_count: Number of rows
    - error: Optional error message
    """
    try:
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


# ============================================================================
# Server Entry Point
# ============================================================================

if __name__ == "__main__":
    import sys
    
    logger.info("Starting PostgreSQL MCP Server...")
    logger.info(f"Connection target: {DB_CONNECTION_STRING.split('@')[1] if '@' in DB_CONNECTION_STRING else 'configured'}")
    
    # Support both stdio and HTTP transports
    # Use HTTP if --http flag is provided, otherwise use stdio
    transport = "sse" if "--http" in sys.argv else "stdio"
    
    if transport == "sse":
        logger.info("Running in HTTP mode on http://localhost:8000")
        logger.info("MCP endpoint: http://localhost:8000/sse")
    else:
        logger.info("Running in stdio mode (for direct MCP client integration)")
    
    # Run the MCP server - FastMCP handles its own lifecycle
    # Database connection pool will be initialized on first use
    mcp.run(transport=transport)

