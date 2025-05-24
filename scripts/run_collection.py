#!/usr/bin/env python
"""
Local news collection script
Use this to collect fresh news data and generate summaries locally
"""

import os
import sys
import subprocess
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_collection():
    """Run the full news collection and summary pipeline"""
    
    print("🗞️  Z-News Local Collection Pipeline")
    print("=" * 50)
    
    try:
        # Step 1: Collect news
        print("\n📰 Step 1: Collecting news for clients...")
        result = subprocess.run([
            'python', 'collect_all_news.py', '--target', 'clients'
        ], capture_output=True, text=True, cwd='..')
        
        if result.returncode != 0:
            print(f"❌ Collection failed: {result.stderr}")
            return False
        
        print("✅ News collection completed")
        
        # Step 2: Generate summary
        print("\n🤖 Step 2: Generating AI summary...")
        result = subprocess.run([
            'python', 'generate_daily_summary.py'
        ], capture_output=True, text=True, cwd='..')
        
        if result.returncode != 0:
            print(f"❌ Summary generation failed: {result.stderr}")
            return False
            
        print("✅ Summary generation completed")
        
        # Step 3: Test API
        print("\n🧪 Step 3: Testing API endpoints...")
        result = subprocess.run([
            'curl', '-s', 'http://localhost:5000/daily-summary'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ API test successful")
        else:
            print("⚠️  API test failed (server may not be running)")
        
        print(f"\n🎉 Pipeline completed at {datetime.now()}")
        print("📁 Check the data/ directory for generated files")
        print("🚀 Start local server with: python dev.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        return False

if __name__ == '__main__':
    run_collection()