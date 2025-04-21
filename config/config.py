#!/usr/bin/env python
"""
Configuration settings for Z-News application
"""

import os

# Search configuration
BATCH_SIZE = 3  # Process entities in batches of this size
WEEKLY_TIME_PERIOD = 'w'  # Default time period for weekly summaries
DELAY_BETWEEN_REQUESTS = 8  # Seconds to wait between requests to avoid rate limits
MAX_RETRIES = 5  # Maximum number of retry attempts
INITIAL_BACKOFF = 10  # Initial backoff time in seconds for rate limits
MAX_BACKOFF = 120  # Maximum backoff time in seconds

# Result count configuration
DEFAULT_RESULT_COUNT = 3  # Default number of results per entity
HIGH_PROFILE_RESULT_COUNT = 5  # Results for high-profile entities
LOW_PROFILE_RESULT_COUNT = 4  # Results for low-profile entities
TOPIC_RESULT_COUNT = 5  # Results for industry topics

# Claude API configuration for summaries
SUMMARY_BATCH_SIZE = 5  # Number of entities per API call
MAX_TOKENS = 4000  # Max tokens for Claude response
MODEL = 'claude-3-7-sonnet-20250219'  # Claude model to use

# Time period descriptions
TIME_DESCRIPTIONS = {
    'd': 'past day',
    'w': 'past week',
    'm': 'past month',
    'y': 'past year',
    None: 'all time'
}

# Directory configuration
DATA_DIR = 'data'
CONFIG_DIR = 'config'

# Create data directory if it doesn't exist
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# Topic categories and their display order
TOPIC_CATEGORIES = [
    "Annuity Market",
    "Life Insurance Market",
    "Technology",
    "Policy Administration",
    "Industry Events",
    "Business Developments",
    "Outsourcing",
    "Regulatory"
]

# Lists of high and low profile entities (for adaptive search parameters)
HIGH_PROFILE_ENTITIES = [
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

LOW_PROFILE_ENTITIES = [
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