# PostgreSQL MCP Server

A generic, reusable Model Context Protocol (MCP) server for PostgreSQL databases. This server provides intelligent database tools that can be used with any MCP-compatible AI client like Cursor, VS Code with GitHub Copilot, Claude Desktop, or any other MCP client.

## 🚀 Features

- **Generic & Reusable**: Works with any PostgreSQL database by simply configuring the connection string
- **Zero External Dependencies**: No OpenAI, Gemini, or other LLM API keys needed - uses the AI client's own intelligence
- **Natural Language Ready**: Provides schema context for AI clients to convert natural language to SQL
- **Comprehensive Tools**: 5 powerful MCP tools for database exploration and querying
- **Async Performance**: Built with asyncpg for high-performance async operations
- **Type-Safe**: Full type hints and Pydantic models for reliability
- **Well-Documented**: Clear docstrings and structured JSON responses

## 🧠 How It Works

This MCP server provides database context to your AI client (Cursor, VS Code, etc.). The AI client uses this context to:

1. **Understand your database** using `get_database_schema_summary`
2. **Generate SQL queries** from your natural language requests
3. **Execute queries** using `execute_query`
4. **Return formatted results** back to you

**You don't need separate API keys** - the AI client you're already using (Cursor, Claude, etc.) handles all the natural language processing!

## 📦 MCP Tools

### 1. `get_tables`
Fetch all tables in the database with comprehensive metadata:
- Table name and schema
- Table type (BASE TABLE or VIEW)
- Column count
- Primary key columns
- Table size

**Parameters:**
- `schema` (optional): Filter by schema name
- `include_views` (optional): Include views in results

### 2. `get_routines_and_functions`
Retrieve all stored procedures and functions:
- Function name and schema
- Arguments (parameter list)
- Return type
- Routine type (function, procedure, aggregate, window)
- Language (plpgsql, sql, etc.)
- Complete definition

**Parameters:**
- `schema` (optional): Filter by schema
- `function_name_pattern` (optional): SQL LIKE pattern for filtering

### 3. `get_database_schema_summary`
**The most useful tool** - get a complete overview of your database:
- All tables with metadata
- Detailed column information
- Constraints and relationships
- Functions and procedures
- Summary statistics

This provides all the context the AI needs to understand your database structure and generate appropriate queries.

**No parameters needed** - returns everything!

### 4. `get_table_schema`
Get detailed schema information for a specific table:
- Column definitions (name, type, nullable, default)
- Constraints (primary key, foreign key, unique, check)
- Indexes (name, type, columns, uniqueness)

**Parameters:**
- `table_name`: Name of the table
- `schema`: Schema name (default: "public")

### 5. `execute_query`
Execute a SQL query with safety features:
- Automatic LIMIT for SELECT queries
- Blocks destructive operations (DROP, DELETE, UPDATE)
- Returns structured results

**Parameters:**
- `query`: SQL query to execute
- `limit`: Max rows to return (default: 1000)

## 🛠️ Installation

### Prerequisites
- Python 3.10, 3.11, 3.12, or 3.13 (NOT 3.14 - dependencies not yet compatible)
- PostgreSQL database (local or cloud)
- Poetry (for dependency management)

### Setup

1. **Clone the repository:**
```bash
git clone <your-repo-url>
cd pgsql-mcp-server
```

2. **Install dependencies:**
```bash
# If you have Python 3.14, use Python 3.12 instead
poetry env use python3.12  # or python3.11, python3.10

poetry install
```

3. **Configure environment:**
```bash
cp env.example .env
# Edit .env with your database credentials
```

4. **Environment variables:**

**Option 1 - Individual parameters:**
```env
DB_USER_NAME=your_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_database
```

**Option 2 - Connection string (recommended):**
```env
POSTGRES_CONNECTION_STRING=postgresql://user:password@host:port/database
```

### ⚠️ Important: Connection String Format

The connection string must be in **PostgreSQL URL format**:

```
postgresql://username:password@host:port/database
```

#### For Azure PostgreSQL with SSL:
```env
POSTGRES_CONNECTION_STRING=postgresql://user:password@server.postgres.database.azure.com:5432/database?sslmode=require
```

#### Special Characters in Passwords

If your password contains special characters, you **must** URL-encode them:

| Character | Encoded | Character | Encoded |
|-----------|---------|-----------|---------|
| `#`       | `%23`   | `@`       | `%40`   |
| `%`       | `%25`   | `&`       | `%26`   |
| `+`       | `%2B`   | `/`       | `%2F`   |
| `?`       | `%3F`   | `=`       | `%3D`   |
| `:` (in pwd)| `%3A` | ` ` (space)| `%20`  |

**Example:**
```env
# Original password: qA5m#6fMk
# Encoded password:  qA5m%236fMk

POSTGRES_CONNECTION_STRING=postgresql://myuser:qA5m%236fMk@host:5432/mydb
```

### 5. Test Your Connection

Run the connection test to verify everything works:

```bash
poetry run python test_connection.py
```

**Expected output:**
```
Testing connection to: postgresql://user:****@host:5432/database

Connecting to database...
[OK] Connected successfully!

Database: your_database
Version: PostgreSQL 16.x on ...

Testing table listing...
[OK] Found 5 tables (showing first 5):
  - schema.table1
  - schema.table2
  ...

[SUCCESS] All connection tests passed!
```

**That's it!** No API keys needed - your AI client handles the rest.

## 🎯 Usage

### Running the Server

The server supports two transport modes:

**stdio mode (default)** - For direct MCP client integration:
```bash
poetry run python mcp_server.py
```

**HTTP mode** - For standalone server (recommended for development):
```bash
poetry run python mcp_server.py --http
```

The HTTP server will start on `http://localhost:8000` with the MCP endpoint at `http://localhost:8000/sse`.

## 🔌 Client Integration

### Cursor IDE Setup

You can configure Cursor to connect to the MCP server in two ways:

#### Recommended Method: HTTP Transport ✅

**Why this works best:**
- ✅ Simple configuration - no path issues
- ✅ Easy to debug - see all server logs
- ✅ Independent server - restart without restarting Cursor
- ✅ Works reliably across all systems

**Setup:**

1. **Edit your Cursor MCP configuration** (`~/.cursor/mcp.json`):

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

2. **Start the server in HTTP mode** (in a separate terminal):
```bash
cd /path/to/pgsql-mcp-server
poetry run python mcp_server.py --http
```

You should see:
```
INFO:__main__:Starting PostgreSQL MCP Server...
INFO:__main__:Connection target: your-host:5432/your-database
INFO:__main__:Running in HTTP mode on http://localhost:8000
INFO:__main__:MCP endpoint: http://localhost:8000/sse
```

3. **Restart Cursor**

4. **Keep the server running** - Don't close the terminal. You can see all logs in real-time.

---

#### Alternative: stdio Transport (Auto-Launch)

**Note:** This method can have path resolution issues on some systems. Use HTTP method above if you encounter problems.

1. **Edit your Cursor MCP configuration** (`~/.cursor/mcp.json`):

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

**Important:** Replace `/absolute/path/to/pgsql-mcp-server` with your actual path (e.g., `/Users/username/Projects/pgsql-mcp-server/pgsql-mcp-server`).

2. **Restart Cursor**

---

**Test the integration:**
   
Open Cursor's AI chat and try:
   
   - "Show me all tables in the database"
   - "What's the schema of the users table?"
   - "Get all users who registered in the last 30 days"
   - "Show me total sales by product category"

The AI will automatically:
- Call `get_database_schema_summary` to understand your database
- Generate the appropriate SQL query
- Execute it using `execute_query`
- Format and explain the results

### VS Code with GitHub Copilot Setup

1. **Start the MCP server** (in a separate terminal):
```bash
cd /path/to/pgsql-mcp-server
poetry run python mcp_server.py --http
```

2. **Create or edit `.vscode/settings.json` in your project:**

```json
{
  "mcp.servers": {
    "postgres": {
      "url": "http://localhost:8000/sse",
      "transport": "sse"
    }
  }
}
```

3. **Reload VS Code**

4. **Use Copilot Chat** to query your database in natural language

**Keep the server running** in the background to maintain the connection.

### Claude Desktop Setup

1. **Start the MCP server** (in a separate terminal):
```bash
cd /path/to/pgsql-mcp-server
poetry run python mcp_server.py --http
```

2. **Edit Claude Desktop configuration:**

On macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

On Windows: `%APPDATA%\Claude\claude_desktop_config.json`

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

3. **Restart Claude Desktop**

**Keep the server running** in the background - Claude will connect to it automatically.

### Using with LangGraph Agents

You can also use this server programmatically:

1. **Start the MCP server**:
```bash
poetry run python mcp_server.py --http
```

2. **Use in your Python code**:

```python
import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

async def main():
    # Connect to the MCP server (HTTP transport)
    client = MultiServerMCPClient({
        "postgres": {
            "url": "http://localhost:8000/sse",
            "transport": "sse",
        },
    })
    
    # Get tools from the server
    tools = await client.get_tools()
    
    # Create an agent with the tools
    llm = ChatOpenAI(model="gpt-4")
    agent = create_react_agent(model=llm, tools=tools)
    
    # Use the agent
    result = await agent.ainvoke({
        "messages": [{
            "role": "user",
            "content": "Show me all users who registered in the last 30 days"
        }]
    })
    
    print(result["messages"][-1].content)

asyncio.run(main())
```

## 📋 Example Queries

Once integrated with your MCP client, you can ask questions in plain English:

**Database Exploration:**
- "What tables are in the database?"
- "Show me the complete database schema"
- "What's the structure of the users table?"
- "List all stored procedures"

**Data Queries:**
- "Show me all customers who made purchases in the last 7 days"
- "Get the top 10 products by revenue with their category names"
- "Find all employees with their department and manager information"
- "What are the most recent orders with customer details?"
- "Count orders by status for each product category"

**Complex Joins:**
- "Show me users with their orders and order items"
- "Get customer lifetime value with total orders and total spent"
- "Find products that have never been ordered"

The AI will:
1. Analyze your question
2. Get the database schema using `get_database_schema_summary`
3. Generate appropriate SQL with JOINs if needed
4. Execute using `execute_query`
5. Format the results for you

## 🏗️ Project Structure

```
pgsql-mcp-server/
├── config.py                    # Configuration settings
├── mcp_server.py                # Main MCP server with all tools
├── db_connection.py             # PostgreSQL connection manager
├── pg_tools.py                  # Database tool implementations
├── env.example                  # Example environment configuration
├── pyproject.toml               # Poetry dependencies
├── poetry.lock                  # Locked dependencies
├── .gitignore                   # Git ignore rules
├── README.md                    # This file (comprehensive docs)
├── QUICKSTART.md                # Quick start guide (5 min setup)
├── PROJECT_SUMMARY.md           # Project overview
├── CHANGELOG.md                 # Version history & changes
├── CODE_OF_CONDUCT.md           # Community guidelines
├── LICENSE.md                   # MIT License
└── REVIEW.md                    # Code review & quality assessment
```

## 🔒 Security Considerations

1. **Read-Only by Default**: The `execute_query` tool blocks destructive operations (DROP, DELETE, UPDATE)
2. **Query Limits**: Automatic LIMIT clause added to SELECT queries (default: 1000 rows)
3. **Connection Pooling**: Uses asyncpg connection pooling for stability
4. **Environment Variables**: Keep credentials in environment variables, never in code
5. **No External APIs**: No data leaves your environment - everything stays local

## 🐛 Troubleshooting

### Connection Issues

**Problem**: "Failed to initialize database pool" or "invalid literal for int()"

**Solution**:
1. **Check connection string format** - Must be: `postgresql://user:password@host:port/database`
   - NOT .NET format with semicolons: `Host=...;Database=...`
   
2. **URL-encode special characters in password**:
   ```bash
   # Wrong: password with # character
   POSTGRES_CONNECTION_STRING=postgresql://user:pass#word@host:5432/db
   
   # Correct: # encoded as %23
   POSTGRES_CONNECTION_STRING=postgresql://user:pass%23word@host:5432/db
   ```

3. **Test the connection**:
   ```bash
   poetry run python test_connection.py
   ```

4. **Verify credentials manually**:
   ```bash
   psql "postgresql://user:password@host:port/database"
   ```

5. **For Azure PostgreSQL**, add `?sslmode=require`:
   ```env
   POSTGRES_CONNECTION_STRING=postgresql://user:password@server.postgres.database.azure.com:5432/db?sslmode=require
   ```

**Problem**: "Python 3.14 is newer than PyO3's maximum supported version"

**Solution**:
```bash
# Use Python 3.12 instead
poetry env use python3.12
poetry install
```

### MCP Client Not Finding Tools

**Problem**: Client says "No tools available"

**Solution**:

**For HTTP transport:**
- Make sure server is running: `poetry run python mcp_server.py --http`
- Check the URL in mcp.json: `http://localhost:8000/sse`
- Verify the server is accessible: Open `http://localhost:8000/sse` in browser
- Check server logs for errors

**For stdio transport:**
- Verify the `cwd` path in mcp.json is absolute (not relative)
- Check environment variables are set correctly in mcp.json
- Look at Cursor's logs for server startup errors

**Both:**
- Restart the MCP client (Cursor/VS Code)
- Test connection: `poetry run python test_connection.py`

### Queries Not Working

**Problem**: "Error executing query"

**Solution**:
- Ask the AI to show you the generated SQL
- Verify table/column names are correct
- Check you have read permissions on the tables
- Try a simpler query first (e.g., "show all tables")

## 💡 Tips

1. **Start with schema exploration**: Ask "What's in the database?" before running complex queries
2. **Be specific**: Instead of "show users", try "show all users with their email and registration date"
3. **Review generated SQL**: Ask the AI to show you the SQL it generated
4. **Use natural language**: You don't need to know SQL - just describe what you want

## 🤝 Contributing

Contributions are welcome! Please:

1. Read our [Code of Conduct](CODE_OF_CONDUCT.md)
2. Fork the repository
3. Create a feature branch
4. Make your changes
5. Submit a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

## 🙏 Acknowledgments

Built with:
- [FastMCP](https://github.com/modelcontextprotocol/fastmcp) - MCP server framework
- [asyncpg](https://github.com/MagicStack/asyncpg) - Fast PostgreSQL driver
- [Pydantic](https://github.com/pydantic/pydantic) - Data validation

---

**Query your PostgreSQL database with natural language through your AI client!** 🚀
