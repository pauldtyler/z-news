# Zappa Deployment Guide for Z-News API

This guide explains how to deploy the Z-News API using Zappa, a serverless Python framework that makes it easy to build and deploy Python applications on AWS Lambda and API Gateway.

## Project Structure

The application is organized for optimal deployment with Zappa:

```
z-news/
├── app.py                  # Flask application (main entry point)
├── zappa_settings.json     # Zappa configuration
├── requirements-zappa.txt  # Dependencies
├── services/
│   ├── __init__.py
│   ├── api_client.py       # Claude API client
│   └── search_service.py   # Search service
├── config/
│   ├── __init__.py
│   ├── config.py           # Configuration settings
│   ├── clients.json        # Client data
│   └── competitors.json    # Competitor data
└── utils.py                # Utility functions
```

## Local Setup and Testing

1. **Create a Virtual Environment**:
   ```bash
   python -m venv zappa-venv
   source zappa-venv/bin/activate  # On Windows: zappa-venv\\Scripts\\activate
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements-zappa.txt
   ```

3. **Set Environment Variables**:
   ```bash
   # Linux/Mac
   export ANTHROPIC_API_KEY=your-anthropic-api-key
   
   # Windows
   set ANTHROPIC_API_KEY=your-anthropic-api-key
   ```

4. **Run the Flask App Locally**:
   ```bash
   python app.py
   ```

5. **Test the Local API**:
   ```bash
   curl -X POST http://127.0.0.1:5000/z-news \
     -H "Content-Type: application/json" \
     -d '{"company_name":"Prudential Financial, Inc.", "time_filter":"w", "summary_type":"client"}'
   ```

   ```bash
   curl -X POST http://127.0.0.1:5000/z-news \
     -H "Content-Type: application/json" \
     -d '{"company_name":"Symetra", "time_filter":"d", "summary_type":"client"}'
   ```

## Zappa Configuration

The `zappa_settings.json` file is pre-configured with two environments:

- **dev**: Development environment with basic settings
- **prod**: Production environment with enhanced settings (API key, more memory, etc.)

Before deployment, customize:
1. `s3_bucket`: Create an S3 bucket for your deployments
2. `aws_region`: Set your preferred AWS region
3. `profile_name`: Your AWS CLI profile name
4. Environment variables: Set your API keys securely 

## Deployment Steps

### 1. Configure AWS Credentials

Ensure your AWS credentials are configured:

```bash
aws configure
```

Or set up a profile in `~/.aws/credentials`:

```
[default]
aws_access_key_id = YOUR_ACCESS_KEY
aws_secret_access_key = YOUR_SECRET_KEY
```

### 2. Update Environment Variables

In the Zappa settings file, ensure sensitive information is not committed to source control. Instead, update during deployment:

```bash
# Securely store API key in AWS Systems Manager Parameter Store
aws ssm put-parameter \
  --name "/z-news/ANTHROPIC_API_KEY" \
  --value "your-api-key" \
  --type SecureString \
  --overwrite
```

Then update `zappa_settings.json` to use this parameter:

```json
"environment_variables": {
  "ANTHROPIC_API_KEY": "${ssm:/z-news/ANTHROPIC_API_KEY}"
}
```

### 3. Initial Deployment

Deploy to the development environment:

```bash
zappa deploy dev
```

This command will:
1. Package your application
2. Upload it to the specified S3 bucket
3. Create the Lambda function
4. Set up API Gateway
5. Create and configure the necessary IAM roles

The command will output the URL for your deployed API.

### 4. Updating the Deployment

After making changes to your code, update the deployment:

```bash
zappa update dev
```

### 5. Production Deployment

When ready for production:

```bash
zappa deploy prod
```

## API Usage

The API provides the following endpoints:

### `/z-news` (POST)

Search for news about a specific company and generate summaries.

**Request Body**:
```json
{
  "company_name": "Prudential Financial, Inc.",
  "time_filter": "w",
  "max_results": 5,
  "summary_type": "client",
  "competitor_name": "MassMutual"
}
```

Parameters:
- `company_name` (required): Name of the company to search for
- `time_filter` (optional): Time filter (d=day, w=week, m=month, y=year), defaults to week
- `max_results` (optional): Maximum number of results to return
- `summary_type` (optional): Type of summary (client, competitor, consolidated), defaults to client
- `competitor_name` (required for consolidated): Name of competitor for consolidated summary

**Example Request**:
```bash
curl -X POST https://YOUR_API_GATEWAY_URL/dev/z-news \
  -H "Content-Type: application/json" \
  -d '{"company_name":"Prudential Financial, Inc.", "time_filter":"w", "summary_type":"client"}'
```
Test your API with:
```bash

curl -X POST https://3b46lk7dvk.execute-api.us-east-1.amazonaws.com/dev/z-news \
  -H "Content-Type: application/json" \
  -d '{"company_name":"Prudential Financial, Inc.", "time_filter":"w", "summary_type":"client"}'
```
```bash
curl https://3b46lk7dvk.execute-api.us-east-1.amazonaws.com/dev/healthcheck
```
### `/healthcheck` (GET)

A simple endpoint to verify the API is running.

**Example Request**:
```bash
curl https://YOUR_API_GATEWAY_URL/dev/healthcheck
```

## Monitoring and Management

### Viewing Logs

```bash
zappa tail dev
```

### Scheduling Events

You can schedule the function to run on a regular basis:

```json
"events": [
  {
    "function": "app.generate_news_for_company",
    "expression": "rate(1 day)"
  }
]
```

### Custom Domain

To set up a custom domain for production:

1. Configure in `zappa_settings.json`:
   ```json
   "domain": "api.yourdomain.com",
   "certificate_arn": "your-certificate-arn"
   ```

2. Deploy or update:
   ```bash
   zappa update prod
   ```

3. Update your DNS settings to point to the API Gateway domain.

## Troubleshooting

### Common Issues

1. **Dependencies Not Found**: 
   - Ensure all dependencies are in `requirements-zappa.txt`
   - For complex packages, consider using Lambda Layers

2. **Path Issues**:
   - Lambda has a different file system, ensure paths are relative
   - Use the `CONFIG_PATH` environment variable to locate config files

3. **Timeouts**:
   - Increase `timeout_seconds` in `zappa_settings.json` if operations take too long

4. **Memory Limitations**:
   - Increase `memory_size` for faster processing and more memory

### Debugging Tips

1. Enable verbose mode in Zappa:
   ```bash
   zappa update dev --verbose
   ```

2. Test functions locally before deployment:
   ```python
   from app import generate_news_for_company
   # Test with sample data
   ```

3. Check CloudWatch logs for detailed error messages:
   ```bash
   zappa tail dev --since 1h
   ```

## Cleaning Up

To remove the deployment:

```bash
zappa undeploy dev
```

This will remove the Lambda function, API Gateway configuration, and related resources.

## Security Considerations

1. **API Security**:
   - Use `api_key_required: true` in production
   - Consider integrating with AWS Cognito for user authentication

2. **Environment Variables**:
   - Never commit sensitive values to source control
   - Use AWS Systems Manager Parameter Store for secrets

3. **IAM Permissions**:
   - Review and restrict the IAM role permissions as needed
   - Follow the principle of least privilege

4. **Rate Limiting**:
   - Configure API Gateway to implement rate limiting
   - Add CORS headers if needed for web clients