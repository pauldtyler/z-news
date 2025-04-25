#!/usr/bin/env python
"""
Comprehensive News Collector

This script collects news for clients, competitors, and industry topics in batches,
with proper rate limiting and error handling, then saves the results to CSV files.
"""

import pandas as pd
from datetime import datetime
import time
import os
import json
import random

from dotenv import load_dotenv
from typing import Dict, List, Tuple, Any, Optional, Union

# Import from local modules
from config.config import (
    BATCH_SIZE, WEEKLY_TIME_PERIOD, DELAY_BETWEEN_REQUESTS,
    DEFAULT_RESULT_COUNT, HIGH_PROFILE_RESULT_COUNT, LOW_PROFILE_RESULT_COUNT,
    TOPIC_RESULT_COUNT, TIME_DESCRIPTIONS, HIGH_PROFILE_ENTITIES, LOW_PROFILE_ENTITIES
)
from services import SearchService
from utils import (
    load_entities, convert_entities_to_tuples,
    get_entity_name, get_entity_query, get_topic_category,
    add_jitter, generate_timestamp, save_latest_file_reference
)

# Load environment variables
load_dotenv()

# Create data directory if it doesn't exist
if not os.path.exists('data'):
    os.makedirs('data')


def get_adaptive_parameters(entity_tuple):
    """
    Determine optimal search parameters based on entity profile
    For weekly summaries, we always use the week time period but vary the result count
    """
    entity_name = get_entity_name(entity_tuple)
    
    # Always use weekly time period for the weekly summary
    time_period = WEEKLY_TIME_PERIOD
    
    # Adjust the number of results based on entity profile
    if any(high in entity_name for high in HIGH_PROFILE_ENTITIES):
        return time_period, HIGH_PROFILE_RESULT_COUNT
    elif any(low in entity_name for low in LOW_PROFILE_ENTITIES):
        return time_period, LOW_PROFILE_RESULT_COUNT
    else:
        return time_period, DEFAULT_RESULT_COUNT


def collect_news_for_batches(entity_list, batch_size=BATCH_SIZE, use_adaptive=True, entity_type="client"):
    """Collect weekly news for all entities (clients, competitors, or topics) in batches"""
    all_news = {}
    search_service = SearchService()
    
    # Calculate number of batches
    num_batches = (len(entity_list) + batch_size - 1) // batch_size
    
    # Use correct entity type name for output messages
    entity_type_display = entity_type
    if entity_type == "topic":
        entity_type_display = "industry topics"
    else:
        entity_type_display = f"{entity_type}s"
    
    print(f"Collecting weekly news for {len(entity_list)} {entity_type_display} in {num_batches} batches")
    print(f"Using {DELAY_BETWEEN_REQUESTS} second delay between requests to avoid rate limits")
    print("=" * 50)
    
    for batch_idx in range(num_batches):
        start_idx = batch_idx * batch_size
        end_idx = min(start_idx + batch_size, len(entity_list))
        
        print(f"\nBatch {batch_idx + 1}/{num_batches}: Processing {entity_type_display} {start_idx} to {end_idx - 1}")
        
        # Get entities for this batch
        batch_entities = entity_list[start_idx:end_idx]
        
        for entity_tuple in batch_entities:
            # Get entity information (works for clients, competitors, and topics)
            if entity_type == "topic":
                # For topics, use the second element (topic name) as the entity name
                entity_name = entity_tuple[1] if isinstance(entity_tuple, tuple) and len(entity_tuple) > 1 else entity_tuple
                # Also get the category
                category = get_topic_category(entity_tuple)
                # Store category with the entity name for later use
                full_entity_name = f"{category}: {entity_name}"
            else:
                # For clients and competitors, use the first element
                entity_name = get_entity_name(entity_tuple)
                full_entity_name = entity_name
            
            # Get the search query
            search_query = get_entity_query(entity_tuple)
            
            # Determine search parameters (adaptive or fixed)
            if use_adaptive and entity_type != "topic":
                # Only use adaptive parameters for clients and competitors, not topics
                time_filter, max_results = get_adaptive_parameters(entity_tuple)
                
                # Determine profile type based on result count
                if max_results == HIGH_PROFILE_RESULT_COUNT:
                    profile_type = "high-profile (more results)"
                elif max_results == LOW_PROFILE_RESULT_COUNT:
                    profile_type = "low-profile (more results)"
                else:
                    profile_type = "medium-profile (standard results)"
                    
                print(f"Searching weekly news for {full_entity_name} ({profile_type})...")
                print(f"  → Query: {search_query}")
                print(f"  → Time period: {TIME_DESCRIPTIONS.get(time_filter)}, Max results: {max_results}")
            else:
                # For topics or non-adaptive, use the weekly time period with fixed result count
                time_filter = WEEKLY_TIME_PERIOD
                # Use more results for industry topics to capture broader trends
                max_results = TOPIC_RESULT_COUNT if entity_type == "topic" else DEFAULT_RESULT_COUNT
                
                print(f"Searching weekly news for {full_entity_name}...")
                print(f"  → Query: {search_query}")
                print(f"  → Time period: {TIME_DESCRIPTIONS.get(time_filter)}, Max results: {max_results}")
            
            # Search for news
            results = search_service.search_news(search_query, max_results=max_results, time_filter=time_filter)
            
            # Store results under the full entity name (includes category for topics)
            all_news[full_entity_name] = results
            
            # Show how many results were found
            num_results = len(all_news[full_entity_name])
            if num_results == 0:
                print(f"  → No results found for {full_entity_name}")
            else:
                print(f"  → Found {num_results} articles")
            
            # Add variable delay with jitter to avoid rate limits
            if not (entity_tuple == batch_entities[-1] and batch_idx == num_batches - 1):
                # Add jitter (±20%) to the delay to avoid pattern detection
                delay = add_jitter(DELAY_BETWEEN_REQUESTS, 0.2)
                
                # Adjust delay based on entity type
                if entity_type != "topic" and any(high in entity_name for high in HIGH_PROFILE_ENTITIES):
                    delay *= 1.5  # 50% longer delay for high-profile companies
                
                print(f"  → Waiting {delay:.1f} seconds before next request...")
                time.sleep(delay)
    
    print("=" * 50)
    print(f"Done! Collected weekly news for {len(entity_list)} {entity_type_display}")
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
    main_entity = main_entity.split(':')[-1].strip()  # Handle topic format "Category: Topic"
    
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
        timestamp = generate_timestamp()
    
    # Generate filename based on entity_type
    csv_filename = f"data/{entity_type}_news_{timestamp}.csv"
    
    # Save to CSV
    df.to_csv(csv_filename, index=False)
    
    # Keep track of the most recent CSV file
    save_latest_file_reference(csv_filename, entity_type)
    
    print(f"News data saved to {csv_filename}")
    print(f"Total articles: {len(df)}")
    print(f"Companies covered: {df['client'].nunique()}")
    
    return csv_filename


def main(target_type="clients", use_adaptive=True):
    """
    Main function to run the weekly news collection pipeline
    
    Args:
        target_type (str): Type of entities to collect news for - "clients", "competitors", "topics", "all"
        use_adaptive (bool): Whether to use adaptive search parameters
    """
    print(f"Starting weekly news collection for {target_type}...")
    
    try:
        timestamp = generate_timestamp()
        csv_files = []
        dataframes = {}
        
        # Load entity data from configuration files
        clients_data = load_entities("client")
        competitors_data = load_entities("competitor")
        topics_data = load_entities("topic")
        
        # Convert to tuple format for backward compatibility
        clients = convert_entities_to_tuples(clients_data, "client")
        competitors = convert_entities_to_tuples(competitors_data, "competitor")
        topics = convert_entities_to_tuples(topics_data, "topic")
        
        # Collect news for clients if requested
        if target_type in ["clients", "both", "all"]:
            print("\n" + "="*50)
            print("COLLECTING WEEKLY CLIENT NEWS")
            print("="*50)
            
            # Collect news for all clients
            client_news = collect_news_for_batches(clients, use_adaptive=use_adaptive, entity_type="client")
            
            # Convert to DataFrame
            client_news_df = convert_to_dataframe(client_news)
            dataframes["client"] = client_news_df
            
            # Save to CSV
            client_csv = save_to_csv(client_news_df, timestamp, entity_type="client")
            csv_files.append(client_csv)
        
        # Collect news for competitors if requested
        if target_type in ["competitors", "both", "all"]:
            print("\n" + "="*50)
            print("COLLECTING WEEKLY COMPETITOR NEWS")
            print("="*50)
            
            # Collect news for all competitors
            competitor_news = collect_news_for_batches(competitors, use_adaptive=use_adaptive, entity_type="competitor")
            
            # Convert to DataFrame
            competitor_news_df = convert_to_dataframe(competitor_news)
            dataframes["competitor"] = competitor_news_df
            
            # Save to CSV
            competitor_csv = save_to_csv(competitor_news_df, timestamp, entity_type="competitor")
            csv_files.append(competitor_csv)
        
        # Collect news for industry topics if requested
        if target_type in ["topics", "all"]:
            print("\n" + "="*50)
            print("COLLECTING WEEKLY INDUSTRY TOPIC NEWS")
            print("="*50)
            
            # Collect news for all industry topics
            topic_news = collect_news_for_batches(topics, use_adaptive=False, entity_type="topic")
            
            # Convert to DataFrame
            topic_news_df = convert_to_dataframe(topic_news)
            dataframes["topic"] = topic_news_df
            
            # Save to CSV
            topic_csv = save_to_csv(topic_news_df, timestamp, entity_type="topic")
            csv_files.append(topic_csv)
        
        # Create combined weekly file if applicable
        if target_type in ["both", "all"]:
            print("\n" + "="*50)
            print("CREATING COMBINED WEEKLY NEWS FILE")
            print("="*50)
            
            # Combine all available dataframes
            dfs_to_combine = list(dataframes.values())
            
            if dfs_to_combine:
                combined_df = pd.concat(dfs_to_combine)
                
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


def cleanup_intermediate_files(files_to_keep):
    """
    Clean up intermediate files, keeping only the specified files.
    
    Args:
        files_to_keep (list): List of file paths to keep
    """
    import os
    import glob
    
    print("\n" + "="*50)
    print("CLEANING UP INTERMEDIATE FILES")
    print("="*50)
    
    # Get all files in the data directory
    all_files = glob.glob("data/*")
    
    # Make sure files_to_keep contains absolute paths
    files_to_keep = [os.path.abspath(f) for f in files_to_keep]
    
    # Files to delete are those not in files_to_keep
    files_to_delete = []
    for file_path in all_files:
        abs_path = os.path.abspath(file_path)
        if abs_path not in files_to_keep and "_latest_" not in file_path:
            # Keep the latest_*.txt reference files
            if not (file_path.endswith('.txt') and 'latest' in file_path):
                files_to_delete.append(file_path)
    
    # Delete the files
    for file_path in files_to_delete:
        try:
            os.remove(file_path)
            print(f"Deleted: {file_path}")
        except Exception as e:
            print(f"Error deleting {file_path}: {e}")
    
    print(f"Cleanup complete. Deleted {len(files_to_delete)} intermediate files.")
    print(f"Kept {len(files_to_keep)} files.")


def get_previous_daily_news():
    """
    Get the most recent daily combined news data for deduplication.
    
    Returns:
        pd.DataFrame: DataFrame containing previous daily news, or empty DataFrame if not found
    """
    try:
        # Look for the previous daily combined CSV file
        previous_file_path = None
        
        # First, try to read from the reference file
        try:
            with open("data/latest_daily_combined_csv.txt", "r") as f:
                previous_file_path = f.read().strip()
                print(f"Found previous daily news file reference: {previous_file_path}")
        except FileNotFoundError:
            print("No reference file found for previous daily news")
        
        # If that fails, look for the most recent daily_combined CSV
        if not previous_file_path or not os.path.exists(previous_file_path):
            import glob
            csv_files = glob.glob("data/daily_combined_*.csv")
            if csv_files:
                previous_file_path = max(csv_files, key=os.path.getctime)
                print(f"Found previous daily news file by searching: {previous_file_path}")
        
        # Load the previous data if a file was found
        if previous_file_path and os.path.exists(previous_file_path):
            previous_df = pd.read_csv(previous_file_path)
            print(f"Loaded previous daily news data: {len(previous_df)} articles")
            return previous_df
        else:
            print("No previous daily news data found")
            return pd.DataFrame()  # Return empty DataFrame
            
    except Exception as e:
        print(f"Error loading previous daily news: {e}")
        return pd.DataFrame()  # Return empty DataFrame on error


def remove_duplicate_news(current_df, previous_df):
    """
    Remove duplicate news articles from the current DataFrame based on previous data.
    
    Args:
        current_df (pd.DataFrame): The current daily news DataFrame
        previous_df (pd.DataFrame): The previous daily news DataFrame
        
    Returns:
        pd.DataFrame: DataFrame with duplicates removed
    """
    if previous_df.empty or current_df.empty:
        print("No previous data or current data to deduplicate")
        return current_df
    
    print(f"Checking {len(current_df)} current articles against {len(previous_df)} previous articles")
    
    # Create a unique identifier for each article based on title and URL
    # This helps identify the same article even if some metadata changed
    def create_id(row):
        # Use title and url to create a unique identifier
        title = str(row.get('title', '')).strip().lower()
        url = str(row.get('url', '')).strip().lower()
        
        # For URLs, remove any tracking parameters or fragments
        if '?' in url:
            url = url.split('?')[0]
        if '#' in url:
            url = url.split('#')[0]
            
        # Combine title and URL for a more robust identifier
        return f"{title}|{url}"
    
    # Add identifiers to both DataFrames
    current_df['article_id'] = current_df.apply(create_id, axis=1)
    previous_df['article_id'] = previous_df.apply(create_id, axis=1)
    
    # Get the set of previous article IDs
    previous_ids = set(previous_df['article_id'])
    
    # Filter out duplicates
    duplicate_mask = current_df['article_id'].isin(previous_ids)
    duplicates_count = duplicate_mask.sum()
    
    # Get the deduplicated DataFrame
    deduplicated_df = current_df[~duplicate_mask].copy()
    
    # Remove the temporary column
    deduplicated_df.drop('article_id', axis=1, inplace=True)
    
    print(f"Removed {duplicates_count} duplicate articles")
    print(f"Remaining articles after deduplication: {len(deduplicated_df)}")
    
    return deduplicated_df


def collect_daily_news_with_summary():
    """
    Collect the prior day's news for clients and competitors, then generate a single 
    markdown summary using Claude API.
    
    This specialized function:
    1. Uses the 'd' (day) time period instead of weekly
    2. Only searches for clients and competitors (not industry topics)
    3. Generates a single combined summary directly
    4. Cleans up intermediate files, keeping only the combined CSV and markdown summary
    5. Removes duplicate news articles by comparing with previous daily summaries
    
    Returns:
        str: Path to the generated markdown summary file
    """
    print("Starting daily news collection and summary process...")
    
    try:
        timestamp = generate_timestamp()
        
        # Override the weekly time period with daily
        daily_time_period = 'd'
        
        # Load entity data from configuration files
        clients_data = load_entities("client")
        competitors_data = load_entities("competitor")
        
        # Convert to tuple format for backward compatibility
        clients = convert_entities_to_tuples(clients_data, "client")
        competitors = convert_entities_to_tuples(competitors_data, "competitor")
        
        all_news = {}
        dataframes = {}
        
        # Collect daily news for clients
        print("\n" + "="*50)
        print("COLLECTING DAILY CLIENT NEWS")
        print("="*50)
        
        # Create search service
        search_service = SearchService()
        
        # Process clients
        for entity_tuple in clients:
            entity_name = get_entity_name(entity_tuple)
            search_query = get_entity_query(entity_tuple)
            
            # Determine result count based on profile
            if any(high in entity_name for high in HIGH_PROFILE_ENTITIES):
                max_results = HIGH_PROFILE_RESULT_COUNT
            elif any(low in entity_name for low in LOW_PROFILE_ENTITIES):
                max_results = LOW_PROFILE_RESULT_COUNT
            else:
                max_results = DEFAULT_RESULT_COUNT
                
            print(f"Searching daily news for {entity_name}...")
            print(f"  → Query: {search_query}")
            print(f"  → Time period: {TIME_DESCRIPTIONS.get(daily_time_period)}, Max results: {max_results}")
            
            # Search for news using daily time period
            results = search_service.search_news(search_query, max_results=max_results, time_filter=daily_time_period)
            
            # Store results
            all_news[entity_name] = results
            
            # Show how many results were found
            num_results = len(results)
            if num_results == 0:
                print(f"  → No results found for {entity_name}")
            else:
                print(f"  → Found {num_results} articles")
            
            # Add delay with jitter to avoid rate limits
            if entity_tuple != clients[-1]:
                delay = add_jitter(DELAY_BETWEEN_REQUESTS, 0.2)
                # Adjust delay based on entity profile
                if any(high in entity_name for high in HIGH_PROFILE_ENTITIES):
                    delay *= 1.5
                print(f"  → Waiting {delay:.1f} seconds before next request...")
                time.sleep(delay)
        
        # Convert client news to DataFrame
        client_news_df = convert_to_dataframe(all_news)
        dataframes["client"] = client_news_df
        
        # Save client news to CSV
        client_csv = save_to_csv(client_news_df, timestamp, entity_type="client_daily")
        
        # Reset all_news dictionary for competitors
        all_news = {}
        
        # Collect daily news for competitors
        print("\n" + "="*50)
        print("COLLECTING DAILY COMPETITOR NEWS")
        print("="*50)
        
        # Process competitors
        for entity_tuple in competitors:
            entity_name = get_entity_name(entity_tuple)
            search_query = get_entity_query(entity_tuple)
            
            # Determine result count based on profile
            if any(high in entity_name for high in HIGH_PROFILE_ENTITIES):
                max_results = HIGH_PROFILE_RESULT_COUNT
            elif any(low in entity_name for low in LOW_PROFILE_ENTITIES):
                max_results = LOW_PROFILE_RESULT_COUNT
            else:
                max_results = DEFAULT_RESULT_COUNT
                
            print(f"Searching daily news for {entity_name}...")
            print(f"  → Query: {search_query}")
            print(f"  → Time period: {TIME_DESCRIPTIONS.get(daily_time_period)}, Max results: {max_results}")
            
            # Search for news using daily time period
            results = search_service.search_news(search_query, max_results=max_results, time_filter=daily_time_period)
            
            # Store results
            all_news[entity_name] = results
            
            # Show how many results were found
            num_results = len(results)
            if num_results == 0:
                print(f"  → No results found for {entity_name}")
            else:
                print(f"  → Found {num_results} articles")
            
            # Add delay with jitter to avoid rate limits
            if entity_tuple != competitors[-1]:
                delay = add_jitter(DELAY_BETWEEN_REQUESTS, 0.2)
                # Adjust delay based on entity profile
                if any(high in entity_name for high in HIGH_PROFILE_ENTITIES):
                    delay *= 1.5
                print(f"  → Waiting {delay:.1f} seconds before next request...")
                time.sleep(delay)
        
        # Convert competitor news to DataFrame
        competitor_news_df = convert_to_dataframe(all_news)
        dataframes["competitor"] = competitor_news_df
        
        # Save competitor news to CSV
        competitor_csv = save_to_csv(competitor_news_df, timestamp, entity_type="competitor_daily")
        
        # Combine dataframes
        if not client_news_df.empty or not competitor_news_df.empty:
            dfs_to_combine = [df for df in dataframes.values() if not df.empty]
            combined_df = pd.concat(dfs_to_combine) if dfs_to_combine else pd.DataFrame()
            
            # Get previous daily news for deduplication
            print("\n" + "="*50)
            print("CHECKING FOR DUPLICATE NEWS ARTICLES")
            print("="*50)
            previous_df = get_previous_daily_news()
            
            # Remove duplicate news articles
            if not previous_df.empty:
                combined_df = remove_duplicate_news(combined_df, previous_df)
            
            # Save combined data
            combined_csv = save_to_csv(combined_df, timestamp, entity_type="daily_combined")
            
            print("\n" + "="*50)
            print("GENERATING DAILY NEWS SUMMARY")
            print("="*50)
            
            # Generate executive summary using Claude API
            from services import ClaudeApiClient
            from datetime import datetime
            
            # We already have the client and competitor data loaded
            # Extract names from the already loaded data
            client_names = set(c.get('name', '') for c in clients_data)
            competitor_names = set(c.get('name', '') for c in competitors_data)
            
            # Create data for the prompt with proper structure
            data_for_claude = {"clients": {}, "competitors": {}}
            
            for entity, df_group in combined_df.groupby('client'):
                # Determine if this is a client or competitor
                entity_type = "clients" if entity in client_names else "competitors"
                
                articles = []
                for _, row in df_group.iterrows():
                    # Convert Timestamp to string if needed
                    date_value = row.get('date', '')
                    if hasattr(date_value, 'strftime'):  # Check if it's a datetime-like object
                        date_str = date_value.strftime('%Y-%m-%d')
                    else:
                        date_str = str(date_value)
                        
                    article = {
                        'title': row.get('title', ''),
                        'date': date_str,
                        'source': row.get('source', ''),
                        'excerpt': row.get('excerpt', ''),
                        'url': row.get('url', '')
                    }
                    articles.append(article)
                
                # Add to the appropriate section
                data_for_claude[entity_type][entity] = articles
                
            # Print counts
            print(f"Categorized {len(data_for_claude['clients'])} clients and {len(data_for_claude['competitors'])} competitors")
            
            # Format data as JSON string
            import json
            json_data = json.dumps(data_for_claude, indent=2)
            
            # Create the prompt for Claude
            from templates import COMBINED_REPORT_HEADER
            
            prompt = f"""## Daily Financial Services News Summary
            
            Create a concise daily executive news summary for financial service clients and competitors. These summaries will be provided to executives who develop software and back office services for financial service companies.
            
            Your output must be direct, factual, and focused on the most important news from the past day.
            
            ### Instructions:
            
            1. Create a markdown document with the title "Daily Financial Services News Summary" and today's date.
            
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
            {json_data}
            """
            
            # Call Claude API
            claude_client = ClaudeApiClient()
            system_prompt = 'You are an expert financial analyst creating executive summaries for the financial services industry.'
            summary = claude_client.generate_summary(prompt, system_prompt)
            
            if summary:
                # Save summary to markdown file
                summary_filename = f"data/daily_summary_{timestamp}.md"
                with open(summary_filename, 'w') as f:
                    f.write(summary)
                
                print(f"Daily news summary saved to: {summary_filename}")
                
                # Keep only the combined CSV and the summary markdown file
                files_to_keep = [os.path.abspath(combined_csv), os.path.abspath(summary_filename)]
                cleanup_intermediate_files(files_to_keep)
                
                return summary_filename
            else:
                print("Failed to generate summary")
                return combined_csv
        else:
            print("No articles found for daily summary")
            return None
        
    except Exception as e:
        print(f"Error in daily news collection: {e}")
        return None


if __name__ == "__main__":
    import argparse
    
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description="Collect news for clients, competitors, and industry topics")
    parser.add_argument("--target", choices=["clients", "competitors", "topics", "both", "all"], 
                        default="clients", help="Type of entities to collect news for (both=clients+competitors, all=clients+competitors+topics)")
    parser.add_argument("--no-adaptive", action="store_false", dest="adaptive",
                        help="Disable adaptive search parameters")
    parser.add_argument("--daily", action="store_true", 
                        help="Collect only the prior day's news for clients and competitors and generate a single summary")
    
    args = parser.parse_args()
    
    if args.daily:
        # Run the specialized daily collection function 
        collect_daily_news_with_summary()
    else:
        # Run normal weekly collection function
        main(target_type=args.target, use_adaptive=args.adaptive)