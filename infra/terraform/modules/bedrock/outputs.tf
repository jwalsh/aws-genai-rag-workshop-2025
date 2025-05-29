output "execution_role_arn" {
  description = "ARN of the Bedrock execution role"
  value       = aws_iam_role.bedrock_execution.arn
}

output "endpoint_url" {
  description = "Bedrock endpoint URL"
  value       = aws_ssm_parameter.bedrock_endpoint.value
}

output "data_bucket_name" {
  description = "Name of the S3 bucket for Bedrock data"
  value       = aws_s3_bucket.bedrock_data.id
}

output "security_group_id" {
  description = "Security group ID for Bedrock access"
  value       = aws_security_group.bedrock_access.id
}

output "log_group_name" {
  description = "CloudWatch log group name for Bedrock"
  value       = aws_cloudwatch_log_group.bedrock.name
}