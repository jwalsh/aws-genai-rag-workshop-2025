data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

resource "aws_iam_role" "anthropic_execution" {
  name = "${var.environment}-anthropic-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = [
            "bedrock.amazonaws.com",
            "lambda.amazonaws.com"
          ]
        }
      }
    ]
  })

  tags = {
    Name = "${var.environment}-anthropic-execution-role"
  }
}

resource "aws_iam_role_policy" "anthropic_execution" {
  name = "${var.environment}-anthropic-execution-policy"
  role = aws_iam_role.anthropic_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream",
          "bedrock:ListFoundationModels",
          "bedrock:GetFoundationModel"
        ]
        Resource = [
          "arn:aws:bedrock:${data.aws_region.current.name}::foundation-model/anthropic.claude-4-*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:*"
      },
      {
        Effect = "Allow"
        Action = [
          "kms:Decrypt",
          "kms:GenerateDataKey"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_cloudwatch_log_group" "anthropic" {
  name              = "/aws/anthropic/${var.environment}"
  retention_in_days = 30

  tags = {
    Name = "${var.environment}-anthropic-logs"
  }
}

resource "aws_security_group" "anthropic_access" {
  name_prefix = "${var.environment}-anthropic-access-"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/8"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.environment}-anthropic-access-sg"
  }
}

resource "aws_ssm_parameter" "anthropic_models" {
  for_each = toset([
    "anthropic.claude-4-sonnet-20250514-v1:0",
    "anthropic.claude-4-haiku-20250514-v1:0",
    "anthropic.claude-4-opus-20250514-v1:0"
  ])

  name  = "/${var.environment}/anthropic/models/${replace(each.value, ":", "_")}"
  type  = "String"
  value = each.value

  tags = {
    Name = "${var.environment}-anthropic-model-${replace(each.value, ":", "_")}"
  }
}

resource "aws_ssm_parameter" "anthropic_endpoint" {
  name  = "/${var.environment}/anthropic/endpoint"
  type  = "String"
  value = "https://bedrock-runtime.${data.aws_region.current.name}.amazonaws.com"

  tags = {
    Name = "${var.environment}-anthropic-endpoint"
  }
}

resource "aws_s3_bucket" "anthropic_data" {
  bucket = "${var.environment}-anthropic-data-${data.aws_caller_identity.current.account_id}"

  tags = {
    Name = "${var.environment}-anthropic-data"
  }
}

resource "aws_s3_bucket_versioning" "anthropic_data" {
  bucket = aws_s3_bucket.anthropic_data.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "anthropic_data" {
  bucket = aws_s3_bucket.anthropic_data.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "anthropic_data" {
  bucket = aws_s3_bucket.anthropic_data.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_lambda_function" "anthropic_proxy" {
  filename         = data.archive_file.lambda_proxy.output_path
  function_name    = "${var.environment}-anthropic-proxy"
  role            = aws_iam_role.anthropic_execution.arn
  handler         = "index.handler"
  runtime         = "python3.11"
  timeout         = 300
  memory_size     = 512

  environment {
    variables = {
      ENVIRONMENT = var.environment
      REGION      = data.aws_region.current.name
    }
  }

  vpc_config {
    subnet_ids         = var.subnet_ids
    security_group_ids = [aws_security_group.anthropic_access.id]
  }

  tags = {
    Name = "${var.environment}-anthropic-proxy"
  }
}

data "archive_file" "lambda_proxy" {
  type        = "zip"
  output_path = "/tmp/anthropic-proxy.zip"
  
  source {
    content  = <<-EOT
import json
import boto3
import os

def handler(event, context):
    bedrock_runtime = boto3.client(
        'bedrock-runtime',
        region_name=os.environ['REGION']
    )
    
    model_id = event.get('model_id', 'anthropic.claude-4-sonnet-20250514-v1:0')
    
    try:
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            body=json.dumps(event['body'])
        )
        
        return {
            'statusCode': 200,
            'body': json.loads(response['body'].read())
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
EOT
    filename = "index.py"
  }
}