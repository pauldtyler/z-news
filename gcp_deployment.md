# Google Cloud Function Deployment Guide

This guide explains how to test and deploy the Z-News cloud function locally and then incorporate it into the company-wide Google Cloud Platform repository.

## Local Testing

1. **Install Dependencies**:
   ```bash
   pip install -r requirements-cloud.txt
   ```

2. **Test the Function Locally**:
   ```bash
   python cloud_function.py --company "Prudential Financial, Inc." --time w
   ```

   Additional options:
   - `--time`: Time range (d=day, w=week, m=month, y=year)
   - `--results`: Maximum number of results
   - `--type`: Summary type (client, competitor, consolidated) 
   - `--competitor`: Competitor name (required for consolidated summary)
   - `--no-csv`: Don't save results to CSV
   - `--no-summary`: Don't save summary to markdown file

   Example for consolidated report:
   ```bash
   python cloud_function.py --company "Prudential Financial, Inc." --time m --type consolidated --competitor "MassMutual"
   ```

## Deploying to Google Cloud Functions

### Option 1: Deploy Standalone for Testing

1. **Authenticate with GCP**:
   ```bash
   gcloud auth login
   ```

2. **Set Your Project**:
   ```bash
   gcloud config set project YOUR_PROJECT_ID
   ```

3. **Deploy the Function**:
   ```bash
   gcloud functions deploy z-news-function \
     --gen2 \
     --runtime=python311 \
     --region=us-central1 \
     --source=. \
     --entry-point=generate_news_for_company \
     --trigger-http \
     --allow-unauthenticated
   ```

4. **Test the Deployed Function**:
   ```bash
   curl -X POST "https://FUNCTION_URL" \
     -H "Content-Type: application/json" \
     -d '{"company_name":"Prudential Financial, Inc.", "time_filter":"w", "summary_type":"client"}'
   ```

### Option 2: Incorporate into Company-Wide GCP Repository

1. **Create a Directory in the Company Repo**:
   Create a new directory for the Z-News function in your company's GCP repository.

2. **Copy Required Files**:
   - `cloud_function.py` (main function code)
   - `requirements-cloud.txt` (renamed to `requirements.txt`)
   - Required modules from the original codebase:
     - `services/search_service.py`
     - `services/api_client.py`
     - `config/config.py`
     - Create a simplified version of `utils.py` with only needed functions
     - Copy relevant JSON config files

3. **Modify Import Statements**:
   Update import statements in the cloud function to match the repository structure.

4. **Add CI/CD Configuration**:
   - Add necessary CI/CD configuration files according to your company standards
   - Include automated tests and deployment workflows

5. **Documentation**:
   - Add README explaining the function's purpose and usage
   - Document API endpoints and parameters
   - Include examples for common use cases

6. **Submit Pull Request**:
   Create a pull request according to your company's contribution guidelines.

## API Usage

### HTTP Request Parameters

**POST Request Body (JSON)**:
```json
{
  "company_name": "Prudential Financial, Inc.",
  "time_filter": "w",
  "max_results": 5,
  "summary_type": "client",
  "competitor_name": "MassMutual"
}
```

- `company_name` (required): Name of the company to search for
- `time_filter` (optional): Time filter (d=day, w=week, m=month, y=year), defaults to week
- `max_results` (optional): Maximum number of results to return
- `summary_type` (optional): Type of summary (client, competitor, consolidated), defaults to client
- `competitor_name` (required for consolidated): Name of competitor for consolidated summary

### Example Response

```json
{
  "company_name": "Prudential Financial, Inc.",
  "time_period": "past week",
  "articles_found": 5,
  "articles": [...],
  "summary": "## Prudential Financial, Inc.\n\nPrudential Financial reported strong Q1 2023 results..." 
}
```

## Security Considerations

1. **API Key**: Consider adding authentication to the cloud function
2. **Rate Limiting**: Implement rate limiting to prevent abuse
3. **Data Privacy**: Ensure that no sensitive information is exposed in logs or responses
4. **Error Handling**: Implement proper error handling to prevent information leakage
