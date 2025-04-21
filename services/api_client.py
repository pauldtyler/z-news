#!/usr/bin/env python
"""
API client service for interacting with Claude API
"""

import time
import os
from typing import Optional, Dict, List, Any

from anthropic import Anthropic
from dotenv import load_dotenv

from config.config import MODEL, MAX_TOKENS

# Load environment variables
load_dotenv()

class ClaudeApiClient:
    """Client for interacting with Claude API with retry mechanism"""
    
    def __init__(self):
        """Initialize the Claude API client"""
        self.api_key = os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("No API key found. Please set ANTHROPIC_API_KEY in your .env file.")
        
        self.client = Anthropic(api_key=self.api_key)
        self.model = MODEL
        self.max_tokens = MAX_TOKENS
    
    def generate_summary(self, prompt: str, system_prompt: Optional[str] = None,
                        attempt: int = 1, max_attempts: int = 3) -> Optional[str]:
        """
        Call Claude API to generate a summary with retry mechanism
        
        Args:
            prompt: The prompt to send to Claude
            system_prompt: Optional system prompt to guide Claude's behavior
            attempt: Current attempt number
            max_attempts: Maximum number of retry attempts
            
        Returns:
            Generated summary text, or None if failed after max attempts
        """
        if system_prompt is None:
            system_prompt = 'You are an expert financial analyst creating executive summaries.'
            
        print('Calling Claude API to generate executive summary...')
        
        try:
            # Call Claude API
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=0.0,
                system=system_prompt,
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
                return self.generate_summary(prompt, system_prompt, attempt + 1, max_attempts)
            else:
                print("Max attempts reached. Giving up.")
                return None