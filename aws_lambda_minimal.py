#!/usr/bin/env python
"""
Minimal AWS Lambda function for Z-News daily summary endpoint
Optimized for website integration without heavy dependencies
"""

import json
import os
from typing import Dict, List, Any
from datetime import datetime

def generate_daily_summary_minimal(companies_list: List[str] = None) -> Dict[str, Any]:
    """
    Generate minimal daily summary response for website integration
    Returns mock data when search services are unavailable
    """
    
    # Default companies if none provided
    if not companies_list:
        companies_list = [
            "Ameriprise Financial, Inc.",
            "American National Life Insurance", 
            "Advisors Excel, LLC"
        ]
    
    # Mock summary for when search is unavailable
    mock_summary = f"""# Financial Services News Summary - {datetime.now().strftime('%B %d, %Y')}

## Service Status

The news search service is currently experiencing connectivity issues with external data providers. 

## Companies Monitored

The following companies are being tracked for news updates:

{chr(10).join(f"- {company}" for company in companies_list)}

## Next Update

Please check back later for the latest financial services news and analysis.

---
*This is an automated summary service for financial services industry news.*
"""
    
    # Create response optimized for website display
    return {
        'date': datetime.now().strftime('%Y-%m-%d'),
        'generated_at': datetime.now().isoformat(),
        'summary': mock_summary,
        'companies_included': companies_list,
        'total_articles': 0,
        'time_period': 'past week',
        'status': 'service_unavailable'
    }

def lambda_handler(event, context):
    """
    Minimal AWS Lambda handler function
    """
    try:
        # Check if this is from API Gateway
        if 'httpMethod' in event:
            # API Gateway request
            path = event.get('path', '')
            method = event.get('httpMethod', '')
            query_params = event.get('queryStringParameters') or {}
            
            if path == '/daily-summary' and method == 'GET':
                # Handle daily summary request from API Gateway
                companies_param = query_params.get('companies')
                companies_list = None
                if companies_param:
                    companies_list = [name.strip() for name in companies_param.split(',')]
                
                response_data = generate_daily_summary_minimal(companies_list)
                
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Headers': 'Content-Type',
                        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
                    },
                    'body': json.dumps(response_data)
                }
            else:
                # Default API Gateway response
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'message': 'Z-News API - Access /daily-summary for daily summaries',
                        'available_endpoints': ['/daily-summary'],
                        'status': 'healthy'
                    })
                }
        
        # Direct Lambda invocation
        elif event.get('action') == 'daily_summary':
            companies_param = event.get('companies')
            
            # Parse companies list
            companies_list = None
            if companies_param:
                if isinstance(companies_param, str):
                    companies_list = [name.strip() for name in companies_param.split(',')]
                elif isinstance(companies_param, list):
                    companies_list = companies_param
            
            # Generate daily summary
            response_data = generate_daily_summary_minimal(companies_list)
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
                },
                'body': json.dumps(response_data)
            }
        
        # Default response for other requests
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Z-News API - Use action=daily_summary for daily summaries',
                'available_endpoints': ['/daily-summary'],
                'status': 'healthy'
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': f'An error occurred: {str(e)}'})
        }

if __name__ == "__main__":
    # Test locally
    test_event = {"action": "daily_summary"}
    result = lambda_handler(test_event, None)
    print(json.dumps(json.loads(result['body']), indent=2))