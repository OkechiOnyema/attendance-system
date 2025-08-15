#!/usr/bin/env python
"""
Database setup script for Render deployment
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Setup Django
django.setup()

from django.core.management import execute_from_command_line

def setup_database():
    print("🔧 Setting up database for Render deployment...")
    print("=" * 60)
    
    try:
        # Run migrations
        print("📊 Running database migrations...")
        execute_from_command_line(['manage.py', 'migrate', '--noinput'])
        print("✅ Migrations completed successfully!")
        
        # Create superuser
        print("👤 Creating superuser account...")
        from django.contrib.auth.models import User
        
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
            print("✅ Superuser 'admin' created successfully!")
        else:
            print("ℹ️ Superuser 'admin' already exists")
        
        # Check if tables exist
        print("🔍 Verifying database tables...")
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
        
        print(f"📋 Found {len(tables)} tables:")
        for table in tables:
            print(f"   - {table}")
        
        if 'auth_user' in tables:
            print("✅ auth_user table exists - database setup complete!")
        else:
            print("❌ auth_user table missing - setup failed!")
            
    except Exception as e:
        print(f"❌ Error during database setup: {e}")
        return False
    
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = setup_database()
    if success:
        print("🎉 Database setup completed successfully!")
    else:
        print("💥 Database setup failed!")
        sys.exit(1)
