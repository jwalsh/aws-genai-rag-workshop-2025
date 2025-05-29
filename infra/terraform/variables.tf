variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "vpc_cidr_us_east_1" {
  description = "CIDR block for VPC in us-east-1"
  type        = string
  default     = "10.0.0.0/16"
}

variable "vpc_cidr_us_west_2" {
  description = "CIDR block for VPC in us-west-2"
  type        = string
  default     = "10.1.0.0/16"
}

variable "availability_zones_us_east_1" {
  description = "Availability zones for us-east-1"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b", "us-east-1c"]
}

variable "availability_zones_us_west_2" {
  description = "Availability zones for us-west-2"
  type        = list(string)
  default     = ["us-west-2a", "us-west-2b", "us-west-2c"]
}

variable "private_subnets_us_east_1" {
  description = "Private subnet CIDR blocks for us-east-1"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
}

variable "public_subnets_us_east_1" {
  description = "Public subnet CIDR blocks for us-east-1"
  type        = list(string)
  default     = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]
}

variable "private_subnets_us_west_2" {
  description = "Private subnet CIDR blocks for us-west-2"
  type        = list(string)
  default     = ["10.1.1.0/24", "10.1.2.0/24", "10.1.3.0/24"]
}

variable "public_subnets_us_west_2" {
  description = "Public subnet CIDR blocks for us-west-2"
  type        = list(string)
  default     = ["10.1.101.0/24", "10.1.102.0/24", "10.1.103.0/24"]
}

variable "bedrock_model_ids" {
  description = "Bedrock model IDs to enable"
  type        = list(string)
  default = [
    "anthropic.claude-3-sonnet-20240229-v1:0",
    "anthropic.claude-3-haiku-20240307-v1:0",
    "amazon.titan-embed-text-v1"
  ]
}

variable "anthropic_model_ids" {
  description = "New Anthropic model IDs for us-west-2"
  type        = list(string)
  default = [
    "anthropic.claude-4-sonnet-20250514-v1:0",
    "anthropic.claude-4-haiku-20250514-v1:0"
  ]
}

variable "enable_vpc_endpoints" {
  description = "Enable VPC endpoints for AWS services"
  type        = bool
  default     = true
}

variable "enable_cross_region_replication" {
  description = "Enable cross-region replication for S3 buckets"
  type        = bool
  default     = true
}