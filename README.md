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
- Python 3.10 or higher
- PostgreSQL database
- Poetry (for dependency management)

### Setup

1. **Clone the repository:**
```bash
git clone <your-repo-url>
cd pgsql-mcp-server
```

2. **Install dependencies:**
```bash
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

**That's it!** No API keys needed - your AI client handles the rest.

## 🎯 Usage

### Running the Server Standalone

```bash
poetry run python mcp_server.py
```

The server will start on `http://localhost:8000` by default.

## 🔌 Client Integration

### Cursor IDE Setup

1. **Open Cursor Settings** (Cmd/Ctrl + Shift + P → "Cursor Settings")

2. **Find the MCP section** and add this configuration:

**Method 1 - Local execution (recommended):**

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

**Method 2 - HTTP transport (for remote servers):**

First, start the server:
```bash
poetry run python mcp_server.py
```

Then configure in Cursor:
```json
{
  "mcpServers": {
    "postgres": {
      "url": "http://localhost:8000/mcp",
      "transport": "streamable_http"
    }
  }
}
```

3. **Restart Cursor**

4. **Test the integration:**
   
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

1. **Create or edit `.vscode/settings.json` in your project:**

```json
{
  "mcp.servers": {
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

2. **Reload VS Code**

3. **Use Copilot Chat** to query your database in natural language

### Claude Desktop Setup

1. **Edit Claude Desktop configuration:**

On macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

On Windows: `%APPDATA%\Claude\claude_desktop_config.json`

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

2. **Restart Claude Desktop**

### Using with LangGraph Agents

You can also use this server programmatically:

```python
import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

async def main():
    # Connect to the MCP server
    client = MultiServerMCPClient({
        "postgres": {
            "url": "http://localhost:8000/mcp",
            "transport": "streamable_http",
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

**Problem**: "Failed to initialize database pool"

**Solution**:
- Verify your database credentials
- Check if PostgreSQL is running
- Ensure the host/port are accessible
- Test connection string manually:
  ```bash
  psql "postgresql://user:password@host:port/database"
  ```

### MCP Client Not Finding Tools

**Problem**: Client says "No tools available"

**Solution**:
- Check the server is running
- Verify the path in MCP configuration is absolute
- Check environment variables are set correctly
- Look at the server logs for errors
- Restart the MCP client

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
