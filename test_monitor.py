#!/usr/bin/env python
"""
Test script to monitor a single website
"""

import json
import logging
from services.website_monitor import monitor_website, format_changes_for_df, save_changes_to_csv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_monitor')

# Define the website to test
TEST_WEBSITE = {
    "name": "iPipeline",
    "url": "https://ipipeline.com/resources/newsroom/",
    "selector": "article.elementor-post",
    "frequency": 86400,
    "type": "competitor"
}

def test_single_website():
    """Test monitoring a single website"""
    logger.info(f"Testing website: {TEST_WEBSITE['name']}")
    
    # Monitor the website
    new_items, updated_items = monitor_website(TEST_WEBSITE)
    
    # Format changes for DataFrame
    changes = format_changes_for_df(TEST_WEBSITE, new_items, updated_items)
    
    # Save all changes to CSV if any
    if changes:
        csv_path = save_changes_to_csv(changes)
        logger.info(f"Saved {len(changes)} changes to {csv_path}")
        return csv_path
    else:
        logger.info("No changes detected on the website")
        return None

if __name__ == "__main__":
    result = test_single_website()
    
    if result:
        print(f"Changes detected and saved to {result}")
    else:
        print("No changes detected")