# Quick Start Guide

Get your PostgreSQL MCP server up and running in 5 minutes!

> ### ⚠️ IMPORTANT: If you have Python 3.14, switch to 3.12 first
> ```bash
> poetry env use python3.12
> ```
> The `asyncpg` library doesn't support Python 3.14 yet.

## 1. Install Dependencies

**Required**: Python 3.10, 3.11, 3.12, or 3.13 (**NOT 3.14**)

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
# PostgreSQL URL format (recommended)
POSTGRES_CONNECTION_STRING=postgresql://user:password@host:port/database

# For Azure PostgreSQL with SSL
POSTGRES_CONNECTION_STRING=postgresql://user:password@server.postgres.database.azure.com:5432/database?sslmode=require
```

### ⚠️ Special Characters in Passwords

If your password has special characters, **URL-encode them**:

```env
# Password: pass#word123  →  pass%23word123
# Password: p@ss+word     →  p%40ss%2Bword

POSTGRES_CONNECTION_STRING=postgresql://user:pass%23word123@host:5432/db
```

Common encodings: `#` → `%23`, `@` → `%40`, `+` → `%2B`, `/` → `%2F`

## 3. Test the Connection

**Before configuring your client, test the connection:**

```bash
poetry run python test_connection.py
```

You should see:
```
Testing connection to: postgresql://user:****@host:5432/database

Connecting to database...
[OK] Connected successfully!

Database: your_database
Version: PostgreSQL 16.x on ...

[SUCCESS] All connection tests passed!
```

If you see errors, check:
- Connection string format (must be `postgresql://...`)
- Special characters are URL-encoded
- Database is accessible from your machine

## 4. Configure in Cursor

Edit `~/.cursor/mcp.json` (or create it if it doesn't exist):

```json
{
  "mcpServers": {
    "postgres": {
      "url": "http://localhost:8000/sse",
      "transport": "sse"
    }
  }
}
```

**That's it!** This simple configuration works reliably without path issues.

## 5. Start the Server

In a terminal, run:

```bash
cd /path/to/pgsql-mcp-server
poetry run python mcp_server.py --http
```

You should see:
```
INFO:__main__:Starting PostgreSQL MCP Server...
INFO:__main__:Running in HTTP mode on http://localhost:8000
INFO:__main__:MCP endpoint: http://localhost:8000/sse
```

**Keep this terminal open** - the server needs to keep running.

## 6. Restart Cursor

Restart Cursor to pick up the new MCP configuration.

## 7. Try It Out!

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

**"Failed to initialize database pool" or "invalid literal for int()"**
- **Wrong format**: Use `postgresql://user:password@host:port/db` NOT `.NET format`
- **Special characters**: URL-encode them (e.g., `#` → `%23`)
- **Test connection**: Run `poetry run python test_connection.py`
- **Verify manually**: `psql "postgresql://user:password@host:port/db"`

**"Python 3.14 is newer than PyO3's maximum supported version"**
- Use Python 3.12: `poetry env use python3.12 && poetry install`

**"No tools available"**
- Verify the `cwd` path is absolute (not relative)
- Check environment variables are set
- Restart Cursor

**Need Help?**
- Read the full README.md for detailed docs
- Check the server logs for error messages

---

That's it! You're ready to query your database with natural language 🚀

