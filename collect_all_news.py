#!/usr/bin/env python
"""
Comprehensive News Collector

This script collects news for clients and competitors in batches, with proper rate limiting
and error handling, then saves the results to a CSV file.
"""

import pandas as pd
from duckduckgo_search import DDGS
from datetime import datetime
import time
import os
import json
import random
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create data directory if it doesn't exist
if not os.path.exists('data'):
    os.makedirs('data')

# Client list with boolean search capabilities
# Format: (client_name, search_query)
# If search_query is None, client_name will be used as the query
clients = [
    ("J.P. Morgan Chase & Co.", "\"J.P. Morgan Chase\" OR \"JPMorgan Chase\" OR \"JP Morgan\""),
    ("Prudential Financial, Inc.", "\"Prudential Financial\" AND (insurance OR Annuities)"),
    ("USAA", "USAA insurance"),
    ("Advisors Excel, LLC", "\"Advisors Excel\""),
    ("Nationwide Mutual Insurance Company", "\"Nationwide Mutual Insurance\" OR \"Nationwide Insurance\""),
    ("The Guardian Life Insurance Company of America", "\"Guardian Life Insurance\""),
    ("LPL Financial Holdings Inc.", "\"LPL Financial\""),
    ("Legal & General America", "(\"Legal & General America\" AND Insurance) OR (\"Legal and General America\" AND Insurance)"),
    ("Edward Jones", "\"Edward Jones\" financial"),
    ("Morgan Stanley", "\"Morgan Stanley\" finance"),
    ("Merrill Lynch Wealth Management", "\"Merrill Lynch\" wealth management"),
    ("Wells Fargo & Company", "\"Wells Fargo\" financial"),
    ("Kuvare Holdings, Inc.", "\"Kuvare Holdings\""),
    ("Global Atlantic Financial Group", "\"Global Atlantic Financial\""), 
    ("Corebridge Financial, Inc", "\"Corebridge Financial\""),
    ("MassMutual", "\"Massachusetts Mutual Life\" OR \"Massachusetts Mutual Life Insurance Company\" OR \"massmutual\""),
    ("Fidelity Investments", "\"Fidelity Investments\""),
    ("FMR LLC", "\"FMR LLC\" OR \"Fidelity Management & Research\""),
    ("BNY Mellon | Pershing", "\"BNY Mellon\" OR \"Bank of New York Mellon\" OR Pershing"),
    ("Nassau Financial Group", "(\"Nassau\" AND Annuities) OR \"Nassau Financial\""),
    ("Farmers Insurance Group", "\"Farmers Insurance\""),
    ("Ameriprise Financial, Inc.", "\"Ameriprise Financial\""),
    ("FNZ Group", "\"FNZ Group\" financial"),
    ("Wellabe, Inc.", "\"Wellabe\" insurance"), 
    ("Arcus Holdings", "\"Arcus Holdings\" financial"), 
    ("ACAP / Atlantic Coast Life", "(\"ACAP\" AND \"insurance\") OR \"Atlantic Coast Life Insurance\" OR (\"ACAP\" AND \"Atlantic Coast\")"),
    ("Security Benefit Life Insurance Company", "\"Security Benefit Life Insurance\" OR (\"Security Benefit\" AND Annuities)")
]

# Configuration
BATCH_SIZE = 3  # Process entities in batches of this size
WEEKLY_TIME_PERIOD = 'w'  # Always use weekly for the weekly summary
DELAY_BETWEEN_REQUESTS = 8  # Seconds to wait between requests
MAX_RETRIES = 5  # Maximum number of retry attempts
INITIAL_BACKOFF = 10  # Initial backoff time in seconds for rate limits
MAX_BACKOFF = 120  # Maximum backoff time in seconds

# Result count configuration
DEFAULT_RESULT_COUNT = 3  # Default number of recent articles per entity
HIGH_PROFILE_RESULT_COUNT = 5  # More results for high-profile entities to capture important developments
LOW_PROFILE_RESULT_COUNT = 4  # More results for low-profile entities to increase chances of finding news

# Time period descriptions
time_descriptions = {
    'd': 'past day',
    'w': 'past week',
    'm': 'past month',
    'y': 'past year',
    None: 'all time'
}

# Companies that are frequently in the news (need more results to track important developments)
high_profile = [
    "J.P. Morgan Chase & Co.",
    "Morgan Stanley", 
    "Wells Fargo & Company",
    "Fidelity Investments",
    "Accenture",
    "Infosys",
    "Verisk",
    "Prudential Financial, Inc.",
    "MassMutual",
    "USAA",
    "Ameriprise Financial, Inc.",
    "Nationwide Mutual Insurance Company"
]

# Companies that are rarely in the news (need more results to find relevant news)
low_profile = [
    "Advisors Excel, LLC",
    "Legal & General America",
    "Kuvare Holdings, Inc.",
    "Nassau Financial Group",
    "Wellabe, Inc.",
    "Arcus Holdings",
    "ACAP",
    "Atlantic Coast Life Insurance Company",
    "Benekiva",
    "FIDx",
    "Hexure",
    "LIDP",
    "LUMA",
    "Sureify"
]

# Competitor list with boolean search capabilities
# Format: (competitor_name, search_query)
# If search_query is None, competitor_name will be used as the query
competitors = [
    ("Accenture", "\"Accenture\" AND (Insurance OR Annuities)"),
    ("Benekiva", "\"Benekiva\" AND (Insurance OR Claims OR \"Policy Administration\")"),
    ("DXC", "\"DXC Technology\" AND (Insurance OR Annuities)"),
    ("Equisoft", "\"Equisoft\" AND (Insurance OR Annuities OR \"Life Insurance\")"),
    ("FIDx", "\"FIDx\" OR \"Fiduciary Exchange\" AND (Insurance OR Annuities)"),
    ("EXL", "\"EXL Service\" AND (Insurance OR Annuities)"),
    ("Hexure", "\"Hexure\" AND (Insurance OR Annuities)"),
    ("iCapital", "\"iCapital\" AND (Financial OR Investment)"),
    ("iPipeline", "\"iPipeline\" AND (Insurance OR Annuities)"),
    ("Infosys", "\"Infosys\" AND (Insurance OR Annuities)"),
    ("LIDP", "\"LIDP Consulting\" OR \"LIDP\" AND (Insurance OR \"Policy Administration\")"),
    ("Majesco", "\"Majesco\" AND (Insurance OR \"Policy Administration\")"),
    ("LUMA", "\"LUMA Financial\" AND (Annuities)"),
    ("Sapiens", "\"Sapiens\" AND (Insurance OR Annuities)"),
    ("Sureify", "\"Sureify\" AND (Insurance OR \"Annuities\")"),
    ("Verisk", "\"Verisk\" AND Insurance")
]

# Get client name from the client tuple
def get_client_name(client_tuple):
    """Extract client name from client tuple"""
    return client_tuple[0] if isinstance(client_tuple, tuple) else client_tuple

# Get search query from the client tuple
def get_search_query(client_tuple):
    """Extract search query from client tuple"""
    if isinstance(client_tuple, tuple) and len(client_tuple) > 1:
        return client_tuple[1] or client_tuple[0]
    return client_tuple

def search_news(query, max_results=10, time_filter='m', attempt=1):
    """
    Search for news articles using DuckDuckGo
    
    Args:
        query (str): The search query
        max_results (int): Maximum number of results to return
        time_filter (str): Time filter for results (d/w/m/y/None)
        attempt (int): Current attempt number for retries
        
    Returns:
        list: A list of news article dictionaries
    """
    results = []
    
    # List of rate limit indicator strings
    rate_limit_indicators = [
        "rate limit", 
        "too many requests", 
        "429", 
        "throttl",
        "blocked",
        "denied",
        "limit exceeded",
        "try again later"
    ]
    
    try:
        # For version 8.x, the parameter is timelimit
        with DDGS() as ddgs:
            for r in ddgs.news(query, max_results=max_results, timelimit=time_filter):
                results.append(r)
                
    except Exception as e:
        error_msg = str(e).lower()
        print(f"Error searching for '{query}': {e}")
        
        # Check if the error is related to rate limiting
        is_rate_limit = any(indicator in error_msg for indicator in rate_limit_indicators)
        
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
                return search_news(query, max_results, time_filter, attempt + 1)
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
            is_rate_limit2 = any(indicator in error_msg2 for indicator in rate_limit_indicators)
            
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

def get_adaptive_parameters(entity_tuple):
    """
    Determine optimal search parameters based on entity profile
    For weekly summaries, we always use the week time period but vary the result count
    """
    entity_name = get_client_name(entity_tuple)
    
    # Always use weekly time period for the weekly summary
    time_period = WEEKLY_TIME_PERIOD
    
    # Adjust the number of results based on entity profile
    if any(high in entity_name for high in high_profile):
        return time_period, HIGH_PROFILE_RESULT_COUNT  # Fewer results for high-profile entities
    elif any(low in entity_name for low in low_profile):
        return time_period, LOW_PROFILE_RESULT_COUNT  # More results for low-profile entities
    else:
        return time_period, DEFAULT_RESULT_COUNT  # Default for others

def collect_news_for_batches(entity_list, batch_size=BATCH_SIZE, use_adaptive=True, entity_type="client"):
    """Collect weekly news for all entities (clients or competitors) in batches"""
    all_news = {}
    
    # Calculate number of batches
    num_batches = (len(entity_list) + batch_size - 1) // batch_size
    
    print(f"Collecting weekly news for {len(entity_list)} {entity_type}s in {num_batches} batches")
    print(f"Using {DELAY_BETWEEN_REQUESTS} second delay between requests to avoid rate limits")
    print("=" * 50)
    
    for batch_idx in range(num_batches):
        start_idx = batch_idx * batch_size
        end_idx = min(start_idx + batch_size, len(entity_list))
        
        print(f"\nBatch {batch_idx + 1}/{num_batches}: Processing {entity_type}s {start_idx} to {end_idx - 1}")
        
        # Get entities for this batch
        batch_entities = entity_list[start_idx:end_idx]
        
        for entity_tuple in batch_entities:
            entity_name = get_client_name(entity_tuple)  # Reusing the client name function
            search_query = get_search_query(entity_tuple)  # Reusing the search query function
            
            # Determine search parameters (adaptive or fixed)
            if use_adaptive:
                time_filter, max_results = get_adaptive_parameters(entity_tuple)
                
                # Determine profile type based on result count
                if max_results == HIGH_PROFILE_RESULT_COUNT:
                    profile_type = "high-profile (more results)"
                elif max_results == LOW_PROFILE_RESULT_COUNT:
                    profile_type = "low-profile (more results)"
                else:
                    profile_type = "medium-profile (standard results)"
                    
                print(f"Searching weekly news for {entity_name} ({profile_type})...")
                print(f"  → Query: {search_query}")
                print(f"  → Time period: {time_descriptions.get(time_filter)}, Max results: {max_results}")
            else:
                # For non-adaptive, use the weekly time period with default result count
                time_filter, max_results = WEEKLY_TIME_PERIOD, DEFAULT_RESULT_COUNT
                print(f"Searching weekly news for {entity_name}...")
                print(f"  → Query: {search_query}")
                print(f"  → Time period: {time_descriptions.get(time_filter)}, Max results: {max_results}")
            
            # Search for news
            results = search_news(search_query, max_results=max_results, time_filter=time_filter)
            all_news[entity_name] = results
            
            # Show how many results were found
            num_results = len(all_news[entity_name])
            if num_results == 0:
                print(f"  → No results found for {entity_name}")
            else:
                print(f"  → Found {num_results} articles")
            
            # Add variable delay with jitter to avoid rate limits
            if not (entity_tuple == batch_entities[-1] and batch_idx == num_batches - 1):
                # Add jitter (±20%) to the delay to avoid pattern detection
                jitter = DELAY_BETWEEN_REQUESTS * 0.2 * (2 * random.random() - 1)
                delay = max(1, DELAY_BETWEEN_REQUESTS + jitter)
                
                # Adjust delay based on profiles (slower for high-profile companies)
                if any(high in entity_name for high in high_profile):
                    delay *= 1.5  # 50% longer delay for high-profile companies
                
                print(f"  → Waiting {delay:.1f} seconds before next request...")
                time.sleep(delay)
    
    print("=" * 50)
    print(f"Done! Collected weekly news for {len(entity_list)} {entity_type}s")
    print(f"Total articles found: {sum(len(articles) for articles in all_news.values())}")
    
    return all_news

def calculate_relevance_score(title, excerpt, entity_name):
    """
    Calculate a relevance score for an article based on how central the entity is to the content.
    
    Args:
        title (str): The article title
        excerpt (str): The article excerpt or body
        entity_name (str): The entity name to check for
        
    Returns:
        float: A relevance score between 0 and 1
    """
    # Convert all to lowercase for case-insensitive matching
    title_lower = title.lower()
    excerpt_lower = excerpt.lower()
    
    # Extract the main part of the entity name (remove "Inc.", "& Co.", etc.)
    main_entity_parts = entity_name.split(',')[0].strip()
    main_entity = main_entity_parts.split('&')[0].strip()
    
    # Generate variations of the entity name
    entity_variations = [
        entity_name.lower(),
        main_entity.lower()
    ]
    
    # Add additional common variations for specific entities
    if "J.P. Morgan" in entity_name:
        entity_variations.extend(["jpmorgan", "jp morgan", "j.p. morgan"])
    elif "Legal & General" in entity_name:
        entity_variations.extend(["legal and general", "l&g"])
    
    # Base score components
    title_score = 0
    excerpt_score = 0
    position_score = 0
    
    # Check title (high importance)
    for variation in entity_variations:
        if variation in title_lower:
            title_score = 0.6
            # Higher score if entity is at the beginning of the title
            if title_lower.find(variation) < len(title_lower) // 3:
                title_score = 0.7
            break
    
    # Check excerpt (lower importance)
    for variation in entity_variations:
        if variation in excerpt_lower:
            excerpt_score = 0.3
            # Calculate position - higher score if entity appears earlier
            position = excerpt_lower.find(variation)
            if position < len(excerpt_lower) // 4:  # In the first quarter
                position_score = 0.2
            elif position < len(excerpt_lower) // 2:  # In the first half
                position_score = 0.1
            break
    
    # Calculate final score
    final_score = title_score + excerpt_score + position_score
    
    # Cap at 1.0
    return min(final_score, 1.0)

def filter_relevant_articles(news_dict, min_relevance=0.5):
    """
    Filter articles based on their relevance to the entity.
    
    Args:
        news_dict (dict): Dictionary mapping entity names to lists of articles
        min_relevance (float): Minimum relevance score threshold (0-1)
        
    Returns:
        dict: Filtered dictionary with only relevant articles
    """
    filtered_news = {}
    
    for entity, articles in news_dict.items():
        relevant_articles = []
        
        for article in articles:
            title = article.get('title', '')
            excerpt = article.get('body', '')
            
            # Calculate relevance score
            relevance = calculate_relevance_score(title, excerpt, entity)
            
            # Add relevance score to article
            article['relevance'] = relevance
            
            # Keep only articles with sufficient relevance
            if relevance >= min_relevance:
                relevant_articles.append(article)
        
        # Ensure we have at least one article per entity
        if not relevant_articles and articles:
            # If no articles meet the threshold but we have articles,
            # take the most relevant one
            most_relevant = max(articles, key=lambda x: calculate_relevance_score(
                x.get('title', ''), x.get('body', ''), entity
            ))
            relevant_articles.append(most_relevant)
        
        filtered_news[entity] = relevant_articles
    
    return filtered_news

def convert_to_dataframe(news_dict):
    """Convert news dictionary to DataFrame with proper formatting"""
    # First, filter for relevant articles
    filtered_news = filter_relevant_articles(news_dict)
    
    news_data = []
    
    for client, articles in filtered_news.items():
        for article in articles:
            article_info = {
                'client': client,
                'title': article.get('title', ''),
                'url': article.get('url', ''),
                'date': article.get('date', ''),
                'source': article.get('source', ''),
                'excerpt': article.get('body', ''),  # Using 'body' instead of 'excerpt'
                'image': article.get('image', ''),
                'relevance': article.get('relevance', 0.0)  # Include the relevance score
            }
            news_data.append(article_info)
    
    news_df = pd.DataFrame(news_data)
    
    # Basic cleaning
    if not news_df.empty:
        # Convert date strings to datetime objects if possible
        try:
            # First convert to pandas datetime
            news_df['date'] = pd.to_datetime(news_df['date'])
            
            # Then standardize by converting all to UTC and then removing timezone
            if hasattr(news_df['date'].dt, 'tz'):
                # Convert all to UTC first
                news_df['date'] = news_df['date'].dt.tz_convert('UTC')
                # Then remove timezone info for consistent comparison
                news_df['date'] = news_df['date'].dt.tz_localize(None)
        except Exception as e:
            print(f"Date conversion issue: {e}")
        
        # Sort by client and relevance score (primary) and date (secondary)
        try:
            news_df = news_df.sort_values(['client', 'relevance', 'date'], ascending=[True, False, False])
        except:
            try:
                news_df = news_df.sort_values(['client', 'relevance'], ascending=[True, False])
            except:
                news_df = news_df.sort_values('client')
    
    return news_df

def save_to_csv(df, timestamp=None, entity_type="client"):
    """Save DataFrame to CSV with timestamp and update latest_csv.txt"""
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Generate filename based on entity_type
    csv_filename = f"data/{entity_type}_news_{timestamp}.csv"
    
    # Save to CSV
    df.to_csv(csv_filename, index=False)
    
    # Keep track of the most recent CSV file
    latest_csv_file = f"data/latest_{entity_type}_csv.txt"
    with open(latest_csv_file, "w") as f:
        f.write(csv_filename)
    
    print(f"News data saved to {csv_filename}")
    print(f"Total articles: {len(df)}")
    print(f"Companies covered: {df['client'].nunique()}")
    print(f"Latest CSV file path saved to {latest_csv_file}")
    
    return csv_filename

def main(target_type="clients", use_adaptive=True):
    """
    Main function to run the weekly news collection pipeline
    
    Args:
        target_type (str): Type of entities to collect news for - "clients", "competitors", or "both"
        use_adaptive (bool): Whether to use adaptive search parameters
    """
    print(f"Starting weekly news collection for {target_type}...")
    
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_files = []
        
        # Collect news for clients if requested
        if target_type in ["clients", "both"]:
            print("\n" + "="*50)
            print("COLLECTING WEEKLY CLIENT NEWS")
            print("="*50)
            
            # Collect news for all clients
            client_news = collect_news_for_batches(clients, use_adaptive=use_adaptive, entity_type="client")
            
            # Convert to DataFrame
            client_news_df = convert_to_dataframe(client_news)
            
            # Save to CSV
            client_csv = save_to_csv(client_news_df, timestamp, entity_type="client")
            csv_files.append(client_csv)
        
        # Collect news for competitors if requested
        if target_type in ["competitors", "both"]:
            print("\n" + "="*50)
            print("COLLECTING WEEKLY COMPETITOR NEWS")
            print("="*50)
            
            # Collect news for all competitors
            competitor_news = collect_news_for_batches(competitors, use_adaptive=use_adaptive, entity_type="competitor")
            
            # Convert to DataFrame
            competitor_news_df = convert_to_dataframe(competitor_news)
            
            # Save to CSV
            competitor_csv = save_to_csv(competitor_news_df, timestamp, entity_type="competitor")
            csv_files.append(competitor_csv)
        
        # Create combined weekly file for both if applicable
        if target_type == "both":
            print("\n" + "="*50)
            print("CREATING COMBINED WEEKLY NEWS FILE")
            print("="*50)
            
            # Combine client and competitor dataframes
            combined_df = pd.concat([client_news_df, competitor_news_df])
            
            # Save to CSV with special weekly prefix
            combined_csv = save_to_csv(combined_df, timestamp, entity_type="weekly")
            csv_files.append(combined_csv)
            
            print(f"Combined weekly news saved to {combined_csv}")
            print(f"Total entities: {combined_df['client'].nunique()}")
            print(f"Total articles: {len(combined_df)}")
        
        print("\nWeekly news collection completed successfully!")
        return csv_files
        
    except Exception as e:
        print(f"Error in news collection: {e}")
        return None

if __name__ == "__main__":
    import argparse
    
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description="Collect news for clients and competitors")
    parser.add_argument("--target", choices=["clients", "competitors", "both"], 
                        default="clients", help="Type of entities to collect news for")
    parser.add_argument("--no-adaptive", action="store_false", dest="adaptive",
                        help="Disable adaptive search parameters")
    
    args = parser.parse_args()
    
    # Run main function with parsed arguments
    main(target_type=args.target, use_adaptive=args.adaptive)