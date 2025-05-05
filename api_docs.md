# Z-News API Documentation

## API Overview

The Z-News API provides a serverless service that collects news about financial service companies and generates executive summaries. The API is deployed as an AWS Lambda function with API Gateway.

## Base URL

```
https://c70o4akv4j.execute-api.us-east-1.amazonaws.com/dev
```

## Endpoints

### 1. News and Summary Generation

**Endpoint:** `/z-news`  
**Method:** POST  
**Description:** Fetches news articles for a specified company and generates an executive summary.

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| company_name | string | Yes | Name of the company to search for (e.g., "Prudential Financial, Inc.") |
| time_filter | string | No | Time range for news search (d=day, w=week, m=month, y=year). Default: "w" (week) |
| max_results | number | No | Maximum number of results to return. Default: varies by company profile |
| summary_type | string | No | Type of summary to generate: "client", "competitor", or "consolidated". Default: "client" |
| competitor_name | string | No (Yes for consolidated) | Name of competitor company (required for consolidated summaries) |

**Example Request:**

```bash
curl -X POST https://c70o4akv4j.execute-api.us-east-1.amazonaws.com/dev/z-news \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Prudential Financial, Inc.",
    "time_filter": "w",
    "summary_type": "client"
  }'
```

**Example Response:**

```json
{
  "company_name": "Prudential Financial, Inc.",
  "time_period": "past week",
  "articles_found": 5,
  "articles": [
    {
      "title": "Prudential Financial Reports Strong Q1 Earnings",
      "url": "https://example.com/news/article1",
      "date": "2023-05-03T14:30:00Z",
      "source": "Financial News",
      "excerpt": "Prudential Financial reported Q1 earnings that exceeded analyst expectations...",
      "relevance": 0.8
    },
    ...
  ],
  "summary": "## Prudential Financial, Inc.\n\nPrudential Financial reported strong Q1 2023 results, with net income increasing by 15% year-over-year to $1.35 billion. The company announced a new strategic partnership with XYZ Technology to enhance its digital customer experience platforms. Prudential's asset management division saw significant growth with $24 billion in new inflows, primarily driven by their retirement solutions products. The company reaffirmed its full-year guidance and announced a 5% increase in quarterly dividends, signaling confidence in sustainable growth."
}
```

### 2. Health Check

**Endpoint:** `/healthcheck`  
**Method:** GET  
**Description:** Simple health check to verify the API is running.

**Example Request:**

```bash
curl https://c70o4akv4j.execute-api.us-east-1.amazonaws.com/dev/healthcheck
```

**Example Response:**

```json
{
  "status": "healthy",
  "service": "z-news-api",
  "timestamp": "2023-05-05T15:30:45.123Z"
}
```

## Advanced Usage Examples

### Consolidated Summary

Get a consolidated report comparing a client and competitor:

```bash
curl -X POST https://c70o4akv4j.execute-api.us-east-1.amazonaws.com/dev/z-news \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Prudential Financial, Inc.",
    "competitor_name": "MassMutual",
    "time_filter": "m",
    "summary_type": "consolidated"
  }'
```

### Search with Different Time Ranges

For news from the past day:

```bash
curl -X POST https://c70o4akv4j.execute-api.us-east-1.amazonaws.com/dev/z-news \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Prudential Financial, Inc.",
    "time_filter": "d"
  }'
```

For news from the past month:

```bash
curl -X POST https://c70o4akv4j.execute-api.us-east-1.amazonaws.com/dev/z-news \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Prudential Financial, Inc.",
    "time_filter": "m"
  }'
```

## Error Responses

The API returns standard HTTP status codes:

- 200: Success
- 400: Bad Request (missing required parameters)
- 404: Not Found (company not found)
- 500: Internal Server Error

Example error response:

```json
{
  "error": "Company 'Invalid Company Name' not found in clients.json"
}
```

## Rate Limits and Quotas

- The API is subject to AWS Lambda and API Gateway service quotas
- Default timeout is set to 120 seconds
- Memory allocation is 1024MB

## Deployment Information

This API is deployed using Zappa, a serverless Python framework for AWS Lambda and API Gateway. The deployment creates:

- An AWS Lambda function (z-news-dev)
- API Gateway endpoints
- IAM roles and permissions
- CloudWatch logs for monitoring

## Monitoring and Logs

All API requests are logged to CloudWatch with detailed information including:
- Request parameters
- Response status
- Execution time
- Errors and exceptions

Each request gets a unique request ID for tracking through the logs.