#!/usr/bin/env python
"""
Search service to handle news searches with proper error handling and rate limiting
"""

import time
import random
import json
import requests
from typing import List, Dict, Any, Optional, Union
import logging

# Configure logging
logger = logging.getLogger('z-news')

# Import configuration
from config.config import (
    MAX_RETRIES,
    INITIAL_BACKOFF,
    MAX_BACKOFF
)

class SearchService:
    """Service for searching news articles with error handling and rate limiting"""
    
    def __init__(self):
        """Initialize the search service"""
        # Rate limit indicators for error detection
        self.rate_limit_indicators = [
            "rate limit", 
            "too many requests", 
            "429", 
            "throttl",
            "blocked",
            "denied",
            "limit exceeded",
            "try again later"
        ]
    
    def search_news(self, query: str, max_results: int = 10, 
                    time_filter: Optional[str] = 'm', attempt: int = 1) -> List[Dict[str, Any]]:
        """
        Search for news articles using requests-based fetching with robust error handling
        
        Args:
            query: The search query
            max_results: Maximum number of results to return
            time_filter: Time filter for results (d/w/m/y/None)
            attempt: Current attempt number for retries
            
        Returns:
            List of news article dictionaries
        """
        results = []
        
        # Convert time_filter to DuckDuckGo format
        time_map = {
            'd': '1d',  # day
            'w': '1w',  # week
            'm': '1m',  # month
            'y': '1y'   # year
        }
        
        ddg_time = time_map.get(time_filter, '1m')  # Default to 1 month
        
        try:
            # Construct the search URL
            encoded_query = requests.utils.quote(query)
            url = f"https://duckduckgo.com/news.js?q={encoded_query}&o=json&df={ddg_time}&kl=us-en"
            
            # User-Agent to mimic browser
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br"
            }
            
            logger.info(f"Searching for news with query: {query}, time filter: {ddg_time}")
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()  # Raise exception for bad status codes
            
            # Parse the response
            try:
                data = response.json()
                news_items = data.get('results', [])
                
                # Process results
                for item in news_items[:max_results]:
                    result_dict = {
                        'title': item.get('title', ''),
                        'body': item.get('excerpt', ''),
                        'href': item.get('url', ''),
                        'source': item.get('source', ''),
                        'date': item.get('date', '')
                    }
                    results.append(result_dict)
                
                logger.info(f"Found {len(results)} news results")
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Error parsing search results: {str(e)}")
                # Handle empty or invalid response
                if attempt < MAX_RETRIES:
                    wait_time = min(INITIAL_BACKOFF * (2 ** (attempt - 1)), MAX_BACKOFF)
                    logger.info(f"Retrying in {wait_time:.1f} seconds (attempt {attempt}/{MAX_RETRIES})...")
                    time.sleep(wait_time)
                    return self.search_news(query, max_results, time_filter, attempt + 1)
                
        except requests.exceptions.RequestException as e:
            error_msg = str(e).lower()
            logger.error(f"Error searching for '{query}': {str(e)}")
            
            # Check if the error is related to rate limiting
            is_rate_limit = any(indicator in error_msg for indicator in self.rate_limit_indicators)
            
            if is_rate_limit or response.status_code == 429:
                if attempt < MAX_RETRIES:
                    # Calculate wait time with exponential backoff and jitter
                    base_wait = min(INITIAL_BACKOFF * (2 ** (attempt - 1)), MAX_BACKOFF)
                    jitter = base_wait * 0.1 * (2 * (random.random() - 0.5))
                    wait_time = base_wait + jitter
                    
                    logger.info(f"Rate limit detected. Waiting {wait_time:.1f} seconds before retry {attempt}/{MAX_RETRIES}...")
                    time.sleep(wait_time)
                    
                    # Retry with same parameters
                    return self.search_news(query, max_results, time_filter, attempt + 1)
            
            # Try fallback approach with different time filter if first attempt failed
            if attempt < MAX_RETRIES:
                logger.info(f"Trying with different time filter as fallback...")
                # Use a more lenient time filter
                fallback_time = 'm' if time_filter != 'm' else 'y'
                return self.search_news(query, max_results, fallback_time, attempt + 1)
        
        # Return whatever results we have, could be empty
        return results