#!/usr/bin/env python
"""
Batched Website Monitor Script

This script monitors company websites in batches to prevent timeouts.
It enables processing a subset of websites at a time and keeps track of progress.
"""

import os
import json
import logging
import argparse
import time
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
logger = logging.getLogger('batched_monitor')

# Default configuration path
CONFIG_PATH = "config/websites.json"
OUTPUT_DIR = "data/website_updates"
CHECKPOINT_FILE = os.path.join(OUTPUT_DIR, "monitor_checkpoint.json")

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
            "last_run": None,
            "completed_sites": [],
            "batch_changes_files": []
        }
    
    try:
        with open(CHECKPOINT_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        logger.warning("Invalid checkpoint file, starting fresh")
        return {
            "last_run": None,
            "completed_sites": [],
            "batch_changes_files": []
        }

def save_checkpoint(checkpoint: Dict[str, Any]) -> None:
    """
    Save the monitoring checkpoint
    
    Args:
        checkpoint: Dictionary with checkpoint data
    """
    with open(CHECKPOINT_FILE, 'w') as f:
        json.dump(checkpoint, f, indent=2)

def monitor_websites_batch(
    websites: List[Dict[str, Any]], 
    batch_size: int = 5, 
    start_index: int = 0, 
    delay: int = 5,
    completed_sites: List[str] = None
) -> Tuple[List[Dict[str, Any]], List[str], Optional[str]]:
    """
    Monitor a batch of websites
    
    Args:
        websites: List of website configurations
        batch_size: Number of websites to process in this batch
        start_index: Starting index in the websites list
        delay: Delay between processing each website (seconds)
        completed_sites: List of site URLs that have been completed
        
    Returns:
        Tuple of (all changes, completed site URLs, CSV path if changes were saved)
    """
    if completed_sites is None:
        completed_sites = []
    
    # Process websites in the batch
    all_changes = []
    processed_sites = []
    end_index = min(start_index + batch_size, len(websites))
    
    logger.info(f"Processing batch: websites {start_index+1}-{end_index} of {len(websites)}")
    
    for i in range(start_index, end_index):
        website = websites[i]
        site_url = website.get('url', '')
        
        # Skip already completed sites
        if site_url in completed_sites:
            logger.info(f"Skipping already processed site: {website.get('name', '')}")
            continue
            
        try:
            # Add delay between sites (skip for first site in batch)
            if i > start_index:
                logger.info(f"Waiting {delay} seconds before next site...")
                time.sleep(delay)
            
            # Monitor the website
            logger.info(f"Processing {i+1}/{len(websites)}: {website.get('name', '')}")
            new_items, updated_items = monitor_website(website)
            
            # Format changes for DataFrame
            changes = format_changes_for_df(website, new_items, updated_items)
            all_changes.extend(changes)
            
            # Mark as completed
            processed_sites.append(site_url)
            
        except Exception as e:
            logger.error(f"Error monitoring {website.get('name', '')}: {e}")
    
    # Save batch changes to CSV if any
    csv_path = None
    if all_changes:
        csv_path = save_changes_to_csv(all_changes)
        logger.info(f"Saved {len(all_changes)} changes to {csv_path}")
    
    return all_changes, processed_sites, csv_path

def monitor_all_websites_batched(
    batch_size: int = 5, 
    delay: int = 5,
    continue_from_checkpoint: bool = True
) -> List[str]:
    """
    Monitor all websites in batches with checkpointing
    
    Args:
        batch_size: Number of websites to process in each batch
        delay: Delay between processing each website (seconds)
        continue_from_checkpoint: Whether to continue from previous checkpoint
        
    Returns:
        List of CSV files with changes
    """
    logger.info(f"Starting batched website monitoring (batch size: {batch_size})")
    
    # Load website configurations
    websites = load_website_config()
    
    if not websites:
        logger.warning("No websites configured for monitoring")
        return []
    
    # Load checkpoint if continuing
    checkpoint = load_checkpoint() if continue_from_checkpoint else {
        "last_run": None,
        "completed_sites": [],
        "batch_changes_files": []
    }
    
    completed_sites = checkpoint.get("completed_sites", [])
    batch_changes_files = checkpoint.get("batch_changes_files", [])
    
    # Calculate batches
    total_batches = (len(websites) + batch_size - 1) // batch_size
    
    for batch_num in range(total_batches):
        start_index = batch_num * batch_size
        
        # Skip batch if all sites in it are already completed
        batch_sites = [websites[i].get('url', '') for i in range(
            start_index, 
            min(start_index + batch_size, len(websites))
        )]
        
        if all(site in completed_sites for site in batch_sites):
            logger.info(f"Skipping batch {batch_num+1}/{total_batches} (already completed)")
            continue
        
        # Process the batch
        logger.info(f"Processing batch {batch_num+1}/{total_batches}")
        _, batch_completed_sites, csv_path = monitor_websites_batch(
            websites, 
            batch_size, 
            start_index, 
            delay,
            completed_sites
        )
        
        # Update checkpoint
        completed_sites.extend(batch_completed_sites)
        if csv_path:
            batch_changes_files.append(csv_path)
        
        checkpoint["last_run"] = datetime.now().isoformat()
        checkpoint["completed_sites"] = list(set(completed_sites))  # Remove duplicates
        checkpoint["batch_changes_files"] = batch_changes_files
        
        save_checkpoint(checkpoint)
        logger.info(f"Checkpoint saved: {len(completed_sites)}/{len(websites)} sites processed")
    
    # Generate final combined CSV if needed
    if batch_changes_files and len(batch_changes_files) > 1:
        # Future enhancement: combine all CSV files into one
        pass
    
    logger.info(f"Completed monitoring {len(completed_sites)}/{len(websites)} websites")
    return batch_changes_files

def clear_checkpoint() -> None:
    """Clear the checkpoint file to start fresh"""
    if os.path.exists(CHECKPOINT_FILE):
        os.remove(CHECKPOINT_FILE)
        logger.info("Checkpoint cleared")

if __name__ == "__main__":
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Monitor websites for updates in batches")
    parser.add_argument("--batch-size", type=int, default=3, 
                        help="Number of websites to process in each batch")
    parser.add_argument("--delay", type=int, default=5,
                        help="Delay between processing each website (seconds)")
    parser.add_argument("--config", help="Path to website configuration JSON file")
    parser.add_argument("--fresh", action="store_true", 
                        help="Start fresh (ignore checkpoint)")
    parser.add_argument("--clear", action="store_true",
                        help="Clear checkpoint and exit")
    
    args = parser.parse_args()
    
    # Clear checkpoint if requested
    if args.clear:
        clear_checkpoint()
        exit(0)
    
    # Use specified config path or default
    config_path = args.config or CONFIG_PATH
    
    # Run the monitoring
    result = monitor_all_websites_batched(
        batch_size=args.batch_size,
        delay=args.delay,
        continue_from_checkpoint=not args.fresh
    )
    
    if result:
        print(f"Changes detected and saved to {len(result)} files:")
        for idx, file_path in enumerate(result, 1):
            print(f"{idx}. {file_path}")
    else:
        print("No changes detected")