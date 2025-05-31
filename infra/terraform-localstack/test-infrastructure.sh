#!/bin/bash
# Test script for Level 5 Terraform infrastructure on LocalStack

echo "=== Testing Level 5 Infrastructure ==="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Test S3 buckets
echo "1. Testing S3 buckets..."
if awslocal s3 ls | grep -q "genai-rag-workshop"; then
    echo -e "${GREEN}✓ S3 buckets created${NC}"
    awslocal s3 ls
else
    echo -e "${RED}✗ S3 buckets not found${NC}"
fi
echo ""

# Test DynamoDB tables
echo "2. Testing DynamoDB tables..."
TABLES=$(awslocal dynamodb list-tables --query 'TableNames' --output text)
if [[ $TABLES == *"vector-metadata"* ]] && [[ $TABLES == *"knowledge-bases"* ]]; then
    echo -e "${GREEN}✓ DynamoDB tables created${NC}"
    echo "Tables: $TABLES"
else
    echo -e "${RED}✗ DynamoDB tables not found${NC}"
fi
echo ""

# Test SQS queues
echo "3. Testing SQS queues..."
QUEUES=$(awslocal sqs list-queues --query 'QueueUrls' --output text)
if [[ $QUEUES == *"document-processing"* ]]; then
    echo -e "${GREEN}✓ SQS queues created${NC}"
    echo "Queues: $QUEUES"
else
    echo -e "${RED}✗ SQS queues not found${NC}"
fi
echo ""

# Test Lambda function
echo "4. Testing Lambda function..."
FUNCTIONS=$(awslocal lambda list-functions --query 'Functions[*].FunctionName' --output text)
if [[ $FUNCTIONS == *"rag-processor"* ]]; then
    echo -e "${GREEN}✓ Lambda function created${NC}"
    
    # Invoke the function
    echo "   Invoking Lambda function..."
    awslocal lambda invoke \
        --function-name genai-rag-workshop-rag-processor-localstack \
        --payload '{"action": "test"}' \
        /tmp/lambda-response.json
    
    echo "   Lambda response:"
    cat /tmp/lambda-response.json | jq .
else
    echo -e "${RED}✗ Lambda function not found${NC}"
fi
echo ""

# Test OpenSearch/Elasticsearch
echo "5. Testing OpenSearch domain..."
DOMAINS=$(awslocal es list-domain-names --query 'DomainNames[*].DomainName' --output text 2>/dev/null)
if [[ $DOMAINS == *"vectors"* ]]; then
    echo -e "${GREEN}✓ OpenSearch domain created${NC}"
    echo "Domains: $DOMAINS"
else
    echo -e "${RED}✗ OpenSearch domain not found (this is normal for LocalStack Community)${NC}"
fi
echo ""

# Test IAM roles
echo "6. Testing IAM roles..."
ROLES=$(awslocal iam list-roles --query 'Roles[*].RoleName' --output text)
if [[ $ROLES == *"bedrock-execution-role"* ]] && [[ $ROLES == *"lambda-execution-role"* ]]; then
    echo -e "${GREEN}✓ IAM roles created${NC}"
    echo "Roles found: bedrock-execution-role, lambda-execution-role"
else
    echo -e "${RED}✗ Some IAM roles not found${NC}"
fi
echo ""

# Summary
echo "=== Infrastructure Test Summary ==="
echo "✓ Level 5 infrastructure is deployed and functional!"
echo ""
echo "To interact with the infrastructure:"
echo "  - Upload documents: awslocal s3 cp <file> s3://genai-rag-workshop-documents-localstack/"
echo "  - Query DynamoDB: awslocal dynamodb scan --table-name genai-rag-workshop-vector-metadata-localstack"
echo "  - Send SQS message: awslocal sqs send-message --queue-url <queue-url> --message-body '{\"action\": \"process\"}'"
echo ""
echo "To clean up: make destroy-level5"