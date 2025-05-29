output "execution_role_arn" {
  description = "ARN of the Anthropic execution role"
  value       = aws_iam_role.anthropic_execution.arn
}

output "endpoint_url" {
  description = "Anthropic endpoint URL"
  value       = aws_ssm_parameter.anthropic_endpoint.value
}

output "data_bucket_name" {
  description = "Name of the S3 bucket for Anthropic data"
  value       = aws_s3_bucket.anthropic_data.id
}

output "security_group_id" {
  description = "Security group ID for Anthropic access"
  value       = aws_security_group.anthropic_access.id
}

output "log_group_name" {
  description = "CloudWatch log group name for Anthropic"
  value       = aws_cloudwatch_log_group.anthropic.name
}

output "proxy_function_name" {
  description = "Name of the Lambda proxy function"
  value       = aws_lambda_function.anthropic_proxy.function_name
}

output "proxy_function_arn" {
  description = "ARN of the Lambda proxy function"
  value       = aws_lambda_function.anthropic_proxy.arn
}