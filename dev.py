#!/usr/bin/env python
"""
Local development server
Run this for local testing before pushing to Vercel
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the Flask app from simple_api
from simple_api import app

if __name__ == '__main__':
    print("🚀 Starting Z-News local development server...")
    print("📡 API endpoints available:")
    print("   GET  /daily-summary")
    print("   GET  /healthcheck") 
    print("   GET  /status")
    print("\n💡 Test with:")
    print("   curl http://localhost:5000/daily-summary")
    print("   curl http://localhost:5000/healthcheck")
    print("\n🔧 Environment:")
    print(f"   NewsAPI Key: {'✅ Set' if os.getenv('NEWSAPI_API_KEY') else '❌ Missing'}")
    print(f"   Anthropic Key: {'✅ Set' if os.getenv('ANTHROPIC_API_KEY') else '❌ Missing'}")
    print()
    
    app.run(
        debug=True,
        host='0.0.0.0',
        port=5000
    )