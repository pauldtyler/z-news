#!/usr/bin/env python
"""
Batch Executive Summary Generator

This script processes client or competitor news data from a CSV file and generates executive summaries
in batches using Claude API, then combines them into a single markdown file.
"""

import os
import json
import pandas as pd
from datetime import datetime
import time
from dotenv import load_dotenv
from anthropic import Anthropic

# Load environment variables from .env
load_dotenv()
API_KEY = os.getenv('ANTHROPIC_API_KEY')

# Make sure data directory exists
if not os.path.exists('data'):
    os.makedirs('data')

# Configuration
BATCH_SIZE = 5  # Number of clients per API call
MAX_TOKENS = 4000  # Max tokens for Claude response
MODEL = 'claude-3-sonnet-20240229'  # Claude model to use

def load_entity_news(csv_file, entity_type="client"):
    """Load news data from CSV and group by entity (client or competitor)"""
    if not os.path.exists(csv_file):
        raise FileNotFoundError(f"CSV file not found: {csv_file}")
    
    # Load the CSV data
    df = pd.read_csv(csv_file)
    
    # Get unique list of entities
    entities = df['client'].unique().tolist()
    print(f"Found {len(entities)} unique {entity_type}s in the data")
    
    # Group news by entity
    entity_news = {}
    for entity in entities:
        entity_df = df[df['client'] == entity]
        articles = []
        
        for _, row in entity_df.iterrows():
            article = {
                'title': row.get('title', ''),
                'date': row.get('date', ''),
                'source': row.get('source', ''),
                'excerpt': row.get('excerpt', ''),
                'url': row.get('url', '')
            }
            articles.append(article)
        
        entity_news[entity] = articles
    
    return entity_news, entities

def create_prompt_for_batch(entity_batch, entity_news, entity_type="client"):
    """Create a prompt for a batch of entities (clients or competitors)"""
    # Extract just the news for this batch of entities
    batch_news = {entity: entity_news[entity] for entity in entity_batch}
    
    # Determine prompt template based on entity type
    if entity_type == "client":
        title = "Client Executive News Summary"
        focus = "financial service clients"
    else:  # competitor
        title = "Competitor Executive News Summary"
        focus = "financial service competitors"
    
    # Prepare data for Claude API
    prompt_template = """## Executive News Summary Prompt Template

You are tasked with creating concise executive news summaries for {focus}. These summaries will be provided to executives who develop software and back office services for financial service companies. Your output must be direct, factual, and focused only on the most relevant news.

### Instructions:

1. Create a markdown document with the title "{title}" and today's date.

2. For each company, include a section header with the company name.

3. Write a single paragraph (3-5 sentences) that summarizes the most significant recent news for each company. Focus on:
   - Financial performance metrics
   - Leadership changes
   - New products or services
   - Major partnerships or transitions
   - Regulatory or legal developments
   - Facility changes or expansions
   - Technology initiatives or digital transformation efforts

4. Each paragraph should:
   - Be direct and start immediately with the news
   - Include specific facts and figures when available
   - Avoid commentary about the frequency of media mentions
   - Focus on items relevant to software and back office service providers
   - Omit subjective assessments or speculations
   - Only include news where the company plays a significant role (not just mentioned in passing)

5. Use clear, concise business language appropriate for C-suite executives.

6. Limit each company's summary to one paragraph regardless of the amount of news available.

7. Format the final output as a clean, professional markdown document.

8. IMPORTANT: For each company, discard any news articles where:
   - The company is only mentioned tangentially or in passing
   - The company is not a primary subject of the article
   - The article is about industry trends with only a minor reference to the company
   - The article primarily focuses on a different company and only mentions this company for context

### Example format:

```markdown
# {title}
[Current Date]

## [Company Name]
[Direct news summary in a single paragraph with key facts and developments relevant to software and back office service providers.]

## [Company Name]
[Direct news summary in a single paragraph with key facts and developments relevant to software and back office service providers.]
```

This summary will be used by executives to understand the current context of {focus} businesses and identify potential service opportunities or risks.

### News Data:
{news_data}
"""
    
    # Format the news data as JSON string
    news_data_str = json.dumps(batch_news, indent=2)
    prompt = prompt_template.format(
        focus=focus,
        title=title,
        news_data=news_data_str
    )
    
    return prompt

def call_claude_api(prompt, attempt=1, max_attempts=3):
    """Call Claude API with retries"""
    if not API_KEY:
        raise ValueError("No API key found. Please set ANTHROPIC_API_KEY in your .env file.")
    
    print('Calling Claude API to generate executive summary...')
    
    try:
        # Initialize Anthropic client
        client = Anthropic(api_key=API_KEY)
        
        # Call Claude API
        message = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            temperature=0.0,
            system='You are an expert financial analyst creating executive summaries.',
            messages=[
                {'role': 'user', 'content': prompt}
            ]
        )
        
        # Extract response
        summary = message.content[0].text
        return summary
        
    except Exception as e:
        print(f'Error calling Claude API (attempt {attempt}/{max_attempts}): {e}')
        if attempt < max_attempts:
            # Wait before retrying (exponential backoff)
            wait_time = 2 ** attempt
            print(f"Waiting {wait_time} seconds before retrying...")
            time.sleep(wait_time)
            return call_claude_api(prompt, attempt + 1, max_attempts)
        else:
            print("Max attempts reached. Giving up.")
            return None

def extract_client_sections(summary):
    """Extract individual client sections from a summary"""
    sections = {}
    
    # Split the summary into lines
    lines = summary.split('\n')
    
    current_client = None
    current_content = []
    
    for line in lines:
        if line.startswith('## '):
            # New client section
            if current_client:
                # Save previous client's content
                sections[current_client] = '\n'.join(current_content)
            
            # Start new client section
            current_client = line[3:].strip()
            current_content = [line]
        elif current_client:
            # Add line to current client's content
            current_content.append(line)
    
    # Save the last client's content
    if current_client:
        sections[current_client] = '\n'.join(current_content)
    
    return sections

def process_in_batches(entity_news, entities, entity_type="client", batch_size=BATCH_SIZE):
    """Process entities in batches"""
    all_sections = {}
    
    # Calculate number of batches
    num_batches = (len(entities) + batch_size - 1) // batch_size
    print(f"Processing {len(entities)} {entity_type}s in {num_batches} batches of {batch_size}")
    
    for i in range(0, len(entities), batch_size):
        batch_num = i // batch_size + 1
        # Get a batch of entities
        entity_batch = entities[i:i+batch_size]
        print(f"\nBatch {batch_num}/{num_batches}: Processing {len(entity_batch)} {entity_type}s")
        print(f"{entity_type.capitalize()}s in this batch: {', '.join(entity_batch)}")
        
        # Create prompt for this batch
        prompt = create_prompt_for_batch(entity_batch, entity_news, entity_type)
        
        # Save prompt to file for reference
        prompt_file = f"data/claude_prompt_{entity_type}_batch{batch_num}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(prompt_file, 'w') as f:
            f.write(prompt)
        
        # Call Claude API for this batch
        batch_summary = call_claude_api(prompt)
        
        if batch_summary:
            # Extract entity sections from the summary
            batch_sections = extract_client_sections(batch_summary)
            
            # Save batch summary to file
            batch_file = f"data/executive_summary_{entity_type}_batch{batch_num}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            with open(batch_file, 'w') as f:
                f.write(batch_summary)
            
            print(f"Batch {batch_num} summary saved to: {batch_file}")
            
            # Add batch sections to all sections
            all_sections.update(batch_sections)
            
            # Wait a bit before next batch to avoid rate limits
            if i + batch_size < len(entities):
                wait_time = 5
                print(f"Waiting {wait_time} seconds before next batch...")
                time.sleep(wait_time)
        else:
            print(f"Failed to generate summary for batch {batch_num}")
    
    return all_sections

def combine_summaries(all_sections, entities, entity_type="client"):
    """Combine all entity sections into a single summary"""
    # Create the header
    if entity_type == "client":
        title = "Client Executive News Summary"
    else:
        title = "Competitor Executive News Summary"
        
    header = f"# {title}\n\n{datetime.now().strftime('%Y-%m-%d')}\n\n"
    
    # Combine all entity sections in the order of the original entity list
    content = []
    for entity in entities:
        if entity in all_sections:
            content.append(all_sections[entity])
        else:
            content.append(f"## {entity}\n\nNo recent news available for this {entity_type}.\n")
    
    # Join everything together
    full_summary = header + '\n'.join(content)
    
    # Save the full summary to file
    summary_file = f"data/executive_summary_{entity_type}_full_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(summary_file, 'w') as f:
        f.write(full_summary)
    
    print(f"\nFull executive summary saved to: {summary_file}")
    return summary_file

def main(csv_file, entity_type="client"):
    """
    Main function to run the batch processing pipeline
    
    Args:
        csv_file (str): Path to the CSV file with news data
        entity_type (str): Type of entities to process - "client" or "competitor"
    """
    print(f"Starting batch executive summary generation for {entity_type}s from: {csv_file}")
    
    try:
        # Load entity news data
        entity_news, entities = load_entity_news(csv_file, entity_type)
        
        # Process in batches
        all_sections = process_in_batches(entity_news, entities, entity_type)
        
        # Combine all summaries
        summary_file = combine_summaries(all_sections, entities, entity_type)
        
        print(f"\nBatch processing for {entity_type}s completed successfully!")
        return summary_file
        
    except Exception as e:
        print(f"Error in batch processing: {e}")
        return None

if __name__ == "__main__":
    import argparse
    
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description="Generate executive summaries from news data")
    parser.add_argument("--type", choices=["client", "competitor"], 
                        default="client", help="Type of entities to process")
    parser.add_argument("--csv", help="Path to CSV file with news data")
    
    args = parser.parse_args()
    
    # Determine CSV file path
    csv_file = args.csv
    if not csv_file:
        # Try to get latest CSV file for the specified entity type
        try:
            with open(f"data/latest_{args.type}_csv.txt", "r") as f:
                csv_file = f.read().strip()
        except FileNotFoundError:
            # Fall back to the general latest_csv.txt
            try:
                with open("data/latest_csv.txt", "r") as f:
                    csv_file = f.read().strip()
            except FileNotFoundError:
                csv_file = input(f"Enter path to CSV file with {args.type} news data: ")
    
    if os.path.exists(csv_file):
        main(csv_file, args.type)
    else:
        print(f"CSV file not found: {csv_file}")