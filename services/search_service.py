#!/usr/bin/env python
"""
Search service to handle news searches with proper error handling and rate limiting
"""

import time
import random
from typing import List, Dict, Any, Optional, Union

from duckduckgo_search import DDGS

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
        Search for news articles using DuckDuckGo with robust error handling
        
        Args:
            query: The search query
            max_results: Maximum number of results to return
            time_filter: Time filter for results (d/w/m/y/None)
            attempt: Current attempt number for retries
            
        Returns:
            List of news article dictionaries
        """
        results = []
        
        try:
            # For version 8.x, the parameter is timelimit
            with DDGS() as ddgs:
                for r in ddgs.news(query, max_results=max_results, timelimit=time_filter):
                    results.append(r)
                    
        except Exception as e:
            error_msg = str(e).lower()
            print(f"Error searching for '{query}': {e}")
            
            # Check if the error is related to rate limiting
            is_rate_limit = any(indicator in error_msg for indicator in self.rate_limit_indicators)
            
            if is_rate_limit:
                if attempt < MAX_RETRIES:
                    # Calculate wait time with exponential backoff and jitter
                    # Base wait time doubles with each attempt
                    base_wait = min(INITIAL_BACKOFF * (2 ** (attempt - 1)), MAX_BACKOFF)
                    # Add small random jitter (±10%) to avoid thundering herd problem
                    jitter = base_wait * 0.1 * (2 * (random.random() - 0.5))
                    wait_time = base_wait + jitter
                    
                    print(f"  → Rate limit detected. Waiting {wait_time:.1f} seconds before retry {attempt}/{MAX_RETRIES}...")
                    time.sleep(wait_time)
                    
                    # Retry with same parameters
                    return self.search_news(query, max_results, time_filter, attempt + 1)
                else:
                    print(f"  → Maximum retries reached. Trying fallback method...")
            
            # Try alternative approach if the first method fails or max retries reached
            try:
                print(f"  → Trying without time filter...")
                with DDGS() as ddgs:
                    # First try without time filter as fallback
                    for r in ddgs.news(query, max_results=max_results):
                        results.append(r)
                
                # If we got results, return them
                if results:
                    print(f"  → Fallback succeeded with {len(results)} results")
                    return results
                    
            except Exception as e2:
                error_msg2 = str(e2).lower()
                print(f"  → Alternative method also failed: {e2}")
                
                # Check if the fallback hit a rate limit too
                is_rate_limit2 = any(indicator in error_msg2 for indicator in self.rate_limit_indicators)
                
                if is_rate_limit2 and attempt < MAX_RETRIES:
                    # Wait even longer before retrying a final time with reduced results
                    wait_time = min(INITIAL_BACKOFF * (2 ** attempt), MAX_BACKOFF)
                    print(f"  → Rate limit on fallback. Final attempt with {max(1, max_results // 2)} results in {wait_time} seconds...")
                    time.sleep(wait_time)
                    
                    # Last attempt with reduced results
                    try:
                        with DDGS() as ddgs:
                            # Last resort: try with reduced results and no time filter
                            reduced_results = max(1, max_results // 2)
                            for r in ddgs.news(query, max_results=reduced_results):
                                results.append(r)
                        print(f"  → Final attempt got {len(results)} results")
                    except Exception as e3:
                        print(f"  → All methods failed. No results available.")
        
        return results