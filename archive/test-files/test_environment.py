#!/usr/bin/env python
"""
Test script to verify the environment setup in GitHub Actions
"""

import sys
import os
import json

def test_environment():
    """Test basic environment setup"""
    
    print("🧪 Testing GitHub Actions Environment")
    print("=" * 50)
    
    # Test Python basics
    print(f"✓ Python version: {sys.version}")
    print(f"✓ Current directory: {os.getcwd()}")
    
    # Test required modules
    modules_to_test = ['pandas', 'anthropic', 'json', 'datetime']
    for module in modules_to_test:
        try:
            __import__(module)
            print(f"✓ Module {module}: Available")
        except ImportError as e:
            print(f"❌ Module {module}: Missing - {e}")
    
    # Test API key
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if api_key:
        print(f"✓ ANTHROPIC_API_KEY: Configured ({len(api_key)} chars)")
    else:
        print("❌ ANTHROPIC_API_KEY: Not configured")
    
    # Test file structure
    files_to_check = [
        'collect_all_news.py',
        'generate_daily_summary.py',
        'create_test_json.py',
        'sample_data.csv',
        'config/clients.json',
        'config/competitors.json'
    ]
    
    for file in files_to_check:
        if os.path.exists(file):
            print(f"✓ File {file}: Exists")
        else:
            print(f"❌ File {file}: Missing")
    
    # Test config directory
    if os.path.exists('config'):
        config_files = os.listdir('config')
        print(f"✓ Config directory: {len(config_files)} files")
    else:
        print("❌ Config directory: Missing")
    
    print("\n🎯 Environment test complete!")
    return True

if __name__ == "__main__":
    test_environment()