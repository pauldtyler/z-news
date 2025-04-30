#!/usr/bin/env python
"""
Incremental Website Monitor Script

This script monitors company websites incrementally, processing one website at a time
and saving progress after each, making it very resilient to timeouts.
"""

import os
import json
import logging
import argparse
import time
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from services.website_monitor import (
    load_website_config, 
    monitor_website, 
    format_changes_for_df, 
    save_changes_to_csv
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('incremental_monitor')

# Default configuration path
CONFIG_PATH = "config/websites.json"
OUTPUT_DIR = "data/website_updates"
CHECKPOINT_FILE = os.path.join(OUTPUT_DIR, "monitor_checkpoint.json")
COMBINED_RESULTS_FILE = os.path.join(OUTPUT_DIR, "recent_monitoring_results.json")

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

def load_checkpoint() -> Dict[str, Any]:
    """
    Load the monitoring checkpoint file
    
    Returns:
        Dictionary with checkpoint data
    """
    if not os.path.exists(CHECKPOINT_FILE):
        return {
            "last_run_started": datetime.now().isoformat(),
            "last_run_completed": None,
            "completed_sites": [],
            "changes_files": []
        }
    
    try:
        with open(CHECKPOINT_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        logger.warning("Invalid checkpoint file, starting fresh")
        return {
            "last_run_started": datetime.now().isoformat(),
            "last_run_completed": None,
            "completed_sites": [],
            "changes_files": []
        }

def save_checkpoint(checkpoint: Dict[str, Any]) -> None:
    """
    Save the monitoring checkpoint
    
    Args:
        checkpoint: Dictionary with checkpoint data
    """
    with open(CHECKPOINT_FILE, 'w') as f:
        json.dump(checkpoint, f, indent=2)

def save_monitoring_results(site_name: str, site_url: str, changes: List[Dict[str, Any]]) -> None:
    """
    Append monitoring results to a combined results file
    
    Args:
        site_name: Name of the monitored website
        site_url: URL of the monitored website
        changes: List of detected changes
    """
    results = {
        "site_name": site_name,
        "site_url": site_url,
        "timestamp": datetime.now().isoformat(),
        "changes_count": len(changes),
        "changes": changes
    }
    
    # Read existing results if they exist
    if os.path.exists(COMBINED_RESULTS_FILE):
        try:
            with open(COMBINED_RESULTS_FILE, 'r') as f:
                all_results = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            all_results = []
    else:
        all_results = []
    
    # Append new results
    all_results.append(results)
    
    # Keep only recent results (last 50 sites)
    if len(all_results) > 50:
        all_results = all_results[-50:]
    
    # Save updated results
    with open(COMBINED_RESULTS_FILE, 'w') as f:
        json.dump(all_results, f, indent=2)

def get_remaining_websites(websites: List[Dict[str, Any]], completed_sites: List[str]) -> List[Dict[str, Any]]:
    """
    Get list of websites that haven't been processed yet
    
    Args:
        websites: List of all website configurations
        completed_sites: List of URLs of already processed sites
        
    Returns:
        List of websites that still need to be processed
    """
    return [site for site in websites if site.get('url', '') not in completed_sites]

def monitor_single_website(website: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """
    Monitor a single website and save results
    
    Args:
        website: Website configuration dictionary
        
    Returns:
        Tuple of (formatted changes, CSV path if changes were saved)
    """
    site_name = website.get('name', 'Unnamed')
    site_url = website.get('url', '')
    
    logger.info(f"Processing website: {site_name}")
    
    try:
        # Monitor the website
        new_items, updated_items = monitor_website(website)
        
        # Format changes for DataFrame
        changes = format_changes_for_df(website, new_items, updated_items)
        
        # Save to monitoring results
        save_monitoring_results(site_name, site_url, changes)
        
        # Save changes to CSV if any
        csv_path = None
        if changes:
            csv_path = save_changes_to_csv(changes)
            logger.info(f"Saved {len(changes)} changes to {csv_path}")
        
        return changes, csv_path
        
    except Exception as e:
        logger.error(f"Error monitoring {site_name}: {e}")
        return [], None

def monitor_incrementally(
    max_sites: int = None,
    delay: int = 5,
    continue_from_checkpoint: bool = True
) -> Dict[str, Any]:
    """
    Monitor websites incrementally, one at a time
    
    Args:
        max_sites: Maximum number of sites to process (None = all)
        delay: Delay between processing each website (seconds)
        continue_from_checkpoint: Whether to continue from previous checkpoint
        
    Returns:
        Monitoring statistics
    """
    logger.info("Starting incremental website monitoring")
    
    # Load website configurations
    websites = load_website_config()
    
    if not websites:
        logger.warning("No websites configured for monitoring")
        return {
            "sites_processed": 0,
            "changes_detected": 0,
            "files_created": []
        }
    
    # Load checkpoint if continuing
    checkpoint = load_checkpoint() if continue_from_checkpoint else {
        "last_run_started": datetime.now().isoformat(),
        "last_run_completed": None,
        "completed_sites": [],
        "changes_files": []
    }
    
    completed_sites = checkpoint.get("completed_sites", [])
    changes_files = checkpoint.get("changes_files", [])
    
    # Get remaining websites
    remaining = get_remaining_websites(websites, completed_sites)
    
    if max_sites:
        remaining = remaining[:max_sites]
    
    logger.info(f"Found {len(remaining)}/{len(websites)} websites to process")
    
    # Process each website incrementally
    total_changes = 0
    
    for i, website in enumerate(remaining):
        site_url = website.get('url', '')
        
        # Add delay between sites (skip for first site)
        if i > 0:
            logger.info(f"Waiting {delay} seconds before next site...")
            time.sleep(delay)
        
        # Process the website
        changes, csv_path = monitor_single_website(website)
        
        # Update statistics
        total_changes += len(changes)
        
        # Update checkpoint
        completed_sites.append(site_url)
        if csv_path and csv_path not in changes_files:
            changes_files.append(csv_path)
        
        checkpoint["completed_sites"] = list(set(completed_sites))  # Remove duplicates
        checkpoint["changes_files"] = changes_files
        
        save_checkpoint(checkpoint)
        logger.info(f"Checkpoint saved: {len(completed_sites)}/{len(websites)} sites processed")
        
        # Status update to console
        print(f"Processed {len(completed_sites)}/{len(websites)}: {website.get('name', '')}")
        if changes:
            print(f"  - Found {len(changes)} changes")
    
    # Mark run as completed
    checkpoint["last_run_completed"] = datetime.now().isoformat()
    save_checkpoint(checkpoint)
    
    return {
        "sites_processed": len(completed_sites),
        "changes_detected": total_changes,
        "files_created": changes_files
    }

def clear_checkpoint() -> None:
    """Clear the checkpoint file to start fresh"""
    if os.path.exists(CHECKPOINT_FILE):
        os.remove(CHECKPOINT_FILE)
        logger.info("Checkpoint cleared")

def list_completed() -> None:
    """List completed websites from checkpoint"""
    if not os.path.exists(CHECKPOINT_FILE):
        print("No checkpoint found")
        return
    
    checkpoint = load_checkpoint()
    completed = checkpoint.get("completed_sites", [])
    
    print(f"Completed sites: {len(completed)}")
    for site in completed:
        print(f"  - {site}")

def show_recent_changes(limit: int = 20, company: str = None, csv_file: str = None, format_type: str = "text") -> None:
    """
    Show recent website changes in a readable format
    
    Args:
        limit: Maximum number of changes to show
        company: Filter changes to specific company (case-insensitive)
        csv_file: Specific CSV file to read (will use most recent if not specified)
        format_type: Output format - 'text' (default) or 'markdown'
    """
    # Find CSV files
    if csv_file:
        csv_path = os.path.join(OUTPUT_DIR, csv_file) if not os.path.isabs(csv_file) else csv_file
        if not os.path.exists(csv_path):
            print(f"CSV file not found: {csv_path}")
            return
        latest_csv = csv_path
    else:
        # Find the most recent CSV file
        csv_files = [f for f in os.listdir(OUTPUT_DIR) if f.startswith('website_updates_') and f.endswith('.csv')]
        if not csv_files:
            print("No website update files found")
            return
        
        # Sort by modification time (newest first)
        csv_files.sort(key=lambda f: os.path.getmtime(os.path.join(OUTPUT_DIR, f)), reverse=True)
        latest_csv = os.path.join(OUTPUT_DIR, csv_files[0])
    
    try:
        # Load the CSV file
        df = pd.read_csv(latest_csv)
        
        # If markdown format requested, check if markdown file exists or create it
        if format_type == "markdown":
            show_markdown_changes(df, os.path.basename(latest_csv), company)
            return
        
        # For text format, continue with original implementation
        # Filter by company if specified
        if company:
            # Case-insensitive partial match
            df = df[df['site_name'].str.lower().str.contains(company.lower())]
            if len(df) == 0:
                print(f"No changes found for company matching '{company}'")
                print("Available companies:")
                all_df = pd.read_csv(latest_csv)
                for site in sorted(all_df['site_name'].unique()):
                    print(f"  - {site}")
                return
        
        # Display summary
        print(f"Recent website changes (from {os.path.basename(latest_csv)}):")
        print(f"Total changes: {len(df)}")
        
        # Group by site and count
        site_counts = df.groupby(['site_name', 'change_type']).size().reset_index(name='count')
        print("\nChanges by site:")
        for _, row in site_counts.iterrows():
            print(f"  - {row['site_name']}: {row['count']} {row['change_type']} items")
        
        # Display the most recent changes
        print(f"\nRecent changes (showing up to {limit}):")
        for idx, row in df.head(limit).iterrows():
            print(f"\n[{idx+1}] {row['site_name']} ({row['change_type']})")
            print(f"    Title: {row['title'][:80]}..." if len(str(row['title'])) > 80 else f"    Title: {row['title']}")
            if not pd.isna(row['url']):
                print(f"    URL: {row['url']}")
            if not pd.isna(row['date']) and row['date']:
                print(f"    Date: {row['date']}")
            if not pd.isna(row['excerpt']) and row['excerpt']:
                excerpt = str(row['excerpt'])
                print(f"    Excerpt: {excerpt[:100]}..." if len(excerpt) > 100 else f"    Excerpt: {excerpt}")
            
    except Exception as e:
        print(f"Error reading CSV file: {e}")


def show_markdown_changes(df: pd.DataFrame, csv_filename: str, company: str = None) -> None:
    """
    Display or generate markdown report for website changes
    
    Args:
        df: DataFrame with website changes
        csv_filename: Name of the CSV file
        company: Filter changes to specific company (case-insensitive)
    """
    # Extract timestamp from CSV filename for matching markdown
    if csv_filename.startswith('website_updates_') and csv_filename.endswith('.csv'):
        timestamp = csv_filename[16:-4]  # Extract timestamp part
        md_filename = f"website_changes_{timestamp}.md"
        md_path = os.path.join(OUTPUT_DIR, md_filename)
    else:
        md_path = os.path.join(OUTPUT_DIR, "latest_website_changes.md")
    
    # Filter by company if specified
    if company:
        # Case-insensitive partial match
        df_filtered = df[df['site_name'].str.lower().str.contains(company.lower())]
        if len(df_filtered) == 0:
            print(f"No changes found for company matching '{company}'")
            print("Available companies:")
            for site in sorted(df['site_name'].unique()):
                print(f"  - {site}")
            return
        
        # Generate a custom markdown for the filtered company
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        from services.website_monitor import generate_markdown_report
        custom_md_path = generate_markdown_report(df_filtered, f"{timestamp}_{company}")
        
        # Display the path to the generated file
        print(f"Generated markdown report for '{company}': {custom_md_path}")
        
        # Optionally display the content directly
        with open(custom_md_path, 'r') as f:
            print("\n" + f.read())
        
        return
    
    # Check if the markdown file already exists
    if os.path.exists(md_path):
        print(f"Showing markdown report: {md_path}")
        with open(md_path, 'r') as f:
            print("\n" + f.read())
    else:
        # Generate markdown from the data
        from services.website_monitor import generate_markdown_report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        md_path = generate_markdown_report(df, timestamp)
        print(f"Generated markdown report: {md_path}")
        
        # Display the content
        with open(md_path, 'r') as f:
            print("\n" + f.read())
        
def list_available_csvs() -> None:
    """List available CSV files with website changes"""
    csv_files = [f for f in os.listdir(OUTPUT_DIR) if f.startswith('website_updates_') and f.endswith('.csv')]
    if not csv_files:
        print("No website update files found")
        return
    
    # Sort by modification time (newest first)
    csv_files.sort(key=lambda f: os.path.getmtime(os.path.join(OUTPUT_DIR, f)), reverse=True)
    
    print(f"Available website update files ({len(csv_files)}):")
    for idx, file in enumerate(csv_files[:10], 1):  # Show most recent 10
        timestamp = os.path.getmtime(os.path.join(OUTPUT_DIR, file))
        time_str = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
        print(f"{idx}. {file} (created: {time_str})")

if __name__ == "__main__":
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Monitor websites incrementally")
    parser.add_argument("--max-sites", type=int, default=None,
                        help="Maximum number of sites to process (default: all remaining)")
    parser.add_argument("--delay", type=int, default=5,
                        help="Delay between processing each website (seconds)")
    parser.add_argument("--config", help="Path to website configuration JSON file")
    parser.add_argument("--fresh", action="store_true", 
                        help="Start fresh (ignore checkpoint)")
    parser.add_argument("--clear", action="store_true",
                        help="Clear checkpoint and exit")
    parser.add_argument("--list", action="store_true",
                        help="List completed websites and exit")
    parser.add_argument("--show-changes", action="store_true",
                        help="Show recent website changes and exit")
    parser.add_argument("--markdown", action="store_true",
                        help="Display changes in markdown format")
    parser.add_argument("--limit", type=int, default=20,
                        help="Limit number of changes to show (default: 20)")
    parser.add_argument("--company", type=str,
                        help="Filter changes to specific company (case-insensitive)")
    parser.add_argument("--csv-file", type=str,
                        help="Specific CSV file to read for changes")
    parser.add_argument("--list-files", action="store_true",
                        help="List available CSV files with website changes")
    parser.add_argument("--list-markdown", action="store_true",
                        help="List available markdown reports")
    
    args = parser.parse_args()
    
    # Handle special commands
    if args.clear:
        clear_checkpoint()
        exit(0)
    
    if args.list:
        list_completed()
        exit(0)
    
    if args.list_files:
        list_available_csvs()
        exit(0)
        
    if args.list_markdown:
        # List all markdown reports in the output directory
        md_files = [f for f in os.listdir(OUTPUT_DIR) if f.startswith('website_changes_') and f.endswith('.md')]
        if not md_files:
            print("No markdown reports found")
        else:
            # Sort by modification time (newest first)
            md_files.sort(key=lambda f: os.path.getmtime(os.path.join(OUTPUT_DIR, f)), reverse=True)
            print(f"Available markdown reports ({len(md_files)}):")
            for idx, file in enumerate(md_files[:10], 1):  # Show most recent 10
                timestamp = os.path.getmtime(os.path.join(OUTPUT_DIR, file))
                time_str = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
                print(f"{idx}. {file} (created: {time_str})")
        exit(0)
        
    if args.show_changes:
        # Use markdown format if requested
        format_type = "markdown" if args.markdown else "text"
        show_recent_changes(args.limit, args.company, args.csv_file, format_type)
        exit(0)
    
    # Use specified config path or default
    if args.config:
        CONFIG_PATH = args.config
    
    # Run the monitoring
    stats = monitor_incrementally(
        max_sites=args.max_sites,
        delay=args.delay,
        continue_from_checkpoint=not args.fresh
    )
    
    # Final report
    print("\nMonitoring completed:")
    print(f"- Sites processed: {stats['sites_processed']}")
    print(f"- Changes detected: {stats['changes_detected']}")
    
    if stats['files_created']:
        print(f"- CSV files created: {len(stats['files_created'])}")
        for idx, file_path in enumerate(stats['files_created'][-5:], 1):  # Show last 5 files
            print(f"  {idx}. {file_path}")
    else:
        print("- No changes detected")