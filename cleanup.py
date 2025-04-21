#!/usr/bin/env python
"""
Cleanup script for z-news project that keeps only the most recent data files
and removes older generated files to maintain a clean workspace.
"""

import os
import glob
import re
from datetime import datetime
from collections import defaultdict

def get_timestamp(filename):
    """Extract timestamp from filename format with pattern *_YYYYMMDD_HHMMSS.*"""
    match = re.search(r'_(\d{8}_\d{6})\.', filename)
    if match:
        timestamp_str = match.group(1)
        try:
            return datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
        except ValueError:
            pass
    return None

def cleanup_files(file_pattern, keep_latest=1):
    """
    Clean up files matching pattern, keeping only the specified number of latest files.
    
    Args:
        file_pattern: Glob pattern to match files
        keep_latest: Number of latest files to keep for each type
    """
    files = glob.glob(file_pattern)
    
    # Group files by type (before timestamp)
    file_groups = defaultdict(list)
    for file in files:
        basename = os.path.basename(file)
        prefix = re.sub(r'_\d{8}_\d{6}\..*$', '', basename)
        timestamp = get_timestamp(basename)
        if timestamp:
            file_groups[prefix].append((file, timestamp))
    
    # For each group, sort by timestamp and delete older files
    deleted = []
    for prefix, file_list in file_groups.items():
        # Sort files by timestamp (newest first)
        file_list.sort(key=lambda x: x[1], reverse=True)
        
        # Keep the latest files, delete the rest
        for file, _ in file_list[keep_latest:]:
            os.remove(file)
            deleted.append(file)
    
    return deleted

def main():
    """Main function to clean up project files."""
    print("Starting cleanup process...")
    
    # List of patterns to match files that should be cleaned up
    patterns = [
        "client_news_*.csv",
        "data/client_news_*.csv",
        "data/competitor_news_*.csv",
        "data/weekly_news_*.csv",
        "data/executive_summary_*.md",
        "data/claude_prompt_*.txt"
    ]
    
    # Keep the latest N files for each type
    keep_latest = 2
    
    total_deleted = []
    for pattern in patterns:
        deleted = cleanup_files(pattern, keep_latest)
        total_deleted.extend(deleted)
    
    # Print summary
    print(f"Cleanup complete! Deleted {len(total_deleted)} files.")
    if total_deleted:
        print("Deleted files:")
        for file in total_deleted:
            print(f"  - {file}")

if __name__ == "__main__":
    main()