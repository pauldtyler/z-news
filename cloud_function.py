#!/usr/bin/env python
"""
Google Cloud Function for Z-News

This module provides a Cloud Function that can search for news about specific companies
and generate summaries. It can be invoked in an ad-hoc manner for testing before
incorporating into the company-wide GCP repository.
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


def create_dataframe_from_news(news_articles: List[Dict[str, Any]], company_name: str) -> pd.DataFrame:
    """
    Convert a list of news articles to a pandas DataFrame
    
    Args:
        news_articles: List of news articles
        company_name: Name of the company
        
    Returns:
        Pandas DataFrame
    """
    news_data = []
    
    for article in news_articles:
        article_info = {
            'client': company_name,
            'title': article.get('title', ''),
            'url': article.get('url', ''),
            'date': article.get('date', ''),
            'source': article.get('source', ''),
            'excerpt': article.get('body', ''),  # Using 'body' instead of 'excerpt'
            'image': article.get('image', ''),
            'relevance': article.get('relevance', 0.0)
        }
        news_data.append(article_info)
    
    news_df = pd.DataFrame(news_data)
    
    # Basic cleaning
    if not news_df.empty:
        # Convert date strings to datetime objects if possible
        try:
            news_df['date'] = pd.to_datetime(news_df['date'])
            
            # Then standardize by converting all to UTC and then removing timezone
            if hasattr(news_df['date'].dt, 'tz'):
                # Convert all to UTC first
                news_df['date'] = news_df['date'].dt.tz_convert('UTC')
                # Then remove timezone info for consistent comparison
                news_df['date'] = news_df['date'].dt.tz_localize(None)
        except Exception as e:
            print(f"Date conversion issue: {e}")
        
        # Sort by relevance score (primary) and date (secondary)
        try:
            news_df = news_df.sort_values(['relevance', 'date'], ascending=[False, False])
        except:
            pass
    
    return news_df


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


def generate_news_for_company(request):
    """
    Cloud Function entry point
    
    Args:
        request: Flask request object
    
    Returns:
        Response with the generated news data and/or summary
    """
    try:
        # Parse request data
        request_json = request.get_json(silent=True)
        request_args = request.args
        
        # Get parameters from either JSON body or URL parameters
        if request_json:
            company_name = request_json.get('company_name')
            time_filter = request_json.get('time_filter', WEEKLY_TIME_PERIOD)
            max_results = request_json.get('max_results')
            summary_type = request_json.get('summary_type', 'client')  # client, competitor, consolidated
            competitor_name = request_json.get('competitor_name')  # For consolidated summary
        else:
            company_name = request_args.get('company_name')
            time_filter = request_args.get('time_filter', WEEKLY_TIME_PERIOD)
            max_results = request_args.get('max_results')
            summary_type = request_args.get('summary_type', 'client')
            competitor_name = request_args.get('competitor_name')
        
        # Validate input
        if not company_name:
            return {'error': 'Missing required parameter: company_name'}, 400
        
        # Convert max_results to int if provided
        if max_results:
            try:
                max_results = int(max_results)
            except ValueError:
                return {'error': 'max_results must be a number'}, 400
        
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
                
        return response
        
    except ValueError as e:
        return {'error': str(e)}, 404
    except Exception as e:
        return {'error': f'An error occurred: {str(e)}'}, 500


def process_news_locally(company_name, time_filter=WEEKLY_TIME_PERIOD, 
                        max_results=None, summary_type='client', 
                        competitor_name=None, save_csv=True, save_summary=True):
    """
    Process news locally for testing purposes
    
    Args:
        company_name: Name of the company to search for
        time_filter: Time filter for search results (d/w/m/y/None)
        max_results: Maximum number of results to return
        summary_type: Type of summary (client, competitor, consolidated)
        competitor_name: Name of competitor (only for consolidated summary)
        save_csv: Whether to save results to CSV
        save_summary: Whether to save summary to markdown file
        
    Returns:
        Tuple of (news_df, summary, response)
    """
    try:
        # Create data directory if it doesn't exist
        if not os.path.exists('data'):
            os.makedirs('data')
            
        # Get news for the specified company
        news_articles = get_client_news(company_name, time_filter, max_results)
        
        # Create response dictionary
        response = {
            'company_name': company_name,
            'time_period': TIME_DESCRIPTIONS.get(time_filter, 'custom'),
            'articles_found': len(news_articles),
            'articles': news_articles
        }
        
        # Convert to DataFrame
        news_df = create_dataframe_from_news(news_articles, company_name)
        
        # Save to CSV if requested
        if save_csv and not news_df.empty:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_filename = f"data/{company_name.replace(' ', '_')}_{timestamp}.csv"
            news_df.to_csv(csv_filename, index=False)
            print(f"News data saved to {csv_filename}")
            response['csv_file'] = csv_filename
        
        # Generate summary if there are articles
        summary = None
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
            
            # Save summary to file if requested
            if save_summary and summary:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                summary_filename = f"data/{company_name.replace(' ', '_')}_{summary_type}_{timestamp}.md"
                with open(summary_filename, 'w') as f:
                    f.write(summary)
                print(f"Summary saved to {summary_filename}")
                response['summary_file'] = summary_filename
        
        return news_df, summary, response
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return None, None, {'error': str(e)}


if __name__ == "__main__":
    """
    This section allows the cloud function to be tested locally
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
    parser.add_argument('--no-csv', action='store_false', dest='save_csv', 
                      help="Don't save results to CSV")
    parser.add_argument('--no-summary', action='store_false', dest='save_summary',
                      help="Don't save summary to markdown file")
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.type == 'consolidated' and not args.competitor:
        parser.error("--competitor is required when --type is 'consolidated'")
    
    # Process news
    news_df, summary, response = process_news_locally(
        args.company, 
        args.time, 
        args.results, 
        args.type,
        args.competitor,
        args.save_csv,
        args.save_summary
    )
    
    # Print response
    if 'error' in response:
        print(f"Error: {response['error']}")
    else:
        print(f"\nCompany: {response['company_name']}")
        print(f"Time period: {response['time_period']}")
        print(f"Articles found: {response['articles_found']}")
        
        if args.type == 'consolidated' and args.competitor:
            print(f"Competitor: {response['competitor_name']}")
            print(f"Competitor articles found: {response['competitor_articles_found']}")
        
        if 'csv_file' in response:
            print(f"CSV file: {response['csv_file']}")
        
        if 'summary_file' in response:
            print(f"Summary file: {response['summary_file']}")
            
        if summary:
            print("\n" + "="*50)
            print("SUMMARY:")
            print("="*50)
            print(summary)