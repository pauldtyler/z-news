#!/usr/bin/env python
"""
NewsAPI service to replace DuckDuckGo search functionality
"""

import os
import time
import random
import requests
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger('z-news')

# Import configuration
from config.config import (
    MAX_RETRIES,
    INITIAL_BACKOFF,
    MAX_BACKOFF
)

class NewsAPIService:
    """Service for searching news articles using NewsAPI"""
    
    def __init__(self):
        """Initialize the NewsAPI service"""
        self.api_key = os.getenv('NEWSAPI_API_KEY')
        if not self.api_key:
            raise ValueError("NEWSAPI_API_KEY not found in environment variables")
        
        self.base_url = "https://newsapi.org/v2/everything"
        
        # Rate limit indicators for error detection
        self.rate_limit_indicators = [
            "rate limit", 
            "too many requests", 
            "429", 
            "throttl",
            "blocked",
            "denied",
            "limit exceeded",
            "try again later",
            "rateLimited"
        ]
    
    def search_news(self, query: str, max_results: int = 10, 
                    time_filter: Optional[str] = 'm', attempt: int = 1) -> List[Dict[str, Any]]:
        """
        Search for news articles using NewsAPI
        
        Args:
            query: The search query
            max_results: Maximum number of results to return
            time_filter: Time filter for results (d/w/m/y/None)
            attempt: Current attempt number for retries
            
        Returns:
            List of news article dictionaries
        """
        results = []
        
        # Convert time_filter to NewsAPI date format
        date_from = self._get_date_from_filter(time_filter)
        
        try:
            params = {
                'q': query,
                'language': 'en',
                'sortBy': 'publishedAt',
                'pageSize': min(max_results, 100),  # NewsAPI max is 100
                'apiKey': self.api_key
            }
            
            if date_from:
                params['from'] = date_from
            
            headers = {
                "User-Agent": "Z-News/1.0"
            }
            
            logger.info(f"Searching NewsAPI for: {query}, time filter: {time_filter}")
            response = requests.get(self.base_url, params=params, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 'ok':
                    articles = data.get('articles', [])
                    
                    # Process results to match expected format
                    for article in articles[:max_results]:
                        result_dict = {
                            'title': article.get('title', ''),
                            'body': article.get('description', '') or article.get('content', ''),
                            'href': article.get('url', ''),
                            'source': article.get('source', {}).get('name', ''),
                            'date': article.get('publishedAt', '')
                        }
                        results.append(result_dict)
                    
                    logger.info(f"Found {len(results)} news results from NewsAPI")
                    
                else:
                    logger.error(f"NewsAPI error: {data.get('message', 'Unknown error')}")
                    if attempt < MAX_RETRIES:
                        return self._retry_search(query, max_results, time_filter, attempt)
                        
            elif response.status_code == 429:
                logger.warning("NewsAPI rate limit hit")
                if attempt < MAX_RETRIES:
                    return self._retry_search(query, max_results, time_filter, attempt)
                    
            else:
                logger.error(f"NewsAPI HTTP error: {response.status_code}")
                if attempt < MAX_RETRIES:
                    return self._retry_search(query, max_results, time_filter, attempt)
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error searching NewsAPI for '{query}': {str(e)}")
            if attempt < MAX_RETRIES:
                return self._retry_search(query, max_results, time_filter, attempt)
        
        return results
    
    def _get_date_from_filter(self, time_filter: Optional[str]) -> Optional[str]:
        """Convert time filter to ISO date string for NewsAPI"""
        if not time_filter:
            return None
            
        now = datetime.now()
        
        if time_filter == 'd':
            date_from = now - timedelta(days=1)
        elif time_filter == 'w':
            date_from = now - timedelta(weeks=1)
        elif time_filter == 'm':
            date_from = now - timedelta(days=30)
        elif time_filter == 'y':
            date_from = now - timedelta(days=365)
        else:
            return None
            
        return date_from.strftime('%Y-%m-%d')
    
    def _retry_search(self, query: str, max_results: int, time_filter: str, attempt: int) -> List[Dict[str, Any]]:
        """Handle retry logic with exponential backoff"""
        wait_time = min(INITIAL_BACKOFF * (2 ** (attempt - 1)), MAX_BACKOFF)
        jitter = wait_time * 0.1 * (2 * (random.random() - 0.5))
        total_wait = wait_time + jitter
        
        logger.info(f"Retrying NewsAPI search in {total_wait:.1f} seconds (attempt {attempt + 1}/{MAX_RETRIES})...")
        time.sleep(total_wait)
        
        return self.search_news(query, max_results, time_filter, attempt + 1)