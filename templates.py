#!/usr/bin/env python
"""
Templates for Claude API prompts
"""

# Client/competitor company prompt template
COMPANY_PROMPT_TEMPLATE = """## Executive News Summary Prompt Template

You are tasked with creating concise executive news summaries for {focus}. These summaries will be provided to executives who develop software and back office services for financial service companies. Your output must be direct, factual, and focused only on the most relevant news.

### Instructions:

1. Create a markdown document with the title "{title}" and today's date.

2. For each company, include a section header with the company name.

3. Write a single paragraph (3-5 sentences) that summarizes the most significant recent news for each company. Focus on:
   - Financial performance metrics
   - Leadership changes
   - New products or services
   - Major partnerships or transitions
   - Regulatory or legal developments
   - Facility changes or expansions
   - Technology initiatives or digital transformation efforts

4. Each paragraph should:
   - Be direct and start immediately with the news
   - Include specific facts and figures when available
   - Avoid commentary about the frequency of media mentions
   - Focus on items relevant to software and back office service providers
   - Omit subjective assessments or speculations
   - Only include news where the company plays a significant role (not just mentioned in passing)

5. Use clear, concise business language appropriate for C-suite executives.

6. Limit each company's summary to one paragraph regardless of the amount of news available.

7. Format the final output as a clean, professional markdown document.

8. IMPORTANT: For each company, discard any news articles where:
   - The company is only mentioned tangentially or in passing
   - The company is not a primary subject of the article
   - The article is about industry trends with only a minor reference to the company
   - The article primarily focuses on a different company and only mentions this company for context

### Example format:

```markdown
# {title}
[Current Date]

## [Company Name]
[Direct news summary in a single paragraph with key facts and developments relevant to software and back office service providers.]

## [Company Name]
[Direct news summary in a single paragraph with key facts and developments relevant to software and back office service providers.]
```

This summary will be used by executives to understand the current context of {focus} businesses and identify potential service opportunities or risks.

### News Data:
{news_data}
"""

# Industry topic prompt template
TOPIC_PROMPT_TEMPLATE = """## Industry Topic News Summary Prompt Template

You are tasked with creating concise industry topic summaries for the insurance and annuity markets. These summaries will be provided to executives who develop software and back office services for financial service companies. Your output must be direct, factual, and focused on significant industry trends and insights.

### Instructions:

1. Each topic name will be provided in the format "Category: Topic Name". Extract the category and topic name.

2. For each topic, write a single paragraph (3-5 sentences) that summarizes the most significant recent news and trends. Focus on:
   - Market trends and forecasts
   - Technological advancements
   - Regulatory developments
   - Industry-wide challenges or opportunities
   - Emerging solutions or best practices
   - Industry event highlights

3. Each paragraph should:
   - Be direct and start immediately with the key insights
   - Include specific facts, figures, and statistics when available
   - Focus on information relevant to insurance/annuity software and service providers
   - Highlight actionable insights when possible
   - Provide a balanced view of the topic area
   - Emphasize market-level insights rather than individual company news

4. Use clear, concise business language appropriate for C-suite executives with deep industry knowledge.

5. Limit each topic's summary to one paragraph regardless of the amount of news available.

6. Format your response as a clean, professional markdown document with proper hierarchical structure.
   - Include the full topic name (including category) as the heading for each section
   - If multiple topics from the same category are present, keep them grouped together

7. IMPORTANT: Ensure that each topic summary:
   - Offers genuine insights rather than just summarizing the articles
   - Identifies implications for insurance/annuity technology providers
   - Highlights underlying patterns or emerging trends
   - Avoids redundancy with other topic summaries

### Example format:

```markdown
# {title}
[Current Date]

## [Category: Topic Name]
[Direct summary paragraph with key insights and developments relevant to insurance technology providers.]

## [Category: Topic Name]
[Direct summary paragraph with key insights and developments relevant to insurance technology providers.]
```

This summary will be used by executives to understand current industry trends and identify potential opportunities for insurance and annuity technology innovation.

### News Data:
{news_data}
"""

# Combined report template header
COMBINED_REPORT_HEADER = """# Financial Services Industry Executive Summary

{current_date}

## Overview

This report provides a comprehensive weekly summary of key developments across the financial services industry, organized by market segments, industry topics, and individual companies.

"""