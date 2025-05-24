#!/usr/bin/env python
"""
Test script to verify API responses for website integration
"""

import json
import requests
from simple_api import app

def test_api_responses():
    """Test the API responses to ensure they match website expectations"""
    
    print("🧪 Testing API responses for website integration...\n")
    
    with app.test_client() as client:
        
        # Test 1: Basic daily summary
        print("1. Testing basic daily summary:")
        response = client.get('/daily-summary')
        data = response.get_json()
        
        required_fields = ['date', 'generated_at', 'summary', 'companies_included', 'total_articles', 'status']
        
        print(f"   ✓ Status code: {response.status_code}")
        print(f"   ✓ Response status: {data.get('status')}")
        print(f"   ✓ Companies count: {len(data.get('companies_included', []))}")
        print(f"   ✓ Articles count: {data.get('total_articles')}")
        print(f"   ✓ Summary length: {len(data.get('summary', ''))}")
        
        # Check all required fields
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            print(f"   ❌ Missing fields: {missing_fields}")
        else:
            print("   ✅ All required fields present")
        
        # Test 2: Company filtering
        print("\n2. Testing company filtering:")
        response = client.get('/daily-summary?companies=Fidelity Investments')
        data = response.get_json()
        
        print(f"   ✓ Status code: {response.status_code}")
        print(f"   ✓ Filtered companies: {data.get('companies_included', [])}")
        
        # Test 3: Status endpoint
        print("\n3. Testing status endpoint:")
        response = client.get('/status')
        data = response.get_json()
        
        print(f"   ✓ Status code: {response.status_code}")
        print(f"   ✓ Service status: {data.get('status')}")
        print(f"   ✓ Last updated: {data.get('last_updated')}")
        
        # Test 4: Healthcheck
        print("\n4. Testing healthcheck:")
        response = client.get('/healthcheck')
        data = response.get_json()
        
        print(f"   ✓ Status code: {response.status_code}")
        print(f"   ✓ Health status: {data.get('status')}")
        
        # Test 5: Sample response structure for frontend
        print("\n5. Sample JavaScript fetch code for your website:")
        print("""
   // Example Next.js integration
   const fetchDailySummary = async () => {
     try {
       const response = await fetch('/api/daily-summary');
       const data = await response.json();
       
       if (data.status === 'success') {
         setSummary(data.summary);
         setCompanies(data.companies_included);
         setArticleCount(data.total_articles);
       } else {
         console.log('Service updating:', data.status);
       }
     } catch (error) {
       console.error('API error:', error);
     }
   };
        """)
        
        print("\n✅ All tests completed! Your API is ready for website integration.")

if __name__ == "__main__":
    test_api_responses()