"""AWS client configuration for LocalStack and production environments."""

import os
import boto3
from functools import lru_cache
from typing import Any, Optional

def get_aws_client(service_name: str, **kwargs) -> Any:
    """Get AWS client configured for LocalStack or production."""
    config = {
        "region_name": os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
    }
    
    # Use LocalStack endpoint if configured
    endpoint_url = os.getenv("AWS_ENDPOINT_URL")
    if endpoint_url:
        config["endpoint_url"] = endpoint_url
        config["aws_access_key_id"] = os.getenv("AWS_ACCESS_KEY_ID", "test")
        config["aws_secret_access_key"] = os.getenv("AWS_SECRET_ACCESS_KEY", "test")
    
    config.update(kwargs)
    return boto3.client(service_name, **config)

@lru_cache(maxsize=None)
def get_bedrock_runtime_client():
    """Get Bedrock runtime client."""
    return get_aws_client("bedrock-runtime")

@lru_cache(maxsize=None)
def get_s3_client():
    """Get S3 client."""
    return get_aws_client("s3")

@lru_cache(maxsize=None)
def get_dynamodb_client():
    """Get DynamoDB client."""
    return get_aws_client("dynamodb")

@lru_cache(maxsize=None)
def get_sagemaker_client():
    """Get SageMaker client."""
    return get_aws_client("sagemaker")
