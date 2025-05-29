terraform {
  required_providers {
    aws = {
      source = "hashicorp/aws"
      version = "~> 5.0"
      configuration_aliases = [aws.primary, aws.secondary]
    }
  }
}

data "aws_caller_identity" "primary" {
  provider = aws.primary
}

data "aws_region" "primary" {
  provider = aws.primary
}

data "aws_region" "secondary" {
  provider = aws.secondary
}

resource "aws_s3_bucket" "rag_documents" {
  provider = aws.primary
  bucket   = "${var.environment}-rag-documents-${data.aws_caller_identity.primary.account_id}"

  tags = {
    Name = "${var.environment}-rag-documents"
  }
}

resource "aws_s3_bucket_versioning" "rag_documents" {
  provider = aws.primary
  bucket   = aws_s3_bucket.rag_documents.id
  
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_replication_configuration" "rag_documents" {
  provider = aws.primary
  role     = aws_iam_role.replication.arn
  bucket   = aws_s3_bucket.rag_documents.id

  rule {
    id     = "replicate-to-secondary"
    status = "Enabled"

    destination {
      bucket        = aws_s3_bucket.rag_documents_replica.arn
      storage_class = "STANDARD_IA"
    }
  }

  depends_on = [aws_s3_bucket_versioning.rag_documents]
}

resource "aws_s3_bucket" "rag_documents_replica" {
  provider = aws.secondary
  bucket   = "${var.environment}-rag-documents-replica-${data.aws_caller_identity.primary.account_id}"

  tags = {
    Name = "${var.environment}-rag-documents-replica"
  }
}

resource "aws_s3_bucket_versioning" "rag_documents_replica" {
  provider = aws.secondary
  bucket   = aws_s3_bucket.rag_documents_replica.id
  
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_iam_role" "replication" {
  provider = aws.primary
  name     = "${var.environment}-rag-s3-replication-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "s3.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "replication" {
  provider = aws.primary
  name     = "${var.environment}-rag-s3-replication-policy"
  role     = aws_iam_role.replication.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetReplicationConfiguration",
          "s3:ListBucket"
        ]
        Resource = aws_s3_bucket.rag_documents.arn
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObjectVersionForReplication",
          "s3:GetObjectVersionAcl",
          "s3:GetObjectVersionTagging"
        ]
        Resource = "${aws_s3_bucket.rag_documents.arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ReplicateObject",
          "s3:ReplicateDelete",
          "s3:ReplicateTags"
        ]
        Resource = "${aws_s3_bucket.rag_documents_replica.arn}/*"
      }
    ]
  })
}

resource "aws_opensearch_domain" "rag" {
  provider    = aws.primary
  domain_name = "${var.environment}-rag-search"
  
  engine_version = "OpenSearch_2.11"

  cluster_config {
    instance_type  = "t3.small.search"
    instance_count = 2
  }

  ebs_options {
    ebs_enabled = true
    volume_type = "gp3"
    volume_size = 20
  }

  vpc_options {
    subnet_ids         = [var.primary_private_subnets[0], var.primary_private_subnets[1]]
    security_group_ids = [aws_security_group.opensearch.id]
  }

  encrypt_at_rest {
    enabled = true
  }

  node_to_node_encryption {
    enabled = true
  }

  domain_endpoint_options {
    enforce_https       = true
    tls_security_policy = "Policy-Min-TLS-1-2-2019-07"
  }

  tags = {
    Name = "${var.environment}-rag-search"
  }
}

resource "aws_security_group" "opensearch" {
  provider    = aws.primary
  name_prefix = "${var.environment}-opensearch-"
  vpc_id      = var.primary_vpc_id

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
    Name = "${var.environment}-opensearch-sg"
  }
}

resource "aws_dynamodb_table" "rag_metadata" {
  provider         = aws.primary
  name             = "${var.environment}-rag-metadata"
  billing_mode     = "PAY_PER_REQUEST"
  hash_key         = "document_id"
  range_key        = "chunk_id"
  stream_enabled   = true
  stream_view_type = "NEW_AND_OLD_IMAGES"

  attribute {
    name = "document_id"
    type = "S"
  }

  attribute {
    name = "chunk_id"
    type = "N"
  }

  attribute {
    name = "source_file"
    type = "S"
  }

  global_secondary_index {
    name            = "source_file_index"
    hash_key        = "source_file"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = {
    Name = "${var.environment}-rag-metadata"
  }
}

resource "aws_dynamodb_table" "rag_metadata_replica" {
  provider = aws.secondary
  
  name             = "${var.environment}-rag-metadata-replica"
  billing_mode     = "PAY_PER_REQUEST"
  hash_key         = "document_id"
  range_key        = "chunk_id"
  stream_enabled   = true
  stream_view_type = "NEW_AND_OLD_IMAGES"

  attribute {
    name = "document_id"
    type = "S"
  }

  attribute {
    name = "chunk_id"
    type = "N"
  }

  attribute {
    name = "source_file"
    type = "S"
  }

  global_secondary_index {
    name            = "source_file_index"
    hash_key        = "source_file"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = {
    Name = "${var.environment}-rag-metadata-replica"
  }
}

resource "aws_sqs_queue" "rag_processing" {
  provider                   = aws.primary
  name                      = "${var.environment}-rag-processing"
  delay_seconds             = 0
  max_message_size          = 262144
  message_retention_seconds = 1209600
  receive_wait_time_seconds = 10
  visibility_timeout_seconds = 300

  tags = {
    Name = "${var.environment}-rag-processing"
  }
}

resource "aws_sqs_queue" "rag_processing_dlq" {
  provider                   = aws.primary
  name                      = "${var.environment}-rag-processing-dlq"
  message_retention_seconds = 1209600

  tags = {
    Name = "${var.environment}-rag-processing-dlq"
  }
}

resource "aws_sqs_queue_redrive_policy" "rag_processing" {
  provider = aws.primary
  queue_url = aws_sqs_queue.rag_processing.id
  
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.rag_processing_dlq.arn
    maxReceiveCount     = 3
  })
}