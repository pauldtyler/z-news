#!/usr/bin/env python
"""
AWS Lambda function entry point for Z-News
This file serves as the Lambda entry point, importing from aws_lambda.py
"""

from aws_lambda import lambda_handler

# AWS Lambda will call this function
def lambda_handler(event, context):
    """Entry point for AWS Lambda"""
    from aws_lambda import lambda_handler as handler
    return handler(event, context)