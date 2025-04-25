#!/usr/bin/env python
"""
Batch Executive Summary Generator

This script processes news data from a CSV file (clients, competitors, topics) and generates executive summaries
in batches using Claude API, then combines them into a single markdown file organized by categories.
"""

import os
import json
import pandas as pd
from datetime import datetime
import time
import re
from typing import Dict, List, Tuple, Any, Optional, Union

from dotenv import load_dotenv

# Import from local modules
from config.config import (
    SUMMARY_BATCH_SIZE, TOPIC_CATEGORIES, DATA_DIR
)
from services import ClaudeApiClient
from templates import (
    COMPANY_PROMPT_TEMPLATE, COMPETITOR_PROMPT_TEMPLATE, TOPIC_PROMPT_TEMPLATE, COMBINED_REPORT_HEADER
)
from utils import (
    load_entities, get_entity_name, get_topic_category,
    generate_timestamp
)

# Load environment variables
load_dotenv()

# Create data directory if it doesn't exist
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)


def load_entity_news(csv_file, entity_type="client"):
    """
    Load news data from CSV and group by entity (client, competitor or topic)
    
    For topics, the entity name is expected to be in the format "Category: Topic Name"
    """
    if not os.path.exists(csv_file):
        raise FileNotFoundError(f"CSV file not found: {csv_file}")
    
    # Load the CSV data
    df = pd.read_csv(csv_file)
    
    # Get unique list of entities
    entities = df['client'].unique().tolist()
    
    # For topic data, extract categories and sort by predefined order
    if entity_type == "topic":
        # Extract categories and organize entities by category
        categorized_entities = {}
        for entity in entities:
            # Extract category and topic name from entity
            if ":" in entity:
                category, topic_name = entity.split(":", 1)
                category = category.strip()
                if category not in categorized_entities:
                    categorized_entities[category] = []
                categorized_entities[category].append(entity)
            else:
                # If no category is found, put in "Other"
                category = "Other"
                if category not in categorized_entities:
                    categorized_entities[category] = []
                categorized_entities[category].append(entity)
        
        # Sort categories by predefined order, with any additional categories at the end
        sorted_categories = []
        for category in TOPIC_CATEGORIES:
            if category in categorized_entities:
                sorted_categories.append(category)
        
        # Add any categories not in predefined list
        for category in categorized_entities:
            if category not in sorted_categories:
                sorted_categories.append(category)
        
        # Create a flat sorted entities list based on sorted categories
        sorted_entities = []
        for category in sorted_categories:
            sorted_entities.extend(sorted(categorized_entities[category]))
        
        entities = sorted_entities
        print(f"Found {len(entities)} unique industry topics in {len(sorted_categories)} categories")
    else:
        # For clients or competitors, sort alphabetically
        entities = sorted(entities)
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
    """Create a prompt for a batch of entities (clients, competitors, or topics)"""
    # Extract just the news for this batch of entities
    batch_news = {entity: entity_news[entity] for entity in entity_batch}
    
    # Format the news data as JSON string
    news_data_str = json.dumps(batch_news, indent=2)
    
    # Determine prompt template and format it based on entity type
    if entity_type == "client":
        title = "Client Executive News Summary"
        focus = "financial service clients"
        prompt = COMPANY_PROMPT_TEMPLATE.format(
            focus=focus,
            title=title,
            news_data=news_data_str
        )
    elif entity_type == "competitor":
        title = "Competitor Intelligence Summary"
        focus = "financial service competitors"
        prompt = COMPETITOR_PROMPT_TEMPLATE.format(
            focus=focus,
            title=title,
            news_data=news_data_str
        )
    else:  # topic
        title = "Industry Topics Executive News Summary"
        prompt = TOPIC_PROMPT_TEMPLATE.format(
            title=title,
            news_data=news_data_str
        )
    
    return prompt


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


def process_in_batches(entity_news, entities, entity_type="client", batch_size=SUMMARY_BATCH_SIZE):
    """Process entities in batches"""
    all_sections = {}
    api_client = ClaudeApiClient()
    
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
        timestamp = generate_timestamp()
        prompt_file = f"data/claude_prompt_{entity_type}_batch{batch_num}_{timestamp}.txt"
        with open(prompt_file, 'w') as f:
            f.write(prompt)
        
        # Call Claude API for this batch
        system_prompt = 'You are an expert financial analyst creating executive summaries for insurance and financial services industry.'
        batch_summary = api_client.generate_summary(prompt, system_prompt)
        
        if batch_summary:
            # Extract entity sections from the summary
            batch_sections = extract_client_sections(batch_summary)
            
            # Save batch summary to file
            batch_file = f"data/executive_summary_{entity_type}_batch{batch_num}_{timestamp}.md"
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
    elif entity_type == "competitor":
        title = "Competitor Executive News Summary"
    else:
        title = "Industry Topics Executive News Summary"
        
    header = f"# {title}\n\n{datetime.now().strftime('%Y-%m-%d')}\n\n"
    
    # Combine all entity sections based on type
    content = []
    
    if entity_type == "topic":
        # For topics, organize by category
        category_sections = {}
        current_category = None
        
        for entity in entities:
            # Extract category from entity name (format: "Category: Topic Name")
            if ":" in entity:
                category, topic_name = entity.split(":", 1)
                category = category.strip()
            else:
                category = "Other"
                
            # Add category header if this is a new category
            if category != current_category:
                if category not in category_sections:
                    category_sections[category] = []
                current_category = category
            
            # Add the entity content
            if entity in all_sections:
                category_sections[category].append(all_sections[entity])
            else:
                category_sections[category].append(f"## {entity}\n\nNo recent news available for this topic.\n")
        
        # Combine categories in order
        for category in TOPIC_CATEGORIES:
            if category in category_sections:
                content.append(f"# {category}\n")
                content.extend(category_sections[category])
                # Remove the category from the dict to track which ones we've processed
                del category_sections[category]
        
        # Add any remaining categories not in the predefined list
        for category in sorted(category_sections.keys()):
            content.append(f"# {category}\n")
            content.extend(category_sections[category])
    else:
        # For clients or competitors, simple sequential order
        for entity in entities:
            if entity in all_sections:
                content.append(all_sections[entity])
            else:
                content.append(f"## {entity}\n\nNo recent news available for this {entity_type}.\n")
    
    # Join everything together
    full_summary = header + '\n'.join(content)
    
    # Save the full summary to file
    timestamp = generate_timestamp()
    summary_file = f"data/executive_summary_{entity_type}_full_{timestamp}.md"
    with open(summary_file, 'w') as f:
        f.write(full_summary)
    
    print(f"\nFull executive summary saved to: {summary_file}")
    return summary_file


def create_combined_report(summary_files, dataframes=None):
    """
    Create a comprehensive combined report with clients, competitors, and topics
    
    Args:
        summary_files (dict): Dictionary of summary files by entity type
        dataframes (dict): Dictionary of raw dataframes by entity type for fallback
    """
    print("\nCreating comprehensive combined report...")
    
    # Create the combined markdown report
    current_date = datetime.now().strftime('%Y-%m-%d')
    combined_title = COMBINED_REPORT_HEADER.format(current_date=current_date)
    
    sections = []
    
    # First add industry topics section if available
    if "topic" in summary_files:
        try:
            with open(summary_files["topic"], 'r') as f:
                topic_content = f.read()
                # Remove the header (first few lines) from the topic content
                topic_content = re.sub(r'^.*?\n\n', '', topic_content, flags=re.DOTALL)
                sections.append("## Industry Topics\n\n" + topic_content)
        except (FileNotFoundError, PermissionError) as e:
            print(f"Warning: Could not read topic summary file: {e}")
            sections.append("## Industry Topics\n\nTopic data not available.")
    
    # Then add client summaries if available
    if "client" in summary_files:
        try:
            with open(summary_files["client"], 'r') as f:
                client_content = f.read()
                # Remove the header (first few lines) from the client content
                client_content = re.sub(r'^.*?\n\n', '', client_content, flags=re.DOTALL)
                sections.append("## Client Companies\n\n" + client_content)
        except (FileNotFoundError, PermissionError) as e:
            print(f"Warning: Could not read client summary file: {e}")
            sections.append("## Client Companies\n\nClient data not available.")
    
    # Finally add competitor summaries if available
    if "competitor" in summary_files:
        try:
            with open(summary_files["competitor"], 'r') as f:
                competitor_content = f.read()
                # Remove the header (first few lines) from the competitor content
                competitor_content = re.sub(r'^.*?\n\n', '', competitor_content, flags=re.DOTALL)
                sections.append("## Competitor Companies\n\n" + competitor_content)
        except (FileNotFoundError, PermissionError) as e:
            print(f"Warning: Could not read competitor summary file: {e}")
            sections.append("## Competitor Companies\n\nCompetitor data not available.")
    
    # Combine all sections
    combined_content = combined_title + "\n\n".join(sections)
    
    # Save to file
    timestamp = generate_timestamp()
    combined_file = f"data/executive_summary_combined_{timestamp}.md"
    with open(combined_file, 'w') as f:
        f.write(combined_content)
    
    print(f"Combined executive summary saved to: {combined_file}")
    return combined_file


def main(csv_files=None, entity_types=None, combined=False):
    """
    Main function to run the batch processing pipeline
    
    Args:
        csv_files (dict): Dictionary mapping entity types to CSV files
        entity_types (list): List of entity types to process
        combined (bool): Whether to create a combined report
    """
    if entity_types is None:
        entity_types = ["client"]  # Default to client only
        
    if csv_files is None:
        csv_files = {}
    
    # Process each entity type
    summary_files = {}
    
    for entity_type in entity_types:
        # Get CSV file for this entity type
        csv_file = csv_files.get(entity_type)
        
        if not csv_file:
            # Try to get latest CSV file for the specified entity type
            try:
                with open(f"data/latest_{entity_type}_csv.txt", "r") as f:
                    csv_file = f.read().strip()
            except FileNotFoundError:
                # Fall back to the general latest_csv.txt
                try:
                    with open("data/latest_csv.txt", "r") as f:
                        csv_file = f.read().strip()
                except FileNotFoundError:
                    csv_file = input(f"Enter path to CSV file with {entity_type} news data: ")
        
        if not os.path.exists(csv_file):
            print(f"CSV file not found for {entity_type}: {csv_file}")
            continue
            
        print(f"\nStarting batch executive summary generation for {entity_type} from: {csv_file}")
        
        try:
            # Load entity news data
            entity_news, entities = load_entity_news(csv_file, entity_type)
            
            # Process in batches
            all_sections = process_in_batches(entity_news, entities, entity_type)
            
            # Combine all summaries for this entity type
            summary_file = combine_summaries(all_sections, entities, entity_type)
            summary_files[entity_type] = summary_file
            
            print(f"Batch processing for {entity_type} completed successfully!")
            
        except Exception as e:
            print(f"Error in batch processing for {entity_type}: {e}")
    
    # Create combined report if requested and we have at least one summary
    if combined and summary_files:
        combined_file = create_combined_report(summary_files)
        return combined_file
    elif len(summary_files) == 1:
        # If only one type was processed, return that summary file
        return list(summary_files.values())[0]
    else:
        # Otherwise return all summary files
        return summary_files


if __name__ == "__main__":
    import argparse
    
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description="Generate executive summaries from news data")
    parser.add_argument("--type", choices=["client", "competitor", "topic", "all"], 
                        default="client", help="Type of entities to process")
    parser.add_argument("--csv", help="Path to CSV file with news data")
    parser.add_argument("--client-csv", help="Path to CSV file with client news data")
    parser.add_argument("--competitor-csv", help="Path to CSV file with competitor news data")
    parser.add_argument("--topic-csv", help="Path to CSV file with topic news data")
    parser.add_argument("--combined", action="store_true", help="Create a combined report")
    
    args = parser.parse_args()
    
    # Determine entity types to process
    if args.type == "all":
        entity_types = ["client", "competitor", "topic"]
    else:
        entity_types = [args.type]
    
    # Determine CSV files for each entity type
    csv_files = {}
    
    # Map specific CSV args to entity types
    if args.client_csv:
        csv_files["client"] = args.client_csv
    
    if args.competitor_csv:
        csv_files["competitor"] = args.competitor_csv
    
    if args.topic_csv:
        csv_files["topic"] = args.topic_csv
    
    # Handle the generic --csv argument
    if args.csv and args.type != "all":
        csv_files[args.type] = args.csv
    
    # Run main function with parsed arguments
    main(csv_files, entity_types, args.combined)