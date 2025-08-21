#!/usr/bin/env python3
"""
Test Supabase Connection String
Run this locally to validate your connection string before deploying to Render
"""

import os
import sys
from urllib.parse import urlparse

def test_connection_string(connection_string):
    """Test if the connection string is valid"""
    print("🔍 Testing connection string format...")
    
    try:
        # Parse the URL
        parsed = urlparse(connection_string)
        
        print(f"✅ URL parsed successfully!")
        print(f"   Scheme: {parsed.scheme}")
        print(f"   Username: {parsed.username}")
        print(f"   Password: {'*' * len(parsed.password) if parsed.password else 'None'}")
        print(f"   Hostname: {parsed.hostname}")
        print(f"   Port: {parsed.port}")
        print(f"   Database: {parsed.path.lstrip('/')}")
        
        # Check if it's a valid PostgreSQL URL
        if parsed.scheme != 'postgresql':
            print("❌ Error: Scheme must be 'postgresql'")
            return False
            
        if not parsed.hostname:
            print("❌ Error: Hostname is missing")
            return False
            
        if not parsed.username:
            print("❌ Error: Username is missing")
            return False
            
        if not parsed.password:
            print("❌ Error: Password is missing")
            return False
            
        if not parsed.path or parsed.path == '/':
            print("❌ Error: Database name is missing")
            return False
            
        # Check if it's a Supabase URL
        if 'supabase.co' not in parsed.hostname:
            print("⚠️  Warning: This doesn't look like a Supabase URL")
            print("   Expected: db.xxxxx.supabase.co")
            print(f"   Got: {parsed.hostname}")
            
        print("✅ Connection string format is valid!")
        return True
        
    except Exception as e:
        print(f"❌ Error parsing URL: {e}")
        return False

def test_database_connection(connection_string):
    """Test actual database connection"""
    print("\n🔌 Testing database connection...")
    
    try:
        import dj_database_url
        import psycopg2
        
        # Parse the connection string
        db_config = dj_database_url.parse(connection_string)
        
        print("✅ Connection string parsed by dj-database-url")
        print(f"   Host: {db_config['HOST']}")
        print(f"   Port: {db_config['PORT']}")
        print(f"   Database: {db_config['NAME']}")
        print(f"   User: {db_config['USER']}")
        
        # Test actual connection
        import psycopg2
        conn = psycopg2.connect(
            host=db_config['HOST'],
            port=db_config['PORT'],
            database=db_config['NAME'],
            user=db_config['USER'],
            password=db_config['PASSWORD'],
            sslmode='require'  # Supabase requires SSL
        )
        
        print("✅ Database connection successful!")
        
        # Test a simple query
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ PostgreSQL version: {version[0]}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("   Install with: pip install psycopg2-binary dj-database-url")
        return False
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def main():
    print("🚀 Supabase Connection String Validator")
    print("=" * 50)
    
    # Get connection string from user
    if len(sys.argv) > 1:
        connection_string = sys.argv[1]
    else:
        connection_string = input("Enter your Supabase connection string: ").strip()
    
    if not connection_string:
        print("❌ No connection string provided")
        return
    
    print(f"\n📝 Testing: {connection_string[:50]}...")
    
    # Test format
    if not test_connection_string(connection_string):
        print("\n❌ Connection string format is invalid!")
        print("Please check your Supabase connection string")
        return
    
    # Test connection
    if test_database_connection(connection_string):
        print("\n🎉 All tests passed! Your connection string is ready for Render!")
        print("\nNext steps:")
        print("1. Copy this connection string")
        print("2. Go to Render dashboard")
        print("3. Update DATABASE_URL environment variable")
        print("4. Redeploy your service")
    else:
        print("\n❌ Connection test failed!")
        print("Please check your Supabase credentials and try again")

if __name__ == "__main__":
    main()
