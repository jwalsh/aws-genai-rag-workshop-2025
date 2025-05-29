output "us_east_1_vpc_id" {
  description = "VPC ID in us-east-1"
  value       = module.networking_us_east_1.vpc_id
}

output "us_west_2_vpc_id" {
  description = "VPC ID in us-west-2"
  value       = module.networking_us_west_2.vpc_id
}

output "bedrock_endpoint_url" {
  description = "Bedrock endpoint URL for us-east-1"
  value       = module.bedrock_us_east_1.endpoint_url
}

output "anthropic_endpoint_url" {
  description = "Anthropic endpoint URL for us-west-2"
  value       = module.anthropic_us_west_2.endpoint_url
}

output "rag_opensearch_domain_endpoint" {
  description = "OpenSearch domain endpoint for RAG"
  value       = module.rag_infrastructure.opensearch_domain_endpoint
}

output "rag_s3_bucket_name" {
  description = "S3 bucket name for RAG documents"
  value       = module.rag_infrastructure.s3_bucket_name
}

output "rag_dynamodb_table_name" {
  description = "DynamoDB table name for RAG metadata"
  value       = module.rag_infrastructure.dynamodb_table_name
}