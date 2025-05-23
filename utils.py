#!/usr/bin/env python
"""
Utility functions for Z-News application
"""

import json
import os
import time
import random
from datetime import datetime
from typing import Dict, List, Tuple, Union, Optional, Any

# Type aliases
EntityType = str  # "client", "competitor", or "topic"
Entity = Dict[str, str]  # Dict with at least "name" and "query" keys
EntityTuple = Tuple[str, str]  # (name, query) format
TopicTuple = Tuple[str, str, str]  # (category, name, query) format

def load_entities(entity_type: EntityType) -> List[Dict[str, str]]:
    """
    Load entities from the appropriate configuration file
    
    Args:
        entity_type: Type of entities to load ("client", "competitor", or "topic")
        
    Returns:
        List of entity dictionaries with name and query keys
    """
    config_file = f"config/{entity_type}s.json"
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading {entity_type} data: {e}")
        return []

def convert_entities_to_tuples(entities: List[Dict[str, str]], entity_type: EntityType = "client") -> List[Union[EntityTuple, TopicTuple]]:
    """
    Convert entity dictionaries to tuples format for backward compatibility
    
    Args:
        entities: List of entity dictionaries
        entity_type: Type of entities ("client", "competitor", or "topic")
        
    Returns:
        List of entity tuples in the appropriate format for the entity type
    """
    if entity_type == "topic":
        # Topics are 3-tuples: (category, name, query)
        return [(entity.get("category", "General"), entity["name"], entity["query"]) for entity in entities]
    else:
        # Clients and competitors are 2-tuples: (name, query)
        return [(entity["name"], entity["query"]) for entity in entities]

def get_entity_name(entity_tuple: Union[EntityTuple, TopicTuple, str]) -> str:
    """
    Extract entity name from tuple
    
    Args:
        entity_tuple: Entity tuple or string
        
    Returns:
        Entity name as string
    """
    if isinstance(entity_tuple, tuple):
        return entity_tuple[0] if len(entity_tuple) <= 2 else entity_tuple[1]
    return entity_tuple

def get_entity_query(entity_tuple: Union[EntityTuple, TopicTuple, str]) -> str:
    """
    Extract search query from entity tuple
    
    Args:
        entity_tuple: Entity tuple or string
        
    Returns:
        Search query as string
    """
    if isinstance(entity_tuple, tuple):
        # For topic (3-tuple with category, name, query)
        if len(entity_tuple) > 2:
            return entity_tuple[2]
        # For client/competitor (2-tuple with name, query)
        elif len(entity_tuple) > 1:
            return entity_tuple[1] or entity_tuple[0]
    # If not a tuple or no query specified, use the name itself
    return entity_tuple

def get_topic_category(topic_tuple: Union[TopicTuple, str]) -> str:
    """
    Extract category from topic tuple
    
    Args:
        topic_tuple: Topic tuple or string
        
    Returns:
        Category as string, or "General" if not found
    """
    if isinstance(topic_tuple, tuple) and len(topic_tuple) > 2:
        return topic_tuple[0]
    return "General"

def add_jitter(delay: float, percent: float = 0.2) -> float:
    """
    Add random jitter to a delay time to avoid request pattern detection
    
    Args:
        delay: Base delay time in seconds
        percent: Percentage of jitter to add (0.2 = ±20%)
        
    Returns:
        Delay with jitter added
    """
    jitter = delay * percent * (2 * random.random() - 1)
    return max(1, delay + jitter)

def generate_timestamp() -> str:
    """
    Generate a timestamp string for file naming
    
    Returns:
        Timestamp string in the format "YYYYMMDD_HHMMSS"
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def format_api_prompt(template: str, **kwargs: Any) -> str:
    """
    Format a prompt template with the given parameters
    
    Args:
        template: Prompt template string
        **kwargs: Parameters to insert into the template
        
    Returns:
        Formatted prompt string
    """
    return template.format(**kwargs)

def save_latest_file_reference(file_path: str, entity_type: EntityType) -> None:
    """
    Save a reference to the latest file of a given type
    
    Args:
        file_path: Path to the file
        entity_type: Type of data in the file
    """
    reference_file = f"data/latest_{entity_type}_csv.txt"
    try:
        with open(reference_file, "w") as f:
            f.write(file_path)
    except Exception as e:
        print(f"Error saving reference to latest {entity_type} file: {e}")

def calculate_relevance_score(title: str, excerpt: str, entity_name: str) -> float:
    """
    Calculate a relevance score for an article based on how central the entity is to the content.
    
    Args:
        title: The article title
        excerpt: The article excerpt or body
        entity_name: The entity name to check for
        
    Returns:
        A relevance score between 0 and 1
    """
    # Convert all to lowercase for case-insensitive matching
    title_lower = title.lower()
    excerpt_lower = excerpt.lower()
    
    # Extract the main part of the entity name (remove "Inc.", "& Co.", etc.)
    main_entity_parts = entity_name.split(',')[0].strip()
    main_entity = main_entity_parts.split('&')[0].strip()
    main_entity = main_entity.split(':')[-1].strip()  # Handle topic format "Category: Topic"
    
    # Generate variations of the entity name
    entity_variations = [
        entity_name.lower(),
        main_entity.lower()
    ]
    
    # Add additional common variations for specific entities
    if "J.P. Morgan" in entity_name:
        entity_variations.extend(["jpmorgan", "jp morgan", "j.p. morgan"])
    elif "Legal & General" in entity_name:
        entity_variations.extend(["legal and general", "l&g"])
    
    # Base score components
    title_score = 0
    excerpt_score = 0
    position_score = 0
    
    # Check title (high importance)
    for variation in entity_variations:
        if variation in title_lower:
            title_score = 0.6
            # Higher score if entity is at the beginning of the title
            if title_lower.find(variation) < len(title_lower) // 3:
                title_score = 0.7
            break
    
    # Check excerpt (lower importance)
    for variation in entity_variations:
        if variation in excerpt_lower:
            excerpt_score = 0.3
            # Calculate position - higher score if entity appears earlier
            position = excerpt_lower.find(variation)
            if position < len(excerpt_lower) // 4:  # In the first quarter
                position_score = 0.2
            elif position < len(excerpt_lower) // 2:  # In the first half
                position_score = 0.1
            break
    
    # Calculate final score
    final_score = title_score + excerpt_score + position_score
    
    # Cap at 1.0
    return min(final_score, 1.0)