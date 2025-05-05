#!/usr/bin/env python
"""
Templates for Claude API prompts
"""

# Client company prompt template
COMPANY_PROMPT_TEMPLATE = """## Executive News Summary Prompt Template

You are tasked with creating concise executive news summaries for {focus}. These summaries will be provided to executives who develop software and back office services for financial service companies. Your output must be direct, factual, and focused only on the most relevant news.

### Instructions:

1. Create a markdown document with the title "{title}" and today's date.

2. For each company, include a section header with the company name.

3. Write a single paragraph (3-5 sentences) that summarizes the most significant recent news for each company. Focus on:
   - Technology initiatives or digital transformation efforts
   - Financial performance metrics
   - Major partnerships or transitions
   - C-suite changes or major leadership transitions
   - New products or services
   - Regulatory or legal developments
   
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

# Competitor company prompt template
COMPETITOR_PROMPT_TEMPLATE = """## Competitive Intelligence Summary Prompt Template

You are tasked with creating concise competitive intelligence summaries for {focus}. These summaries will be provided to executives who develop software and back office services for financial service companies. Your output must be direct, factual, and focused on strategic competitive insights.

### Instructions:

1. Create a markdown document with the title "{title}" and today's date.

2. For each competitor, include a section header with the company name.

3. Write a single paragraph (3-5 sentences) that summarizes the most significant recent competitive developments. Focus on:
   - Market positioning changes and strategic moves
   - New product or service launches that could disrupt the market
   - Technology investments and innovation initiatives
   - Partnerships and acquisitions that strengthen their position
   - Client wins or losses and their market implications
   - Operational changes that may affect competitive position

4. Each paragraph should:
   - Be direct and start immediately with the competitive insight
   - Include specific facts and figures when available
   - Highlight potential threats or opportunities for our business
   - Analyze competitive moves from a strategic perspective
   - Focus on implications for our market position
   - Emphasize information that helps predict future competitive actions

5. Use clear, concise business language appropriate for C-suite executives with competitive strategy focus.

6. Limit each competitor's summary to one paragraph regardless of the amount of news available.

7. Format the final output as a clean, professional markdown document.

8. IMPORTANT: For each competitor, discard any news articles where:
   - The competitor is only mentioned tangentially
   - The news has no strategic competitive implications
   - The article is primarily about financial results without strategic context
   - The article doesn't reveal anything about the competitor's market position or strategy

### Example format:

```markdown
# {title}
[Current Date]

## [Competitor Name]
[Direct competitive intelligence summary focusing on strategic moves, market positioning, and potential threats or opportunities.]

## [Competitor Name]
[Direct competitive intelligence summary focusing on strategic moves, market positioning, and potential threats or opportunities.]
```

This summary will be used by executives to understand competitive threats and opportunities in the marketplace.

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