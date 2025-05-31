variable "localstack_endpoint" {
  description = "LocalStack endpoint URL"
  type        = string
  default     = "http://localhost:4566"
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-west-2"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "localstack"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "genai-rag-workshop"
}