#!/bin/bash
echo "Initializing LocalStack AWS services..."

# Set AWS CLI to use LocalStack
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1
export AWS_ENDPOINT_URL=http://localhost:4566

# Create S3 buckets
awslocal s3 mb s3://workshop-rag-documents
awslocal s3 mb s3://workshop-embeddings
awslocal s3 mb s3://workshop-model-artifacts

# Create DynamoDB tables
awslocal dynamodb create-table \
    --table-name workshop-vector-metadata \
    --attribute-definitions \
        AttributeName=id,AttributeType=S \
        AttributeName=doc_type,AttributeType=S \
    --key-schema AttributeName=id,KeyType=HASH \
    --global-secondary-indexes \
        IndexName=doc-type-index,Keys=[{AttributeName=doc_type,KeyType=HASH}],Projection={ProjectionType=ALL},BillingMode=PAY_PER_REQUEST \
    --billing-mode PAY_PER_REQUEST

# Create IAM role for Bedrock
awslocal iam create-role \
    --role-name BedrockExecutionRole \
    --assume-role-policy-document '{
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "bedrock.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }'

# Create Secrets Manager secrets
awslocal secretsmanager create-secret \
    --name workshop/api-keys \
    --secret-string '{"openai_api_key":"test-key","anthropic_api_key":"test-key"}'

echo "LocalStack initialization complete!"
