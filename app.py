#!/usr/bin/env python
"""
Flask application for Z-News API
Designed for deployment with Zappa to AWS Lambda
"""

from flask import Flask, request, jsonify
import json
import os
import pandas as pd
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger('z-news')

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
    calculate_relevance_score
)

# Initialize Flask app
app = Flask(__name__)

def find_client_by_name(company_name: str) -> Dict[str, Any]:
    """
    Find a client in the clients.json file by name
    
    Args:
        company_name: Name of the company to search for
        
    Returns:
        Client dict if found, empty dict if not found
    """
    logger.info(f"Looking for company: {company_name}")
    clients = load_entities("client")
    
    # Try exact match first
    for client in clients:
        if client.get("name", "").lower() == company_name.lower():
            logger.info(f"Found exact match for company: {company_name}")
            return client
    
    # Try partial match
    for client in clients:
        if company_name.lower() in client.get("name", "").lower():
            logger.info(f"Found partial match for company: {company_name} -> {client.get('name')}")
            return client
    
    logger.warning(f"Company not found: {company_name}")
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
    logger.info(f"Getting news for company: {company_name}, time filter: {time_filter}")
    
    # Find the client in the clients.json file
    client = find_client_by_name(company_name)
    
    if not client:
        logger.error(f"Company '{company_name}' not found in clients.json")
        raise ValueError(f"Company '{company_name}' not found in clients.json")
    
    # Determine the appropriate max_results based on company profile
    if max_results is None:
        if any(high in client["name"] for high in HIGH_PROFILE_ENTITIES):
            max_results = HIGH_PROFILE_RESULT_COUNT
        elif any(low in client["name"] for low in LOW_PROFILE_ENTITIES):
            max_results = LOW_PROFILE_RESULT_COUNT
        else:
            max_results = DEFAULT_RESULT_COUNT
    
    logger.info(f"Using max_results: {max_results}")
    
    # Create search service
    search_service = SearchService()
    
    # Get the search query
    search_query = client.get("query", f'"{client["name"]}"')
    
    # Search for news
    logger.info(f"Searching for news with query: {search_query}")
    results = search_service.search_news(search_query, max_results=max_results, time_filter=time_filter)
    
    # Calculate relevance scores for each article
    for article in results:
        title = article.get('title', '')
        excerpt = article.get('body', '')
        relevance = calculate_relevance_score(title, excerpt, client["name"])
        article['relevance'] = relevance
    
    # Sort by relevance
    results = sorted(results, key=lambda x: x.get('relevance', 0), reverse=True)
    
    logger.info(f"Found {len(results)} news articles for {company_name}")
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
    logger.info(f"Generating {summary_type} summary for {company_name}")
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
    logger.info(f"Calling Claude API to generate summary")
    system_prompt = 'You are an expert financial analyst creating executive summaries for the financial services industry.'
    summary = api_client.generate_summary(prompt, system_prompt)
    
    if summary:
        logger.info(f"Successfully generated summary ({len(summary)} characters)")
    else:
        logger.error("Failed to generate summary")
    
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
    logger.info(f"Generating consolidated summary for {client_name} and {competitor_name}")
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
    logger.info(f"Calling Claude API to generate consolidated summary")
    system_prompt = 'You are an expert financial analyst creating executive summaries for the financial services industry.'
    summary = api_client.generate_summary(prompt, system_prompt)
    
    if summary:
        logger.info(f"Successfully generated consolidated summary ({len(summary)} characters)")
    else:
        logger.error("Failed to generate consolidated summary")
    
    return summary


@app.route('/z-news', methods=['POST'])
def generate_news_for_company():
    """
    Flask route for z-news API endpoint
    """
    try:
        # Log request information
        request_id = datetime.now().strftime('%Y%m%d%H%M%S-') + str(hash(datetime.now().microsecond))[-4:]
        logger.info(f"Request {request_id}: Received request to /z-news endpoint")
        
        # Parse request data
        if request.is_json:
            request_data = request.json
            logger.info(f"Request {request_id}: Received JSON data")
        else:
            request_data = request.form.to_dict()
            logger.info(f"Request {request_id}: Received form data")
        
        # Get parameters
        company_name = request_data.get('company_name')
        time_filter = request_data.get('time_filter', WEEKLY_TIME_PERIOD)
        max_results = request_data.get('max_results')
        summary_type = request_data.get('summary_type', 'client')  # client, competitor, consolidated
        competitor_name = request_data.get('competitor_name')  # For consolidated summary
        
        logger.info(f"Request {request_id}: Parameters - company_name: {company_name}, time_filter: {time_filter}, " +
                   f"summary_type: {summary_type}, competitor_name: {competitor_name}")
        
        # Validate input
        if not company_name:
            logger.error(f"Request {request_id}: Missing required parameter: company_name")
            return jsonify({'error': 'Missing required parameter: company_name'}), 400
        
        # Convert max_results to int if provided
        if max_results:
            try:
                max_results = int(max_results)
                logger.info(f"Request {request_id}: max_results: {max_results}")
            except ValueError:
                logger.error(f"Request {request_id}: Invalid max_results value: {max_results}")
                return jsonify({'error': 'max_results must be a number'}), 400
        
        # Get news for the specified company
        try:
            news_articles = get_client_news(company_name, time_filter, max_results)
        except Exception as e:
            logger.error(f"Request {request_id}: Error getting news: {str(e)}", exc_info=True)
            raise
        
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
                try:
                    # Get competitor news
                    competitor_articles = get_client_news(competitor_name, time_filter, max_results)
                    response['competitor_name'] = competitor_name
                    response['competitor_articles_found'] = len(competitor_articles)
                    
                    # Generate consolidated summary
                    summary = create_consolidated_summary(
                        news_articles, competitor_articles, company_name, competitor_name
                    )
                    response['summary'] = summary
                except Exception as e:
                    logger.error(f"Request {request_id}: Error in consolidated summary: {str(e)}", exc_info=True)
                    response['summary_error'] = f"Error generating consolidated summary: {str(e)}"
            else:
                try:
                    # Generate summary for just the company
                    summary = generate_summary_for_company(company_name, news_articles, summary_type)
                    response['summary'] = summary
                except Exception as e:
                    logger.error(f"Request {request_id}: Error in summary generation: {str(e)}", exc_info=True)
                    response['summary_error'] = f"Error generating summary: {str(e)}"
        
        logger.info(f"Request {request_id}: Completed successfully with {len(news_articles)} articles")
        return jsonify(response)
        
    except ValueError as e:
        logger.error(f"Request error (ValueError): {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        logger.error(f"Request error (Exception): {str(e)}", exc_info=True)
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500


@app.route('/healthcheck', methods=['GET'])
def healthcheck():
    """Simple healthcheck endpoint to verify the API is running"""
    logger.info("Healthcheck endpoint called")
    return jsonify({
        'status': 'healthy',
        'service': 'z-news-api',
        'timestamp': datetime.now().isoformat()
    })


# This allows running the Flask app locally for testing
if __name__ == "__main__":
    app.run(debug=True)