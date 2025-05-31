terraform {
  required_version = ">= 1.5.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Configure AWS Provider for LocalStack
provider "aws" {
  access_key                  = "test"
  secret_key                  = "test"
  region                      = var.region
  s3_use_path_style          = true
  skip_credentials_validation = true
  skip_metadata_api_check    = true
  skip_requesting_account_id = true

  endpoints {
    apigateway     = var.localstack_endpoint
    apigatewayv2   = var.localstack_endpoint
    cloudformation = var.localstack_endpoint
    cloudwatch     = var.localstack_endpoint
    dynamodb       = var.localstack_endpoint
    ec2            = var.localstack_endpoint
    es             = var.localstack_endpoint
    firehose       = var.localstack_endpoint
    iam            = var.localstack_endpoint
    kinesis        = var.localstack_endpoint
    lambda         = var.localstack_endpoint
    route53        = var.localstack_endpoint
    redshift       = var.localstack_endpoint
    s3             = var.localstack_endpoint
    secretsmanager = var.localstack_endpoint
    ses            = var.localstack_endpoint
    sns            = var.localstack_endpoint
    sqs            = var.localstack_endpoint
    ssm            = var.localstack_endpoint
    stepfunctions  = var.localstack_endpoint
    sts            = var.localstack_endpoint
    bedrock        = var.localstack_endpoint
    opensearch     = var.localstack_endpoint
  }
}

locals {
  common_tags = {
    Project     = "GenAI-RAG-Workshop"
    Environment = "localstack"
    ManagedBy   = "Terraform"
    CreatedBy   = "Workshop-Infrastructure"
  }
}

# S3 Buckets for RAG
resource "aws_s3_bucket" "rag_documents" {
  bucket = "${var.project_name}-documents-${var.environment}"
  
  tags = merge(local.common_tags, {
    Name = "${var.project_name}-documents-${var.environment}"
    Type = "DocumentStorage"
  })
}

resource "aws_s3_bucket" "rag_embeddings" {
  bucket = "${var.project_name}-embeddings-${var.environment}"
  
  tags = merge(local.common_tags, {
    Name = "${var.project_name}-embeddings-${var.environment}"
    Type = "EmbeddingStorage"
  })
}

# DynamoDB Tables
resource "aws_dynamodb_table" "vector_metadata" {
  name           = "${var.project_name}-vector-metadata-${var.environment}"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "document_id"
  range_key      = "chunk_id"

  attribute {
    name = "document_id"
    type = "S"
  }

  attribute {
    name = "chunk_id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "N"
  }

  global_secondary_index {
    name            = "timestamp-index"
    hash_key        = "document_id"
    range_key       = "timestamp"
    projection_type = "ALL"
  }

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-vector-metadata-${var.environment}"
    Type = "Metadata"
  })
}

resource "aws_dynamodb_table" "knowledge_bases" {
  name           = "${var.project_name}-knowledge-bases-${var.environment}"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "kb_id"

  attribute {
    name = "kb_id"
    type = "S"
  }

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-knowledge-bases-${var.environment}"
    Type = "KnowledgeBase"
  })
}

# SQS Queues
resource "aws_sqs_queue" "document_processing" {
  name                      = "${var.project_name}-document-processing-${var.environment}"
  delay_seconds             = 0
  max_message_size          = 262144
  message_retention_seconds = 86400
  receive_wait_time_seconds = 10

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-document-processing-${var.environment}"
    Type = "Processing"
  })
}

resource "aws_sqs_queue" "document_processing_dlq" {
  name = "${var.project_name}-document-processing-dlq-${var.environment}"

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-document-processing-dlq-${var.environment}"
    Type = "DeadLetterQueue"
  })
}

# IAM Roles
resource "aws_iam_role" "bedrock_execution_role" {
  name = "${var.project_name}-bedrock-execution-role-${var.environment}"

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

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-bedrock-execution-role-${var.environment}"
    Type = "IAMRole"
  })
}

resource "aws_iam_role_policy" "bedrock_s3_access" {
  name = "${var.project_name}-bedrock-s3-access-${var.environment}"
  role = aws_iam_role.bedrock_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.rag_documents.arn,
          "${aws_s3_bucket.rag_documents.arn}/*",
          aws_s3_bucket.rag_embeddings.arn,
          "${aws_s3_bucket.rag_embeddings.arn}/*"
        ]
      }
    ]
  })
}

# OpenSearch Domain (simulated in LocalStack)
resource "aws_elasticsearch_domain" "rag_vectors" {
  domain_name           = "${var.project_name}-vectors-${var.environment}"
  elasticsearch_version = "7.10"

  cluster_config {
    instance_type  = "t3.small.elasticsearch"
    instance_count = 1
  }

  ebs_options {
    ebs_enabled = true
    volume_size = 10
  }

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-vectors-${var.environment}"
    Type = "VectorSearch"
  })
}

# Lambda Function for RAG Processing
resource "aws_lambda_function" "rag_processor" {
  filename      = "lambda_function.zip"
  function_name = "${var.project_name}-rag-processor-${var.environment}"
  role          = aws_iam_role.lambda_execution_role.arn
  handler       = "index.handler"
  runtime       = "python3.11"
  timeout       = 300
  memory_size   = 512

  environment {
    variables = {
      DOCUMENTS_BUCKET = aws_s3_bucket.rag_documents.id
      EMBEDDINGS_BUCKET = aws_s3_bucket.rag_embeddings.id
      VECTOR_TABLE = aws_dynamodb_table.vector_metadata.id
      OPENSEARCH_DOMAIN = aws_elasticsearch_domain.rag_vectors.endpoint
    }
  }

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-rag-processor-${var.environment}"
    Type = "Lambda"
  })
}

resource "aws_iam_role" "lambda_execution_role" {
  name = "${var.project_name}-lambda-execution-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-lambda-execution-role-${var.environment}"
    Type = "IAMRole"
  })
}

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "rag_processor_logs" {
  name              = "/aws/lambda/${aws_lambda_function.rag_processor.function_name}"
  retention_in_days = 7

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-rag-processor-logs-${var.environment}"
    Type = "Logs"
  })
}

# Outputs
output "s3_buckets" {
  value = {
    documents  = aws_s3_bucket.rag_documents.id
    embeddings = aws_s3_bucket.rag_embeddings.id
  }
}

output "dynamodb_tables" {
  value = {
    vector_metadata = aws_dynamodb_table.vector_metadata.id
    knowledge_bases = aws_dynamodb_table.knowledge_bases.id
  }
}

output "sqs_queues" {
  value = {
    processing = aws_sqs_queue.document_processing.id
    dlq        = aws_sqs_queue.document_processing_dlq.id
  }
}

output "opensearch_endpoint" {
  value = aws_elasticsearch_domain.rag_vectors.endpoint
}

output "lambda_function" {
  value = aws_lambda_function.rag_processor.function_name
}