#!/usr/bin/env python
"""
Website Monitor Service

This module monitors company websites for updates to blog posts, news, and product releases.
It uses Puppeteer (via Node.js) to handle JavaScript-heavy sites.
"""

import os
import json
import subprocess
import time
import hashlib
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import pandas as pd

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('website_monitor')

# Default configuration path
CONFIG_PATH = "config/websites.json"
OUTPUT_DIR = "data/website_updates"

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

def load_website_config(config_path: str = CONFIG_PATH) -> List[Dict[str, Any]]:
    """
    Load website monitoring configuration from JSON file
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        List of website configurations
    """
    try:
        if not os.path.exists(config_path):
            # Create a default config if none exists
            default_config = [
                {
                    "name": "iPipeline Newsroom",
                    "url": "https://ipipeline.com/resources/newsroom/",
                    "selector": ".elementor-posts-container .elementor-post",
                    "frequency": 86400,  # Check daily (in seconds)
                    "type": "news"
                },
                {
                    "name": "iPipeline Insights",
                    "url": "https://ipipeline.com/resources/insights/",
                    "selector": ".elementor-posts-container .elementor-post",
                    "frequency": 86400,  # Check daily (in seconds)
                    "type": "blog"
                }
            ]
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            # Write default config
            with open(config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            
            return default_config
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        logger.info(f"Loaded monitoring configuration for {len(config)} websites")
        return config
        
    except Exception as e:
        logger.error(f"Error loading website config: {e}")
        return []

def write_puppeteer_script(website: Dict[str, Any]) -> str:
    """
    Generate a temporary Puppeteer script for website scraping
    
    Args:
        website: Website configuration dict
        
    Returns:
        Path to the generated script
    """
    script_dir = os.path.join(OUTPUT_DIR, "scripts")
    os.makedirs(script_dir, exist_ok=True)
    
    site_url = website['url']
    site_selector = website['selector']
    script_path = os.path.join(script_dir, f"scrape_{hashlib.md5(site_url.encode()).hexdigest()}.js")
    
    # Create the Puppeteer script without using f-strings for the JavaScript code
    script_content = """
    const puppeteer = require('puppeteer');

    (async () => {
      const browser = await puppeteer.launch({
        headless: 'new',
        args: ['--no-sandbox', '--disable-setuid-sandbox']
      });
      
      const page = await browser.newPage();
      
      // Set a user agent to avoid detection
      await page.setUserAgent('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36');
      
      const url = "%s";
      const selector = "%s";
      
      console.log("Navigating to " + url);
      
      try {
        // Navigate to the page with extended timeout
        await page.goto(url, {
          waitUntil: 'networkidle2',
          timeout: 90000
        });
        
        // Check if it's an Accenture site, which needs special handling
        if (url.includes('accenture.com')) {
          console.log("Detected Accenture site, applying special handling");
          
          // Accept cookies if prompted
          try {
            const cookieButton = await page.$('button#onetrust-accept-btn-handler');
            if (cookieButton) {
              await cookieButton.click();
              await new Promise(resolve => setTimeout(resolve, 1000));
            }
          } catch (e) {
            console.log("No cookie banner found or could not be clicked");
          }
        }
        
        // Wait for page to fully render using setTimeout (more compatible than waitForTimeout)
        await new Promise(resolve => setTimeout(resolve, 8000));
        
        // Scroll down to load any lazy-loaded content
        await page.evaluate(() => {
          window.scrollTo(0, document.body.scrollHeight / 2);
        });
        
        // Wait a bit more after scrolling
        await new Promise(resolve => setTimeout(resolve, 3000));
        
        console.log("DEBUG: Page loaded, looking for selector");
        
        // Take a screenshot to help with debugging
        await page.screenshot({ path: 'debug_screenshot.png' });
        
        // Log available selectors for debugging
        const availableElements = await page.evaluate(() => {
          return {
            articles: document.querySelectorAll('article').length,
            posts: document.querySelectorAll('.post, .elementor-post').length,
            divs: document.querySelectorAll('div').length
          };
        });
        console.log("Available elements:", JSON.stringify(availableElements));
        
        // Extract all items matching the selector
        const items = await page.evaluate((selector) => {
          // First try the provided selector
          let elements = Array.from(document.querySelectorAll(selector));
          
          // If no elements found, try a more generic selector
          if (elements.length === 0) {
            console.log("WARNING: Primary selector not found, trying alternatives");
            elements = Array.from(document.querySelectorAll('article, .post, .news-item, .blog-post'));
          }
          
          // Still no elements? Try an even more generic approach
          if (elements.length === 0) {
            elements = Array.from(document.querySelectorAll('div[class*="post"], div[class*="article"], div[class*="news"]'));
          }
          
          return elements.map(el => {
            // Get the title - handle various site structures
            let title = '';
            const titleSelectors = [
              'h3', '.elementor-post__title', '.title', '.cmp-teaser__title',
              '.heading', '.card-title', '.rad-card__title', '.card-content .title'
            ];
            
            for (const selector of titleSelectors) {
              const titleEl = el.querySelector(selector);
              if (titleEl) {
                title = titleEl.textContent.trim();
                break;
              }
            }
            
            // If no title found, try to get text from the element itself
            if (!title) {
              title = el.textContent.trim().substring(0, 100);
              if (title.length === 100) title += '...';
            }
            
            // Get the link - handle various site structures
            let link = '';
            const linkEl = el.querySelector('a') || el.closest('a');
            if (linkEl) {
              link = linkEl.href;
            } else {
              // Try to find any link within the element
              const anyLink = el.querySelector('a[href]');
              if (anyLink) link = anyLink.href;
            }
            
            // Get the date if available
            let dateText = '';
            const dateSelectors = [
              '.elementor-post-date', '.date', 'time', '.publish-date',
              '.card-date', '[data-analytics-timestamp]', '.rad-card__date'
            ];
            
            for (const selector of dateSelectors) {
              const dateEl = el.querySelector(selector);
              if (dateEl) {
                dateText = dateEl.textContent.trim() || dateEl.getAttribute('datetime') || dateEl.getAttribute('data-analytics-timestamp') || '';
                break;
              }
            }
            
            // Get the excerpt if available
            let excerpt = '';
            const excerptSelectors = [
              '.elementor-post__excerpt', '.excerpt', '.summary', '.description',
              '.cmp-teaser__description', '.card-description', '.rad-card__description'
            ];
            
            for (const selector of excerptSelectors) {
              const excerptEl = el.querySelector(selector);
              if (excerptEl) {
                excerpt = excerptEl.textContent.trim();
                break;
              }
            }
            
            // If no excerpt, try to find any paragraph
            if (!excerpt) {
              const paragraphEl = el.querySelector('p');
              if (paragraphEl) excerpt = paragraphEl.textContent.trim();
            }
            
            // Create content hash for change detection
            const contentHash = title + excerpt;
            
            return {
              title,
              link,
              date: dateText,
              excerpt,
              contentHash
            };
          });
        }, selector);
        
        console.log(JSON.stringify(items));
      } catch (error) {
        console.error('Error:', error.message);
        process.exit(1);
      } finally {
        await browser.close();
      }
    })();
    """ % (site_url, site_selector)
    
    with open(script_path, 'w') as f:
        f.write(script_content)
    
    return script_path

def run_puppeteer_script(script_path: str) -> Optional[List[Dict[str, Any]]]:
    """
    Execute the Puppeteer script and return the results
    
    Args:
        script_path: Path to the Puppeteer script
        
    Returns:
        List of extracted items or None if failed
    """
    try:
        # Check if Node.js and Puppeteer are installed
        try:
            subprocess.run(['node', '--version'], check=True, capture_output=True)
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.error("Node.js is not installed. Please install Node.js to use the website monitor.")
            return None
        
        # Check if puppeteer is installed
        result = subprocess.run(['npm', 'list', 'puppeteer'], check=False, capture_output=True)
        if 'puppeteer' not in result.stdout.decode():
            logger.warning("Puppeteer is not installed. Attempting to install it...")
            subprocess.run(['npm', 'install', 'puppeteer'], check=True)
        
        # Run the script
        result = subprocess.run(['node', script_path], capture_output=True, text=True, check=True)
        
        # Parse the JSON output
        output = result.stdout.strip()
        items_start = output.find('[')
        if items_start >= 0:
            items_json = output[items_start:]
            return json.loads(items_json)
        else:
            logger.error(f"Invalid output format: {output}")
            return None
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running Puppeteer script: {e}")
        logger.error(f"stderr: {e.stderr}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON output: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error running script: {e}")
        return None

def get_previous_data(website: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Get previously stored data for the website
    
    Args:
        website: Website configuration dictionary
        
    Returns:
        List of previously extracted items
    """
    site_id = hashlib.md5(website['url'].encode()).hexdigest()
    data_path = os.path.join(OUTPUT_DIR, f"{site_id}_data.json")
    
    if not os.path.exists(data_path):
        return []
    
    try:
        with open(data_path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def save_data(website: Dict[str, Any], data: List[Dict[str, Any]]) -> None:
    """
    Save scraped data to disk
    
    Args:
        website: Website configuration dictionary
        data: List of extracted items
    """
    site_id = hashlib.md5(website['url'].encode()).hexdigest()
    data_path = os.path.join(OUTPUT_DIR, f"{site_id}_data.json")
    
    try:
        with open(data_path, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving data: {e}")

def detect_changes(previous_data: List[Dict[str, Any]], 
                  current_data: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Detect new and updated content
    
    Args:
        previous_data: Previously stored data
        current_data: Currently scraped data
        
    Returns:
        Tuple of (new items, updated items)
    """
    # Build a map of previous items by link
    previous_map = {item.get('link', ''): item for item in previous_data if item.get('link')}
    
    new_items = []
    updated_items = []
    
    for item in current_data:
        link = item.get('link', '')
        
        # Skip items without links
        if not link:
            continue
        
        if link not in previous_map:
            # This is a new item
            item['detected_at'] = datetime.now().isoformat()
            new_items.append(item)
        else:
            # Item exists, check if content changed
            prev_item = previous_map[link]
            if item.get('contentHash') != prev_item.get('contentHash'):
                item['detected_at'] = datetime.now().isoformat()
                item['previous_hash'] = prev_item.get('contentHash')
                updated_items.append(item)
    
    return new_items, updated_items

def format_changes_for_df(website: Dict[str, Any], 
                         new_items: List[Dict[str, Any]], 
                         updated_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Format changes for storing in DataFrame format
    
    Args:
        website: Website configuration
        new_items: List of new items
        updated_items: List of updated items
        
    Returns:
        List of formatted change records
    """
    records = []
    
    # Process new items
    for item in new_items:
        records.append({
            'site_name': website.get('name', ''),
            'site_url': website.get('url', ''),
            'content_type': website.get('type', 'news'),
            'title': item.get('title', ''),
            'url': item.get('link', ''),
            'date': item.get('date', ''),
            'excerpt': item.get('excerpt', ''),
            'change_type': 'new',
            'detected_at': item.get('detected_at', datetime.now().isoformat())
        })
    
    # Process updated items
    for item in updated_items:
        records.append({
            'site_name': website.get('name', ''),
            'site_url': website.get('url', ''),
            'content_type': website.get('type', 'news'),
            'title': item.get('title', ''),
            'url': item.get('link', ''),
            'date': item.get('date', ''),
            'excerpt': item.get('excerpt', ''),
            'change_type': 'updated',
            'detected_at': item.get('detected_at', datetime.now().isoformat())
        })
    
    return records

def save_changes_to_csv(changes: List[Dict[str, Any]]) -> Optional[str]:
    """
    Save changes to CSV file
    
    Args:
        changes: List of change records
        
    Returns:
        Path to the CSV file or None if no changes
    """
    if not changes:
        return None
    
    # Create DataFrame from changes
    df = pd.DataFrame(changes)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = os.path.join(OUTPUT_DIR, f"website_updates_{timestamp}.csv")
    
    # Save to CSV
    df.to_csv(csv_path, index=False)
    
    # Update latest reference
    reference_path = os.path.join(OUTPUT_DIR, "latest_website_updates.txt")
    with open(reference_path, 'w') as f:
        f.write(csv_path)
    
    # Generate markdown report for these changes
    md_path = generate_markdown_report(df, timestamp)
    
    return csv_path


def generate_markdown_report(df: pd.DataFrame, timestamp: str) -> str:
    """
    Generate a markdown report for website changes
    
    Args:
        df: DataFrame with website changes
        timestamp: Timestamp string for the filename
        
    Returns:
        Path to the markdown file
    """
    # Create markdown file path
    md_path = os.path.join(OUTPUT_DIR, f"website_changes_{timestamp}.md")
    
    # Group changes by site
    site_groups = df.groupby('site_name')
    
    # Start building markdown content
    md_content = f"# Website Changes Report\n\n"
    md_content += f"*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
    
    # Summary section
    md_content += "## Summary\n\n"
    md_content += f"- **Total changes detected:** {len(df)}\n"
    md_content += f"- **Sites with changes:** {len(site_groups)}\n"
    
    # Changes by type
    change_types = df['change_type'].value_counts()
    md_content += "- **Changes by type:**\n"
    for change_type, count in change_types.items():
        md_content += f"  - {change_type.capitalize()}: {count}\n"
    md_content += "\n"
    
    # Detailed changes by site
    md_content += "## Changes by Site\n\n"
    
    for site_name, group in site_groups:
        md_content += f"### {site_name}\n\n"
        
        # Site metadata
        site_url = group['site_url'].iloc[0]
        md_content += f"- **Site URL:** [{site_url}]({site_url})\n"
        md_content += f"- **Content type:** {group['content_type'].iloc[0]}\n"
        md_content += f"- **Changes detected:** {len(group)}\n\n"
        
        # List all changes for this site
        for _, row in group.iterrows():
            md_content += f"#### {row['title']}\n\n"
            md_content += f"- **Type:** {row['change_type'].capitalize()}\n"
            
            if not pd.isna(row['url']) and row['url']:
                md_content += f"- **URL:** [{row['url']}]({row['url']})\n"
            
            if not pd.isna(row['date']) and row['date']:
                md_content += f"- **Date:** {row['date']}\n"
            
            if not pd.isna(row['excerpt']) and row['excerpt']:
                md_content += f"- **Excerpt:** {row['excerpt']}\n"
            
            md_content += f"- **Detected at:** {row['detected_at']}\n\n"
    
    # Write to file
    with open(md_path, 'w') as f:
        f.write(md_content)
    
    # Update latest markdown reference
    reference_path = os.path.join(OUTPUT_DIR, "latest_website_changes.md")
    with open(reference_path, 'w') as f:
        f.write(md_content)
    
    logger.info(f"Generated markdown report: {md_path}")
    return md_path

def monitor_website(website: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Monitor a single website for changes
    
    Args:
        website: Website configuration dictionary
        
    Returns:
        Tuple of (new items, updated items)
    """
    logger.info(f"Monitoring website: {website.get('name', 'Unnamed')}")
    
    # Generate and run Puppeteer script
    script_path = write_puppeteer_script(website)
    current_data = run_puppeteer_script(script_path)
    
    if current_data is None:
        logger.error(f"Failed to scrape {website.get('name', website.get('url', 'Unknown'))}")
        return [], []
    
    logger.info(f"Scraped {len(current_data)} items from {website.get('name', '')}")
    
    # Get previous data for comparison
    previous_data = get_previous_data(website)
    
    # Detect changes
    new_items, updated_items = detect_changes(previous_data, current_data)
    
    logger.info(f"Found {len(new_items)} new items and {len(updated_items)} updated items")
    
    # Save updated data (merge new/updated with existing)
    save_data(website, current_data)
    
    return new_items, updated_items

def monitor_all_websites() -> Optional[str]:
    """
    Monitor all configured websites for changes
    
    Returns:
        Path to the CSV file with changes, or None if no changes detected
    """
    logger.info("Starting website monitoring")
    
    # Load website configurations
    websites = load_website_config()
    
    if not websites:
        logger.warning("No websites configured for monitoring")
        return None
    
    # Process each website
    all_changes = []
    
    for website in websites:
        try:
            # Add delay to avoid hitting rate limits
            if website != websites[0]:
                delay = 5  # 5 second delay between sites
                logger.info(f"Waiting {delay} seconds before next site...")
                time.sleep(delay)
            
            # Monitor the website
            new_items, updated_items = monitor_website(website)
            
            # Format changes for DataFrame
            changes = format_changes_for_df(website, new_items, updated_items)
            all_changes.extend(changes)
            
        except Exception as e:
            logger.error(f"Error monitoring {website.get('name', '')}: {e}")
    
    # Save all changes to CSV
    if all_changes:
        csv_path = save_changes_to_csv(all_changes)
        logger.info(f"Saved {len(all_changes)} changes to {csv_path}")
        return csv_path
    else:
        logger.info("No changes detected on any websites")
        return None

if __name__ == "__main__":
    import argparse
    
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Monitor websites for updates")
    parser.add_argument("--config", help="Path to website configuration JSON file")
    
    args = parser.parse_args()
    
    # Use specified config path or default
    config_path = args.config or CONFIG_PATH
    
    # Run the monitoring
    result = monitor_all_websites()
    
    if result:
        print(f"Changes detected and saved to {result}")
    else:
        print("No changes detected")