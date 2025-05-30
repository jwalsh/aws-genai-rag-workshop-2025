# AWS setup utilities for RAG
import boto3
import json
import time
from typing import Dict, Any


class AWSSetup:
    """Handles AWS infrastructure setup for RAG applications"""
    
    def __init__(self, region_name='us-east-1'):
        self.region = region_name
        self.session = boto3.Session(region_name=region_name)
        self.bedrock_client = self.session.client('bedrock-agent')
        self.iam_client = self.session.client('iam')
        self.s3_client = self.session.client('s3')
        self.sts_client = self.session.client('sts')
        self.logs_client = self.session.client('logs')
        
    def get_aws_account_info(self) -> Dict[str, str]:
        """Get AWS account information"""
        account_id = self.sts_client.get_caller_identity()['Account']
        return {
            'account_id': account_id,
            'region': self.region
        }
    
    def create_bedrock_execution_role(self, role_name: str) -> str:
        """Create IAM role for Bedrock execution"""
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "bedrock.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        try:
            response = self.iam_client.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description='Role for Bedrock Knowledge Base execution'
            )
            
            # Attach necessary policies
            policies = [
                'arn:aws:iam::aws:policy/AmazonBedrockFullAccess',
                'arn:aws:iam::aws:policy/AmazonS3FullAccess',
                'arn:aws:iam::aws:policy/CloudWatchLogsFullAccess'
            ]
            
            for policy in policies:
                self.iam_client.attach_role_policy(
                    RoleName=role_name,
                    PolicyArn=policy
                )
            
            return response['Role']['Arn']
        except self.iam_client.exceptions.EntityAlreadyExistsException:
            return self.iam_client.get_role(RoleName=role_name)['Role']['Arn']
    
    def create_s3_bucket(self, bucket_name: str) -> str:
        """Create S3 bucket for knowledge base data"""
        try:
            if self.region == 'us-east-1':
                self.s3_client.create_bucket(Bucket=bucket_name)
            else:
                self.s3_client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': self.region}
                )
            return f's3://{bucket_name}'
        except self.s3_client.exceptions.BucketAlreadyExists:
            return f's3://{bucket_name}'
    
    def create_cloudwatch_log_group(self, log_group_name: str) -> str:
        """Create CloudWatch log group"""
        try:
            self.logs_client.create_log_group(logGroupName=log_group_name)
        except self.logs_client.exceptions.ResourceAlreadyExistsException:
            pass
        return log_group_name