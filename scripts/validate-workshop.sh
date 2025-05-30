#!/bin/bash
# AWS GenAI RAG Workshop Validation Script
# Run this to quickly check all workshop components

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo -e "\n${YELLOW}=== $1 ===${NC}"
}

check_command() {
    local name=$1
    local command=$2
    printf "%-30s" "$name"
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✅${NC}"
        return 0
    else
        echo -e "${RED}❌${NC}"
        return 1
    fi
}

check_with_output() {
    local name=$1
    local command=$2
    printf "%-30s" "$name"
    local result=$(eval "$command" 2>/dev/null || echo "0")
    if [ "$result" != "0" ] && [ -n "$result" ]; then
        echo -e "${GREEN}✅ ($result)${NC}"
        return 0
    else
        echo -e "${RED}❌${NC}"
        return 1
    fi
}

# Main validation
main() {
    echo "AWS GenAI RAG Workshop Validation"
    echo "================================="
    echo "Time: $(date)"
    echo "Region: ${AWS_REGION:-us-west-2}"
    
    # Check if .env exists
    if [ ! -f .env ]; then
        echo -e "${RED}ERROR: .env file not found${NC}"
        echo "Please create .env with your AWS credentials"
        exit 1
    fi
    
    # Source environment
    source .env
    
    print_header "1. Environment Check"
    check_command "Python" "python --version"
    check_command "AWS CLI" "aws --version"
    check_command "jq installed" "which jq"
    check_command "direnv active" "echo \$DIRENV_DIR"
    
    print_header "2. AWS Authentication"
    if check_command "AWS credentials" "aws sts get-caller-identity"; then
        ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
        echo "   Account ID: $ACCOUNT_ID"
    else
        echo -e "${RED}Cannot proceed without AWS credentials${NC}"
        exit 1
    fi
    
    print_header "3. Bedrock Access"
    check_with_output "Bedrock models available" \
        "aws bedrock list-foundation-models --region us-west-2 --query 'length(modelSummaries)' --output text"
    
    check_command "Titan Embed model" \
        "aws bedrock list-foundation-models --region us-west-2 --query 'modelSummaries[?modelId==\`amazon.titan-embed-text-v1\`]' --output text"
    
    check_command "Claude 3 Haiku model" \
        "aws bedrock list-foundation-models --region us-west-2 --query 'modelSummaries[?contains(modelId, \`claude-3-haiku\`)]' --output text"
    
    print_header "4. S3 Resources"
    S3_BUCKET="${ACCOUNT_ID}-us-west-2-advanced-rag-workshop"
    check_command "S3 bucket exists" "aws s3 ls s3://${S3_BUCKET}/"
    
    if aws s3 ls s3://${S3_BUCKET}/ > /dev/null 2>&1; then
        check_with_output "10-K reports uploaded" \
            "aws s3 ls s3://${S3_BUCKET}/10k-reports/ --recursive | grep -c '.pdf'"
    fi
    
    print_header "5. OpenSearch Serverless"
    check_with_output "OpenSearch collections" \
        "aws opensearchserverless list-collections --query 'length(collectionSummaries)' --output text"
    
    # Check specific collection
    check_command "Collection 'advancedrag'" \
        "aws opensearchserverless list-collections --query 'collectionSummaries[?name==\`advancedrag\`]' --output text"
    
    print_header "6. Bedrock Knowledge Bases"
    check_with_output "Knowledge Bases created" \
        "aws bedrock-agent list-knowledge-bases --query 'length(knowledgeBaseSummaries)' --output text"
    
    # List KB names if any exist
    KB_COUNT=$(aws bedrock-agent list-knowledge-bases --query 'length(knowledgeBaseSummaries)' --output text 2>/dev/null || echo "0")
    if [ "$KB_COUNT" -gt 0 ]; then
        echo "   Knowledge Base IDs:"
        aws bedrock-agent list-knowledge-bases \
            --query 'knowledgeBaseSummaries[*].[knowledgeBaseId,name]' \
            --output text | sed 's/^/   - /'
    fi
    
    print_header "7. Athena Resources"
    check_command "Athena available" "aws athena list-work-groups"
    check_with_output "Databases created" \
        "aws athena list-databases --catalog-name AwsDataCatalog --query 'length(DatabaseList)' --output text"
    
    print_header "8. IAM Resources"
    check_command "Bedrock execution role" \
        "aws iam get-role --role-name BedrockExecutionRoleForKB"
    
    print_header "9. Python Dependencies"
    check_command "RAG modules available" \
        "python -c 'import sys; sys.path.append(\".\"); from src.rag.pipeline import RAGPipeline'"
    
    check_command "Cost calculator available" \
        "python -c 'import sys; sys.path.append(\".\"); from src.utils.cost_calculator import RAGCostEstimator'"
    
    print_header "10. Local Testing (No AWS)"
    check_command "Philosophy texts downloaded" \
        "ls data/*.pdf | grep -E '(boethius|kant|wittgenstein|roget)'"
    
    # Summary
    print_header "Summary"
    echo "Validation complete!"
    echo ""
    echo "Next steps:"
    echo "1. If any checks failed, address them before proceeding"
    echo "2. Run the consolidated notebook: notebooks/01_rag_basics_consolidated.org"
    echo "3. Follow the WEEKEND_TESTING_CHECKLIST.org for detailed testing"
    echo ""
    
    # Cost reminder
    echo -e "${YELLOW}Cost Reminder:${NC}"
    echo "Estimated workshop cost: \$15-25 per participant"
    echo "Main costs: Bedrock embeddings, OpenSearch Serverless, S3 storage"
    echo ""
}

# Run main function
main "$@"