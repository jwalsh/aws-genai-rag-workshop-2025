data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

resource "aws_iam_role" "bedrock_execution" {
  name = "${var.environment}-bedrock-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "bedrock.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "${var.environment}-bedrock-execution-role"
  }
}

resource "aws_iam_role_policy" "bedrock_execution" {
  name = "${var.environment}-bedrock-execution-policy"
  role = aws_iam_role.bedrock_execution.id

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
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:*"
      }
    ]
  })
}

resource "aws_cloudwatch_log_group" "bedrock" {
  name              = "/aws/bedrock/${var.environment}"
  retention_in_days = 30

  tags = {
    Name = "${var.environment}-bedrock-logs"
  }
}

resource "aws_security_group" "bedrock_access" {
  name_prefix = "${var.environment}-bedrock-access-"
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
    Name = "${var.environment}-bedrock-access-sg"
  }
}

resource "aws_ssm_parameter" "bedrock_models" {
  for_each = toset([
    "anthropic.claude-3-sonnet-20240229-v1:0",
    "anthropic.claude-3-haiku-20240307-v1:0",
    "amazon.titan-embed-text-v1"
  ])

  name  = "/${var.environment}/bedrock/models/${replace(each.value, ":", "_")}"
  type  = "String"
  value = each.value

  tags = {
    Name = "${var.environment}-bedrock-model-${replace(each.value, ":", "_")}"
  }
}

resource "aws_ssm_parameter" "bedrock_endpoint" {
  name  = "/${var.environment}/bedrock/endpoint"
  type  = "String"
  value = "https://bedrock-runtime.${data.aws_region.current.name}.amazonaws.com"

  tags = {
    Name = "${var.environment}-bedrock-endpoint"
  }
}

resource "aws_s3_bucket" "bedrock_data" {
  bucket = "${var.environment}-bedrock-data-${data.aws_caller_identity.current.account_id}"

  tags = {
    Name = "${var.environment}-bedrock-data"
  }
}

resource "aws_s3_bucket_versioning" "bedrock_data" {
  bucket = aws_s3_bucket.bedrock_data.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "bedrock_data" {
  bucket = aws_s3_bucket.bedrock_data.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "bedrock_data" {
  bucket = aws_s3_bucket.bedrock_data.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}