# Quick Start Guide

Get your PostgreSQL MCP server up and running in 5 minutes!

## 1. Install Dependencies

```bash
poetry install
```

## 2. Configure Database Connection

Create a `.env` file:

```bash
cp env.example .env
```

Edit `.env` and add your database connection:

```env
# Simple connection string (recommended)
POSTGRES_CONNECTION_STRING=postgresql://user:password@host:port/database

# OR individual parameters
DB_USER_NAME=your_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_database
```

## 3. Test the Server

```bash
poetry run python mcp_server.py
```

You should see:
```
PostgreSQL MCP Server started successfully
Connected to database: host:port
```

Press Ctrl+C to stop.

## 4. Configure in Cursor

1. Open Cursor Settings (Cmd/Ctrl + Shift + P → "Cursor Settings")
2. Find MCP section and add:

```json
{
  "mcpServers": {
    "postgres": {
      "command": "poetry",
      "args": ["run", "python", "mcp_server.py"],
      "cwd": "/absolute/path/to/pgsql-mcp-server",
      "env": {
        "POSTGRES_CONNECTION_STRING": "postgresql://user:password@host:port/database"
      }
    }
  }
}
```

**Important**: Replace `/absolute/path/to/pgsql-mcp-server` with the actual full path to this folder.

3. Restart Cursor

## 5. Try It Out!

Open Cursor's AI chat and ask:

- "Show me all tables in the database"
- "What's the schema of the users table?"
- "Get all records from users created in the last 30 days"

The AI will automatically use the MCP tools to:
1. Understand your database structure
2. Generate the right SQL query
3. Execute it and show you the results

## Available Tools

Your AI client now has access to 5 database tools:

1. **get_database_schema_summary** - Get complete database overview
2. **get_tables** - List all tables with metadata
3. **get_table_schema** - Get detailed schema for a specific table
4. **get_routines_and_functions** - List stored procedures and functions
5. **execute_query** - Run SQL queries (read-only)

## Troubleshooting

**"Failed to initialize database pool"**
- Check your database credentials in `.env`
- Make sure PostgreSQL is running
- Test connection: `psql "your_connection_string"`

**"No tools available"**
- Verify the `cwd` path is absolute (not relative)
- Check environment variables are set
- Restart Cursor

**Need Help?**
- Read the full README.md for detailed docs
- Check the server logs for error messages

---

That's it! You're ready to query your database with natural language 🚀

