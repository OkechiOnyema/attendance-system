#!/usr/bin/env python3
"""
PythonAnywhere Deployment Helper Script
This script helps prepare your Django project for PythonAnywhere deployment.
"""

import os
import shutil
import zipfile
from pathlib import Path

def create_deployment_package():
    """Create a deployment package for PythonAnywhere"""
    print("🚀 Creating PythonAnywhere deployment package...")
    
    # Project root directory
    project_root = Path(__file__).parent
    
    # Files to exclude from deployment
    exclude_patterns = [
        '__pycache__',
        '*.pyc',
        '.venv',
        'venv',
        '.git',
        '.vscode',
        '.idea',
        '*.log',
        'db.sqlite3',
        'media',
        'static',
        'deploy_to_pythonanywhere.py',
        'setup_esp32.py',
        'test_esp32_integration.py',
        'attendance-system-deployment.zip'  # Don't include the old zip
    ]
    
    # Create deployment directory
    deploy_dir = project_root / 'deployment_package'
    if deploy_dir.exists():
        shutil.rmtree(deploy_dir)
    deploy_dir.mkdir()
    
    # Copy project files
    print("📁 Copying project files...")
    for item in project_root.iterdir():
        if item.name == 'deployment_package':
            continue
            
        # Check if item should be excluded
        should_exclude = False
        for pattern in exclude_patterns:
            if pattern in str(item) or item.name.endswith(pattern.replace('*', '')):
                should_exclude = True
                break
        
        if not should_exclude:
            if item.is_file():
                shutil.copy2(item, deploy_dir / item.name)
            elif item.is_dir():
                shutil.copytree(item, deploy_dir / item.name, ignore=shutil.ignore_patterns(*exclude_patterns))
    
    # Create zip file
    zip_path = project_root / 'attendance-system-deployment.zip'
    print(f"📦 Creating deployment zip: {zip_path}")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(deploy_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, deploy_dir)
                zipf.write(file_path, arcname)
    
    # Clean up deployment directory
    shutil.rmtree(deploy_dir)
    
    print(f"✅ Deployment package created: {zip_path}")
    print(f"📁 Package size: {zip_path.stat().st_size / 1024 / 1024:.2f} MB")
    
    return zip_path

def show_deployment_instructions():
    """Show deployment instructions"""
    print("\n" + "="*60)
    print("🚀 PYTHONANYWHERE DEPLOYMENT INSTRUCTIONS")
    print("="*60)
    
    print("\n📋 STEP-BY-STEP DEPLOYMENT:")
    print("1. Go to www.pythonanywhere.com")
    print("2. Create a Beginner account (free)")
    print("3. Go to Files tab")
    print("4. Upload the deployment zip file")
    print("5. Extract the zip file")
    print("6. Follow the detailed guide in PYTHONANYWHERE_DEPLOYMENT_STEPS.md")
    
    print("\n📁 FILES CREATED:")
    print("✅ requirements.txt - Python dependencies")
    print("✅ .gitignore - Clean deployment")
    print("✅ config/settings_production.py - Production settings")
    print("✅ PYTHONANYWHERE_DEPLOYMENT_STEPS.md - Detailed guide")
    print("✅ attendance-system-deployment.zip - Ready to upload")
    
    print("\n🔧 NEXT STEPS:")
    print("1. Upload the zip file to PythonAnywhere")
    print("2. Follow the deployment guide")
    print("3. Test your app on PythonAnywhere")
    print("4. Come back for ESP32 WiFi restriction setup")
    
    print("\n" + "="*60)

def main():
    """Main deployment process"""
    print("🎯 Attendance System - PythonAnywhere Deployment Helper")
    print("="*60)
    
    try:
        # Create deployment package
        zip_path = create_deployment_package()
        
        # Show instructions
        show_deployment_instructions()
        
        print(f"\n🎉 Ready for deployment!")
        print(f"📦 Upload this file to PythonAnywhere: {zip_path.name}")
        
    except Exception as e:
        print(f"❌ Error creating deployment package: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
