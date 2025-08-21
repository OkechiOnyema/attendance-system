#!/usr/bin/env python3
"""
Simple Database Connection Test
Run this to check if your Supabase connection works
"""

import os
import sys

def test_simple_connection():
    """Test basic database connection"""
    print("🔍 Testing basic database connection...")
    
    # Your connection string (replace with your actual password)
    connection_string = "postgresql://postgres:Oke389ony5131!!@db.NEWPROJECTREF.supabase.co:5432/postgres"
    
    try:
        # Test if we can import required modules
        print("📦 Checking dependencies...")
        import dj_database_url
        print("✅ dj-database-url imported successfully")
        
        import psycopg2
        print("✅ psycopg2 imported successfully")
        
        # Test URL parsing
        print("🔗 Parsing connection string...")
        db_config = dj_database_url.parse(connection_string)
        print("✅ Connection string parsed successfully")
        
        # Test actual connection
        print("🔌 Testing database connection...")
        conn = psycopg2.connect(
            host=db_config['HOST'],
            port=db_config['PORT'],
            database=db_config['NAME'],
            user=db_config['USER'],
            password=db_config['PASSWORD'],
            sslmode='require'
        )
        
        print("✅ Database connection successful!")
        
        # Test a simple query
        cursor = conn.cursor()
        cursor.execute("SELECT 1;")
        result = cursor.fetchone()
        print(f"✅ Test query successful: {result}")
        
        cursor.close()
        conn.close()
        
        print("\n🎉 All tests passed!")
        print("Your connection string is working correctly.")
        
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Install with: pip install psycopg2-binary dj-database-url")
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\n🔧 Troubleshooting tips:")
        print("1. Check if your password is correct")
        print("2. Make sure Supabase project is active")
        print("3. Verify the connection string format")
        print("4. Check if your IP is allowed (if restrictions set)")

if __name__ == "__main__":
    print("🚀 Simple Database Connection Test")
    print("=" * 40)
    print("\n⚠️  IMPORTANT: Replace 'YOUR_PASSWORD_HERE' with your actual password!")
    print("   Edit line 20 in this script before running.\n")
    
    test_simple_connection()
