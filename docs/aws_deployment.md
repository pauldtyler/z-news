# AWS Lambda Deployment Guide

This guide explains how to test and deploy the Z-News AWS Lambda function locally and then incorporate it into your AWS environment.

## Local Testing

1. **Install Dependencies**:
   ```bash
   pip install -r requirements-cloud.txt
   ```

2. **Test the Function Locally**:
   ```bash
   python aws_lambda.py --company "Prudential Financial, Inc." --time w
   ```

   Additional options:
   - `--time`: Time range (d=day, w=week, m=month, y=year)
   - `--results`: Maximum number of results
   - `--type`: Summary type (client, competitor, consolidated) 
   - `--competitor`: Competitor name (required for consolidated summary)

   Example for consolidated report:
   ```bash
   python aws_lambda.py --company "Prudential Financial, Inc." --time m --type consolidated --competitor "MassMutual"
   ```

## Deploying to AWS Lambda with API Gateway

### Option 1: Deploy Using AWS CLI

1. **Package the Function**:
   
   Create a deployment package that includes your Lambda function and dependencies:
   
   ```bash
   # Create a deployment directory
   mkdir -p deployment/services deployment/config
   
   # Copy necessary files
   cp aws_lambda.py deployment/lambda_function.py
   cp services/search_service.py deployment/services/
   cp services/api_client.py deployment/services/
   cp services/__init__.py deployment/services/
   cp config/config.py deployment/config/
   cp config/__init__.py deployment/config/
   cp config/clients.json deployment/config/
   cp config/competitors.json deployment/config/
   cp utils.py deployment/
   
   # Install dependencies into the deployment directory
   pip install -r requirements-cloud.txt -t deployment/
   
   # Create a zip file
   cd deployment
   zip -r ../z-news-lambda.zip .
   cd ..
   ```

2. **Create the Lambda Function**:
   
   ```bash
   aws lambda create-function \
     --function-name z-news-function \
     --runtime python3.9 \
     --handler lambda_function.lambda_handler \
     --zip-file fileb://z-news-lambda.zip \
     --role arn:aws:iam::<YOUR-ACCOUNT-ID>:role/lambda-role \
     --timeout 30 \
     --memory-size 512
   ```

3. **Set Environment Variables** (if needed):
   
   ```bash
   aws lambda update-function-configuration \
     --function-name z-news-function \
     --environment "Variables={ANTHROPIC_API_KEY=your-anthropic-api-key}"
   ```

4. **Create API Gateway REST API**:
   
   ```bash
   # Create the API
   API_ID=$(aws apigateway create-rest-api \
     --name "Z-News API" \
     --query "id" --output text)
   
   # Get the root resource ID
   ROOT_ID=$(aws apigateway get-resources \
     --rest-api-id $API_ID \
     --query "items[0].id" --output text)
   
   # Create a resource
   RESOURCE_ID=$(aws apigateway create-resource \
     --rest-api-id $API_ID \
     --parent-id $ROOT_ID \
     --path-part "z-news" \
     --query "id" --output text)
   
   # Create a POST method
   aws apigateway put-method \
     --rest-api-id $API_ID \
     --resource-id $RESOURCE_ID \
     --http-method POST \
     --authorization-type NONE
   
   # Set Lambda integration
   aws apigateway put-integration \
     --rest-api-id $API_ID \
     --resource-id $RESOURCE_ID \
     --http-method POST \
     --type AWS_PROXY \
     --integration-http-method POST \
     --uri arn:aws:apigateway:<YOUR-REGION>:lambda:path/2015-03-31/functions/arn:aws:lambda:<YOUR-REGION>:<YOUR-ACCOUNT-ID>:function:z-news-function/invocations
   
   # Deploy the API
   aws apigateway create-deployment \
     --rest-api-id $API_ID \
     --stage-name prod
   ```

5. **Add API Gateway Permission to Invoke Lambda**:
   
   ```bash
   aws lambda add-permission \
     --function-name z-news-function \
     --statement-id apigateway-test \
     --action lambda:InvokeFunction \
     --principal apigateway.amazonaws.com \
     --source-arn "arn:aws:execute-api:<YOUR-REGION>:<YOUR-ACCOUNT-ID>:$API_ID/*/POST/z-news"
   ```

6. **Test the Deployed Function**:
   
   ```bash
   # The invocation URL follows this pattern:
   # https://{API_ID}.execute-api.{YOUR-REGION}.amazonaws.com/{stage_name}/{resource_path}
   
   curl -X POST \
     https://$API_ID.execute-api.<YOUR-REGION>.amazonaws.com/prod/z-news \
     -H "Content-Type: application/json" \
     -d '{"company_name":"Prudential Financial, Inc.", "time_filter":"w", "summary_type":"client"}'
   ```

### Option 2: Deploy Using AWS SAM (Serverless Application Model)

1. **Create a SAM template** (template.yaml):
   
   ```yaml
   AWSTemplateFormatVersion: '2010-09-09'
   Transform: 'AWS::Serverless-2016-10-31'
   
   Resources:
     ZNewsFunction:
       Type: AWS::Serverless::Function
       Properties:
         CodeUri: ./deployment/
         Handler: lambda_function.lambda_handler
         Runtime: python3.9
         Timeout: 30
         MemorySize: 512
         Environment:
           Variables:
             ANTHROPIC_API_KEY: your-anthropic-api-key
         Events:
           ApiEvent:
             Type: Api
             Properties:
               Path: /z-news
               Method: post
   
   Outputs:
     ZNewsApi:
       Description: "API Gateway endpoint URL"
       Value: !Sub "https://${ServerlessRestApi}.execute-api.${AWS::Region}.amazonaws.com/Prod/z-news"
     ZNewsFunction:
       Description: "Lambda Function ARN"
       Value: !GetAtt ZNewsFunction.Arn
   ```

2. **Deploy with SAM CLI**:
   
   ```bash
   # Package the application
   sam package \
     --template-file template.yaml \
     --output-template-file packaged.yaml \
     --s3-bucket your-s3-bucket
   
   # Deploy the application
   sam deploy \
     --template-file packaged.yaml \
     --stack-name z-news-stack \
     --capabilities CAPABILITY_IAM
   ```

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
  "statusCode": 200,
  "headers": {
    "Content-Type": "application/json"
  },
  "body": {
    "company_name": "Prudential Financial, Inc.",
    "time_period": "past week",
    "articles_found": 5,
    "articles": [...],
    "summary": "## Prudential Financial, Inc.\n\nPrudential Financial reported strong Q1 2023 results..." 
  }
}
```

## AWS Lambda Considerations

1. **Execution Time**: The default Lambda timeout is 3 seconds, but this function requires more time to fetch news and generate summaries. Set the timeout to at least 30 seconds.

2. **Memory Allocation**: Consider allocating at least 512MB or more to ensure efficient execution.

3. **Cold Starts**: The function might experience "cold starts" when not used for a while. Consider using Provisioned Concurrency for consistent performance.

4. **API Key**: Protect your API Gateway endpoint with API keys or other authentication methods.

5. **CloudWatch Logs**: Monitor your function's performance and errors using CloudWatch Logs.

6. **Cost Management**: 
   - Lambda billing is based on number of requests and execution time
   - API Gateway charges for API calls and data transfer
   - Consider implementing caching to reduce costs for frequently requested companies

7. **Error Handling**: The Lambda function includes comprehensive error handling to provide meaningful error messages to clients.