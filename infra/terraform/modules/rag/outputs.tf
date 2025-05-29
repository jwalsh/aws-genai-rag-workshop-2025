output "s3_bucket_name" {
  description = "Name of the S3 bucket for RAG documents"
  value       = aws_s3_bucket.rag_documents.id
}

output "s3_bucket_replica_name" {
  description = "Name of the replica S3 bucket"
  value       = aws_s3_bucket.rag_documents_replica.id
}

output "opensearch_domain_endpoint" {
  description = "OpenSearch domain endpoint"
  value       = aws_opensearch_domain.rag.endpoint
}

output "opensearch_domain_arn" {
  description = "OpenSearch domain ARN"
  value       = aws_opensearch_domain.rag.arn
}

output "dynamodb_table_name" {
  description = "DynamoDB table name for RAG metadata"
  value       = aws_dynamodb_table.rag_metadata.name
}

output "dynamodb_table_replica_name" {
  description = "DynamoDB replica table name"
  value       = aws_dynamodb_table.rag_metadata_replica.name
}

output "sqs_queue_url" {
  description = "SQS queue URL for RAG processing"
  value       = aws_sqs_queue.rag_processing.url
}

output "sqs_queue_arn" {
  description = "SQS queue ARN for RAG processing"
  value       = aws_sqs_queue.rag_processing.arn
}