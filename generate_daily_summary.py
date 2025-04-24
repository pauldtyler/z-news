#!/usr/bin/env python
"""
Generate Daily Summary

This script generates a daily news summary from an existing CSV file without rerunning the search.
"""

import pandas as pd
import os
import json
from datetime import datetime
import glob

from services import ClaudeApiClient
from config.config import MODEL, MAX_TOKENS


def load_entity_lists():
    """Load client and competitor lists from config files"""
    # Load client list
    with open("config/clients.json", "r") as f:
        clients_data = json.load(f)
    client_names = [client["name"] for client in clients_data]
    
    # Load competitor list
    with open("config/competitors.json", "r") as f:
        competitors_data = json.load(f)
    competitor_names = [competitor["name"] for competitor in competitors_data]
    
    return set(client_names), set(competitor_names)


def generate_summary_from_csv(csv_path):
    """Generate a daily news summary from an existing CSV file"""
    
    print(f"Loading data from {csv_path}...")
    
    # Read the CSV file
    df = pd.read_csv(csv_path)
    
    print(f"Found {len(df)} articles for {df['client'].nunique()} companies")
    
    # Load client and competitor lists
    client_names, competitor_names = load_entity_lists()
    
    # Create data for the prompt, separating clients and competitors
    data_for_claude = {"clients": {}, "competitors": {}}
    
    for entity, df_group in df.groupby('client'):
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
    
    # Count companies in each category
    client_count = len(data_for_claude["clients"])
    competitor_count = len(data_for_claude["competitors"])
    print(f"Categorized {client_count} clients and {competitor_count} competitors")
    
    # Format data as JSON string
    json_data = json.dumps(data_for_claude, indent=2)
    
    # Create the prompt for Claude
    prompt = f"""## Daily Financial Services News Summary
    
    Create a concise daily executive news summary for financial service clients and competitors. These summaries will be provided to executives who develop software and back office services for financial service companies.
    
    Your output must be direct, factual, and focused on the most important news from the past day.
    
    ### Instructions:
    
    1. Create a markdown document with the title "Daily Financial Services News Summary" and today's date.
    
    2. Create two main sections:
       - "Client Companies" - for all companies in the "clients" object of the data
       - "Competitor Companies" - for all companies in the "competitors" object of the data
    
    3. Within each section, for each company with news, include a subsection header with the company name.
    
    4. Write a single paragraph (3-5 sentences) that summarizes the most significant recent news for each company.
    
    5. Each paragraph should:
       - Be direct and start immediately with the news
       - Include specific facts and figures when available
       - Only include news where the company plays a significant role
       - Focus on information relevant to software and service providers
    
    6. IMPORTANT: If the story is an analyst report written by the client about another company, please ignore it. Only include news about the client/competitor company itself, not reports or analysis they publish about other companies.
    
    7. Format the final output as a clean, professional markdown document.
    
    8. VERY IMPORTANT: Only include companies under their correct category as defined in the JSON data structure. Companies in the "clients" object should ONLY appear in the "Client Companies" section, and companies in the "competitors" object should ONLY appear in the "Competitor Companies" section.
    
    ### News Data:
    {json_data}
    """
    
    # Call Claude API
    print("Calling Claude API to generate summary...")
    claude_client = ClaudeApiClient()
    system_prompt = 'You are an expert financial analyst creating executive summaries for the financial services industry.'
    summary = claude_client.generate_summary(prompt, system_prompt)
    
    if summary:
        # Generate timestamp for the file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save summary to markdown file
        summary_filename = f"data/daily_summary_{timestamp}.md"
        with open(summary_filename, 'w') as f:
            f.write(summary)
        
        print(f"Daily news summary saved to: {summary_filename}")
        return summary_filename
    else:
        print("Failed to generate summary")
        return None


if __name__ == "__main__":
    import argparse
    
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description="Generate a daily news summary from an existing CSV file")
    parser.add_argument("--file", required=False, 
                       help="Path to the CSV file (if not specified, will use latest daily_combined CSV)")
    
    args = parser.parse_args()
    
    if args.file:
        csv_path = args.file
    else:
        # Try to read the latest_daily_combined_csv.txt file
        try:
            with open("data/latest_daily_combined_csv.txt", "r") as f:
                csv_path = f.read().strip()
            print(f"Using latest daily combined CSV: {csv_path}")
        except:
            # If that fails, look for the most recent daily_combined CSV in the data directory
            csv_files = glob.glob("data/daily_combined_*.csv")
            if csv_files:
                csv_path = max(csv_files, key=os.path.getctime)
                print(f"Using most recent daily combined CSV: {csv_path}")
            else:
                print("No daily combined CSV file found. Please specify a file with --file.")
                exit(1)
    
    generate_summary_from_csv(csv_path)