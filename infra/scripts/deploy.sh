#!/bin/bash

set -euo pipefail

ENVIRONMENT=${1:-dev}
ACTION=${2:-plan}

if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|prod)$ ]]; then
    echo "Error: Environment must be dev, staging, or prod"
    exit 1
fi

if [[ ! "$ACTION" =~ ^(plan|apply|destroy)$ ]]; then
    echo "Error: Action must be plan, apply, or destroy"
    exit 1
fi

cd "$(dirname "$0")/../terraform"

echo "Initializing Terraform..."
terraform init -backend-config="key=infrastructure/${ENVIRONMENT}/terraform.tfstate"

echo "Validating Terraform configuration..."
terraform validate

echo "Running terraform ${ACTION} for ${ENVIRONMENT} environment..."
terraform ${ACTION} -var-file="environments/${ENVIRONMENT}/terraform.tfvars"

if [[ "$ACTION" == "apply" ]]; then
    echo "Saving outputs to environments/${ENVIRONMENT}/outputs.json..."
    terraform output -json > "environments/${ENVIRONMENT}/outputs.json"
fi