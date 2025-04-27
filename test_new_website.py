#!/usr/bin/env python
"""
Test script to monitor a single new competitor website
"""

import json
import logging
import sys
from services.website_monitor import monitor_website, format_changes_for_df, save_changes_to_csv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_new_website')

# Dictionary of test websites
TEST_WEBSITES = {
    "benekiva": {
        "name": "Benekiva",
        "url": "https://benekiva.com/company-news/",
        "selector": "article, .post, .news-item",
        "frequency": 86400,
        "type": "competitor"
    },
    "dxc": {
        "name": "DXC",
        "url": "https://dxc.com/us/en/newsroom",
        "selector": "article, .news-item, .press-release",
        "frequency": 86400,
        "type": "competitor"
    },
    "equisoft": {
        "name": "Equisoft",
        "url": "https://www.equisoft.com/insights?type=press-release&industry=insurance#filter",
        "selector": "article, .news-item, .press-release",
        "frequency": 86400,
        "type": "competitor"
    },
    "fidx": {
        "name": "FIDx",
        "url": "https://fidx.io/news",
        "selector": "article, .news-item, .post",
        "frequency": 86400,
        "type": "competitor"
    },
    "sureify": {
        "name": "Sureify",
        "url": "https://www.sureify.com/all-resources/#press",
        "selector": "article, .press-release, .resource-item",
        "frequency": 86400,
        "type": "competitor"
    }
}

def test_single_website(website_key):
    """Test monitoring a single website"""
    if website_key not in TEST_WEBSITES:
        logger.error(f"Website '{website_key}' not found in test websites")
        print(f"Available websites: {', '.join(TEST_WEBSITES.keys())}")
        return None
        
    website = TEST_WEBSITES[website_key]
    logger.info(f"Testing website: {website['name']}")
    
    # Monitor the website
    new_items, updated_items = monitor_website(website)
    
    # Format changes for DataFrame
    changes = format_changes_for_df(website, new_items, updated_items)
    
    # Save all changes to CSV if any
    if changes:
        csv_path = save_changes_to_csv(changes)
        logger.info(f"Saved {len(changes)} changes to {csv_path}")
        return csv_path
    else:
        logger.info("No changes detected on the website")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} WEBSITE_NAME")
        print(f"Available websites: {', '.join(TEST_WEBSITES.keys())}")
        sys.exit(1)
        
    website_key = sys.argv[1].lower()
    result = test_single_website(website_key)
    
    if result:
        print(f"Changes detected and saved to {result}")
    else:
        print("No changes detected")