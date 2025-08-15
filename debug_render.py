#!/usr/bin/env python
"""
Debug script for Render deployment issues
"""
import os

def debug_render():
    print("🔍 Debugging Render Environment...")
    print("=" * 60)
    
    # Check all environment variables
    print("📋 All Environment Variables:")
    for key, value in os.environ.items():
        if 'DATABASE' in key or 'DEBUG' in key or 'SECRET' in key:
            if 'SECRET' in key and value != 'Not set':
                print(f"   {key}: {'Set (hidden)'}")
            else:
                print(f"   {key}: {value}")
    
    print("\n🔑 Key Variables Check:")
    
    # Check DEBUG
    debug = os.environ.get('DEBUG', 'Not set')
    print(f"   DEBUG: {debug}")
    
    # Check SECRET_KEY
    secret_key = os.environ.get('SECRET_KEY', 'Not set')
    print(f"   SECRET_KEY: {'Set' if secret_key != 'Not set' else 'Not set'}")
    
    # Check DATABASE_URL
    database_url = os.environ.get('DATABASE_URL', 'Not set')
    print(f"   DATABASE_URL: {'Set' if database_url != 'Not set' else 'Not set'}")
    
    # Check if we're in production
    if debug == 'False' and secret_key != 'Not set':
        print("\n✅ Production environment detected!")
        if database_url != 'Not set':
            print("✅ Database URL is set!")
            print("🚀 Should work with PostgreSQL")
        else:
            print("❌ Database URL is missing!")
            print("⚠️ Will fall back to SQLite")
    else:
        print("\n⚠️ Not in production mode")
        print("   - DEBUG should be 'False'")
        print("   - SECRET_KEY should be set")
    
    print("=" * 60)

if __name__ == "__main__":
    debug_render()
