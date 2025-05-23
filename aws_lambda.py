#!/usr/bin/env python
"""
AWS Lambda function for Z-News

This module provides a Lambda function that can search for news about specific companies
and generate summaries. It can be invoked via API Gateway.
"""

import json
import os
import pandas as pd
from typing import Dict, List, Any, Optional, Union
import tempfile
from datetime import datetime

# Import required modules from the existing codebase
from services.search_service import SearchService
from services.api_client import ClaudeApiClient
from config.config import (
    TIME_DESCRIPTIONS,
    WEEKLY_TIME_PERIOD,
    DEFAULT_RESULT_COUNT,
    HIGH_PROFILE_RESULT_COUNT,
    LOW_PROFILE_RESULT_COUNT,
    HIGH_PROFILE_ENTITIES,
    LOW_PROFILE_ENTITIES
)
from utils import (
    load_entities,
    get_entity_name,
    get_entity_query,
    calculate_relevance_score  # Import from collect_all_news.py
)


def find_client_by_name(company_name: str) -> Dict[str, Any]:
    """
    Find a client in the clients.json file by name
    
    Args:
        company_name: Name of the company to search for
        
    Returns:
        Client dict if found, empty dict if not found
    """
    clients = load_entities("client")
    
    # Try exact match first
    for client in clients:
        if client.get("name", "").lower() == company_name.lower():
            return client
    
    # Try partial match
    for client in clients:
        if company_name.lower() in client.get("name", "").lower():
            return client
    
    return {}


def get_client_news(company_name: str, time_filter: str = WEEKLY_TIME_PERIOD, max_results: int = None) -> List[Dict[str, Any]]:
    """
    Get news for a specific client
    
    Args:
        company_name: Name of the company to search for
        time_filter: Time filter for search results (d/w/m/y/None)
        max_results: Maximum number of results to return
        
    Returns:
        List of news article dictionaries
    """
    # Find the client in the clients.json file
    client = find_client_by_name(company_name)
    
    if not client:
        raise ValueError(f"Company '{company_name}' not found in clients.json")
    
    # Determine the appropriate max_results based on company profile
    if max_results is None:
        if any(high in client["name"] for high in HIGH_PROFILE_ENTITIES):
            max_results = HIGH_PROFILE_RESULT_COUNT
        elif any(low in client["name"] for low in LOW_PROFILE_ENTITIES):
            max_results = LOW_PROFILE_RESULT_COUNT
        else:
            max_results = DEFAULT_RESULT_COUNT
    
    # Create search service
    search_service = SearchService()
    
    # Get the search query
    search_query = client.get("query", f'"{client["name"]}"')
    
    # Search for news
    results = search_service.search_news(search_query, max_results=max_results, time_filter=time_filter)
    
    # Calculate relevance scores for each article
    for article in results:
        title = article.get('title', '')
        excerpt = article.get('body', '')
        relevance = calculate_relevance_score(title, excerpt, client["name"])
        article['relevance'] = relevance
    
    # Sort by relevance
    results = sorted(results, key=lambda x: x.get('relevance', 0), reverse=True)
    
    return results


def generate_summary_for_company(company_name: str, news_articles: List[Dict[str, Any]], 
                                summary_type: str = "client") -> str:
    """
    Generate a summary for a specific company using the Claude API
    
    Args:
        company_name: Name of the company
        news_articles: List of news articles
        summary_type: Type of summary (client or competitor)
        
    Returns:
        Generated summary text
    """
    api_client = ClaudeApiClient()
    
    # Format the data for the prompt
    data_for_prompt = {company_name: news_articles}
    news_data_str = json.dumps(data_for_prompt, indent=2)
    
    if summary_type == "client":
        title = "Client Executive News Summary"
        focus = "financial service clients"
        prompt_template = """## {title}

Create a concise executive news summary for {focus}. These summaries will be provided to executives who develop software and back office services for financial service companies.

Your output must be:
- Direct and factual
- Focused on the most important news developments
- Written in a clear, professional business tone
- Free of excessive detail, speculation, or editorializing

For each company, create a markdown section with:
1. A level-2 heading with the company name
2. A concise summary paragraph (3-5 sentences) that:
   - Captures the most significant recent developments
   - Focuses on technology initiatives, financial performance, partnerships, new products
   - Includes specific facts and figures when available
   - Emphasizes news relevant to financial service software/service providers

News Data:
{news_data}
"""
    else:  # competitor
        title = "Competitor Intelligence Summary"
        focus = "financial service competitors"
        prompt_template = """## {title}

Create a concise competitor intelligence summary for {focus}. These summaries will be provided to executives who develop software and back office services for financial service companies.

Your output must be:
- Direct and factual
- Strategically focused on competitive implications
- Written in a clear, professional business tone
- Free of excessive detail or speculation

For each competitor, create a markdown section with:
1. A level-2 heading with the competitor name
2. A concise competitive analysis paragraph (3-5 sentences) that:
   - Identifies strategic market moves and positioning
   - Analyzes competitive implications
   - Highlights new products, partnerships, or acquisitions that strengthen their position
   - Identifies potential threats or opportunities for software/service providers
   - Emphasizes insights that help predict future competitive actions

News Data:
{news_data}
"""
    
    # Format the prompt
    prompt = prompt_template.format(
        title=title,
        focus=focus,
        news_data=news_data_str
    )
    
    # Generate the summary
    system_prompt = 'You are an expert financial analyst creating executive summaries for the financial services industry.'
    summary = api_client.generate_summary(prompt, system_prompt)
    
    return summary


def create_consolidated_summary(client_articles: List[Dict[str, Any]], 
                               competitor_articles: List[Dict[str, Any]],
                               client_name: str, competitor_name: str) -> str:
    """
    Generate a consolidated summary for both client and competitor
    
    Args:
        client_articles: List of client news articles
        competitor_articles: List of competitor news articles
        client_name: Name of the client
        competitor_name: Name of the competitor
        
    Returns:
        Generated consolidated summary text
    """
    api_client = ClaudeApiClient()
    
    # Format the data for the prompt
    data_for_prompt = {
        "clients": {client_name: client_articles},
        "competitors": {competitor_name: competitor_articles}
    }
    
    news_data_str = json.dumps(data_for_prompt, indent=2)
    
    prompt = f"""## Financial Services News Summary
            
    Create a concise executive news summary for financial service clients and competitors. These summaries will be provided to executives who develop software and back office services for financial service companies.
    
    Your output must be direct, factual, and focused on the most important news developments.
    
    ### Instructions:
    
    1. Create a markdown document with the title "Financial Services News Summary" and today's date.
    
    2. Create two main sections:
       - "Client Companies" - for all companies in the "clients" object of the data
       - "Competitor Companies" - for all companies in the "competitors" object of the data
    
    3. Within each section, for each company with news, include a subsection header with the company name.
    
    4. When writing about CLIENTS:
       - Write a single paragraph (3-5 sentences) that summarizes the most significant recent news
       - Focus on technology initiatives, financial performance, partnerships, new products/services
       - Be direct and factual about developments relevant to software/service providers
       - Include specific facts and figures when available
    
    5. When writing about COMPETITORS:
       - Focus on strategic competitive moves and market positioning
       - Analyze how their actions might affect the competitive landscape
       - Highlight new products, partnerships, or acquisitions that strengthen their position
       - Identify potential threats or opportunities their moves create
       - Emphasize insights that help predict their future competitive actions
    
    6. IMPORTANT: If the story is an analyst report written by the client about another company, please ignore it. Only include news about the client/competitor company itself, not reports or analysis they publish about other companies.
    
    7. Format the final output as a clean, professional markdown document.
    
    8. VERY IMPORTANT: Only include companies under their correct category as defined in the JSON data structure. Companies in the "clients" object should ONLY appear in the "Client Companies" section, and companies in the "competitors" object should ONLY appear in the "Competitor Companies" section.
    
    ### News Data:
    {news_data_str}
    """
    
    # Generate the summary
    system_prompt = 'You are an expert financial analyst creating executive summaries for the financial services industry.'
    summary = api_client.generate_summary(prompt, system_prompt)
    
    return summary


def generate_daily_summary(companies_list: List[str] = None, time_filter: str = WEEKLY_TIME_PERIOD) -> Dict[str, Any]:
    """
    Generate daily summary for multiple companies optimized for website integration
    
    Args:
        companies_list: List of company names (defaults to first 5 clients)
        time_filter: Time filter for search results
        
    Returns:
        Dictionary with daily summary data optimized for website display
    """
    from datetime import datetime
    
    # Use default companies if none provided
    if not companies_list:
        clients = load_entities("client")
        companies_list = [client["name"] for client in clients[:5]]
    
    # Collect news for all companies
    all_articles = []
    companies_included = []
    total_articles = 0
    
    for company_name in companies_list:
        try:
            articles = get_client_news(company_name, time_filter, max_results=10)
            if articles:
                all_articles.extend(articles)
                companies_included.append(company_name)
                total_articles += len(articles)
        except Exception:
            continue
    
    # Generate consolidated summary if we have articles
    summary = ""
    if all_articles:
        try:
            # Create a consolidated data structure for the prompt
            companies_data = {}
            for company_name in companies_included:
                company_articles = [article for article in all_articles 
                                  if company_name.lower() in article.get('title', '').lower() 
                                  or company_name.lower() in article.get('body', '').lower()]
                if company_articles:
                    companies_data[company_name] = company_articles
            
            # Generate summary using existing Claude API client
            api_client = ClaudeApiClient()
            news_data_str = json.dumps(companies_data, indent=2)
            
            prompt = f"""## Daily Financial Services News Summary

Create a concise daily executive summary for financial service companies. This summary will be displayed on a website for executives who develop software and back office services for financial service companies.

Your output must be:
- Direct and factual
- Focused on the most important news developments
- Written in clean markdown format
- Optimized for web display

### Instructions:

1. Create a markdown document with today's date as a level-1 heading
2. For each company with significant news, create a level-2 heading with the company name
3. Write a single concise paragraph (2-4 sentences) highlighting:
   - Most significant recent developments
   - Technology initiatives, financial performance, partnerships, new products
   - Specific facts and figures when available
   - Relevance to financial service software/service providers

4. Only include companies with meaningful news developments
5. Format as clean markdown suitable for web display

### News Data:
{news_data_str}
"""
            
            system_prompt = 'You are an expert financial analyst creating daily executive summaries for the financial services industry.'
            summary = api_client.generate_summary(prompt, system_prompt)
            
        except Exception as e:
            summary = f"Error generating summary: {str(e)}"
    
    # Create response optimized for website display
    return {
        'date': datetime.now().strftime('%Y-%m-%d'),
        'generated_at': datetime.now().isoformat(),
        'summary': summary,
        'companies_included': companies_included,
        'total_articles': total_articles,
        'time_period': TIME_DESCRIPTIONS.get(time_filter, 'custom')
    }


# AWS Lambda handler function
def lambda_handler(event, context):
    """
    AWS Lambda handler function
    
    Args:
        event: The event dict from Lambda containing request information
        context: The context object from Lambda
    
    Returns:
        API Gateway response object with generated news data and/or summary
    """
    try:
        # Check if this is a daily summary request
        if event.get('action') == 'daily_summary':
            companies_param = event.get('companies')
            time_filter = event.get('time_filter', WEEKLY_TIME_PERIOD)
            
            # Parse companies list
            companies_list = None
            if companies_param:
                if isinstance(companies_param, str):
                    companies_list = [name.strip() for name in companies_param.split(',')]
                elif isinstance(companies_param, list):
                    companies_list = companies_param
            
            # Generate daily summary
            response_data = generate_daily_summary(companies_list, time_filter)
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps(response_data)
            }
        
        # Parse request data based on whether it's coming from API Gateway
        if 'body' in event:
            # API Gateway request with body
            try:
                # If body is a string, parse it as JSON
                if isinstance(event['body'], str):
                    request_data = json.loads(event['body'])
                else:
                    request_data = event['body']
            except:
                request_data = {}
        elif 'queryStringParameters' in event and event['queryStringParameters']:
            # API Gateway request with query string parameters
            request_data = event['queryStringParameters']
        else:
            # Direct Lambda invocation
            request_data = event
        
        # Get parameters
        company_name = request_data.get('company_name')
        time_filter = request_data.get('time_filter', WEEKLY_TIME_PERIOD)
        max_results = request_data.get('max_results')
        summary_type = request_data.get('summary_type', 'client')  # client, competitor, consolidated
        competitor_name = request_data.get('competitor_name')  # For consolidated summary
        
        # Validate input
        if not company_name:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Missing required parameter: company_name'})
            }
        
        # Convert max_results to int if provided
        if max_results:
            try:
                max_results = int(max_results)
            except ValueError:
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'max_results must be a number'})
                }
        
        # Get news for the specified company
        news_articles = get_client_news(company_name, time_filter, max_results)
        
        # Create response dictionary
        response = {
            'company_name': company_name,
            'time_period': TIME_DESCRIPTIONS.get(time_filter, 'custom'),
            'articles_found': len(news_articles),
            'articles': news_articles
        }
        
        # Generate summary if there are articles
        if news_articles:
            if summary_type == 'consolidated' and competitor_name:
                # Get competitor news
                competitor_articles = get_client_news(competitor_name, time_filter, max_results)
                response['competitor_name'] = competitor_name
                response['competitor_articles_found'] = len(competitor_articles)
                
                # Generate consolidated summary
                summary = create_consolidated_summary(
                    news_articles, competitor_articles, company_name, competitor_name
                )
                response['summary'] = summary
            else:
                # Generate summary for just the company
                summary = generate_summary_for_company(company_name, news_articles, summary_type)
                response['summary'] = summary
        
        # Return successful response
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(response)
        }
        
    except ValueError as e:
        return {
            'statusCode': 404,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': f'An error occurred: {str(e)}'})
        }


if __name__ == "__main__":
    """
    This section allows the Lambda function to be tested locally
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate company-specific news and summaries")
    parser.add_argument('--company', required=True, help="Company name to search for")
    parser.add_argument('--time', choices=['d', 'w', 'm', 'y'], default='w', 
                      help="Time filter (d=day, w=week, m=month, y=year)")
    parser.add_argument('--results', type=int, help="Maximum number of results")
    parser.add_argument('--type', choices=['client', 'competitor', 'consolidated'], 
                      default='client', help="Type of summary to generate")
    parser.add_argument('--competitor', help="Competitor name (for consolidated summary)")
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.type == 'consolidated' and not args.competitor:
        parser.error("--competitor is required when --type is 'consolidated'")
    
    # Simulate an API Gateway event
    event = {
        'body': json.dumps({
            'company_name': args.company,
            'time_filter': args.time,
            'max_results': args.results,
            'summary_type': args.type,
            'competitor_name': args.competitor
        })
    }
    
    # Call the Lambda handler function
    response = lambda_handler(event, None)
    
    # Print the response
    if response['statusCode'] != 200:
        print(f"Error: {json.loads(response['body'])['error']}")
    else:
        result = json.loads(response['body'])
        print(f"\nCompany: {result['company_name']}")
        print(f"Time period: {result['time_period']}")
        print(f"Articles found: {result['articles_found']}")
        
        if args.type == 'consolidated' and args.competitor:
            print(f"Competitor: {result['competitor_name']}")
            print(f"Competitor articles found: {result['competitor_articles_found']}")
            
        if 'summary' in result:
            print("\n" + "="*50)
            print("SUMMARY:")
            print("="*50)
            print(result['summary'])