#!/usr/bin/env python3
"""Check which AWS environment is currently active."""

import os
import boto3
from botocore.config import Config

def check_environment():
    """Check and display the current AWS environment configuration."""
    print("Current AWS Environment Configuration")
    print("=" * 40)
    
    # Check environment variables
    endpoint_url = os.environ.get('AWS_ENDPOINT_URL', '')
    aws_profile = os.environ.get('AWS_PROFILE', '')
    access_key = os.environ.get('AWS_ACCESS_KEY_ID', '')
    region = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
    
    print(f"AWS_ENDPOINT_URL: {endpoint_url or '(not set - using real AWS)'}")
    print(f"AWS_PROFILE: {aws_profile or '(not set)'}")
    print(f"AWS_ACCESS_KEY_ID: {'***' + access_key[-4:] if access_key else '(not set)'}")
    print(f"AWS_DEFAULT_REGION: {region}")
    
    # Determine active environment
    print("\n" + "-" * 40)
    if endpoint_url:
        print("🏠 Active Environment: LocalStack")
        print(f"   Endpoint: {endpoint_url}")
        if 'localhost' in endpoint_url or '127.0.0.1' in endpoint_url:
            print("   Status: Local development mode")
    elif aws_profile:
        print("☁️  Active Environment: AWS (via profile)")
        print(f"   Profile: {aws_profile}")
    elif access_key:
        print("☁️  Active Environment: AWS (via credentials)")
        if access_key == 'test':
            print("   ⚠️  Warning: Using test credentials")
    else:
        print("❌ No AWS environment configured")
    
    # Test connectivity
    print("\n" + "-" * 40)
    print("Testing connectivity...")
    
    try:
        if endpoint_url:
            # LocalStack
            s3 = boto3.client('s3', endpoint_url=endpoint_url, region_name=region)
        else:
            # Real AWS
            s3 = boto3.client('s3', region_name=region)
        
        buckets = s3.list_buckets()
        print(f"✅ Connected! Found {len(buckets['Buckets'])} S3 buckets")
        
        # List first 3 buckets
        for i, bucket in enumerate(buckets['Buckets'][:3]):
            print(f"   - {bucket['Name']}")
        if len(buckets['Buckets']) > 3:
            print(f"   ... and {len(buckets['Buckets']) - 3} more")
            
    except Exception as e:
        print(f"❌ Connection failed: {str(e)[:100]}")
        if 'credentials' in str(e).lower():
            print("   Hint: Check your AWS credentials configuration")
        elif 'connection' in str(e).lower():
            print("   Hint: Is LocalStack running? Try: make localstack-up")

if __name__ == "__main__":
    check_environment()