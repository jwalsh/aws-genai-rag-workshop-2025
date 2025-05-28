#!/bin/bash
# Script to help fix AWS credentials file formatting issues

echo "AWS Credentials File Fixer"
echo "========================="

# Check if backup exists
if [ -f ~/.aws/credentials.bak ]; then
    echo "Found backup at ~/.aws/credentials.bak"
    
    # Create a clean credentials file
    echo "Creating clean credentials file..."
    
    cat > ~/.aws/credentials.tmp << 'EOF'
[default]
aws_access_key_id = YOUR_DEFAULT_ACCESS_KEY
aws_secret_access_key = YOUR_DEFAULT_SECRET_KEY

[lcl]
aws_access_key_id = YOUR_LCL_ACCESS_KEY
aws_secret_access_key = YOUR_LCL_SECRET_KEY

[dev]
aws_access_key_id = YOUR_DEV_ACCESS_KEY
aws_secret_access_key = YOUR_DEV_SECRET_KEY

[spaces]
aws_access_key_id = YOUR_SPACES_ACCESS_KEY
aws_secret_access_key = YOUR_SPACES_SECRET_KEY
EOF

    echo ""
    echo "Template created at ~/.aws/credentials.tmp"
    echo ""
    echo "To fix your credentials:"
    echo "1. Copy your actual keys from ~/.aws/credentials.bak"
    echo "2. Replace the YOUR_* placeholders in ~/.aws/credentials.tmp"
    echo "3. Move the fixed file: mv ~/.aws/credentials.tmp ~/.aws/credentials"
    echo "4. Set permissions: chmod 600 ~/.aws/credentials"
    echo ""
    echo "Or manually create ~/.aws/credentials with proper formatting:"
    echo ""
    cat ~/.aws/credentials.tmp
else
    echo "No backup found. Please ensure your credentials are backed up first."
fi