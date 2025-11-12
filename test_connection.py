#!/usr/bin/env python3
"""
Test PostgreSQL database connection

This script verifies your database connection string is configured correctly.
Run this before setting up your MCP client to ensure everything works.

Usage:
    poetry run python test_connection.py
"""
import asyncio
from db_connection import PostgresConnectionManager
from config import app_settings

async def test_connection():
    """Test the database connection"""
    
    # Get connection string
    conn_str = app_settings.postgres_connection_string
    
    if not conn_str:
        print("[ERROR] POSTGRES_CONNECTION_STRING not configured")
        print("\nPlease set it in your .env file:")
        print("POSTGRES_CONNECTION_STRING=postgresql://user:password@host:port/database")
        return False
    
    # Mask password for display
    if '@' in conn_str:
        before_at = conn_str.split('@')[0]
        after_at = conn_str.split('@', 1)[1]
        if '://' in before_at and ':' in before_at.split('://', 1)[1]:
            protocol = before_at.split('://')[0]
            creds = before_at.split('://', 1)[1]
            if ':' in creds:
                username = creds.split(':')[0]
                masked = f"{protocol}://{username}:****@{after_at}"
        else:
            masked = conn_str[:20] + "****"
    else:
        masked = conn_str[:20] + "****"
    
    print(f"Testing connection to: {masked}")
    print()
    
    # Create connection manager
    db_manager = PostgresConnectionManager(conn_str)
    
    try:
        # Try to connect and run a simple query
        print("Connecting to database...")
        result = await db_manager.fetchrow("SELECT version() as version, current_database() as database")
        
        print("[OK] Connected successfully!")
        print()
        print(f"Database: {result['database']}")
        print(f"Version: {result['version']}")
        print()
        
        # Test getting tables
        print("Testing table listing...")
        tables = await db_manager.fetch("""
            SELECT schemaname, tablename 
            FROM pg_tables 
            WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
            ORDER BY schemaname, tablename
            LIMIT 5
        """)
        
        if tables:
            print(f"[OK] Found {len(tables)} tables (showing first 5):")
            for table in tables:
                print(f"  - {table['schemaname']}.{table['tablename']}")
        else:
            print("[INFO] No user tables found in database")
        
        print()
        print("[SUCCESS] All connection tests passed!")
        print()
        print("You're ready to run: poetry run python mcp_server.py")
        return True
        
    except Exception as e:
        print(f"[ERROR] Connection failed: {str(e)}")
        print()
        print("Troubleshooting tips:")
        print("1. Check connection string format: postgresql://user:password@host:port/database")
        print("2. URL-encode special characters in password (e.g., # -> %23)")
        print("3. Verify database host is reachable")
        print("4. Confirm username/password are correct")
        print("5. For Azure PostgreSQL, add ?sslmode=require at the end")
        return False
        
    finally:
        await db_manager.close_pool()

if __name__ == "__main__":
    success = asyncio.run(test_connection())
    exit(0 if success else 1)

