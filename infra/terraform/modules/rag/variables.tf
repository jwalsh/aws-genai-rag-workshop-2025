variable "environment" {
  description = "Environment name"
  type        = string
}

variable "primary_vpc_id" {
  description = "Primary VPC ID (us-east-1)"
  type        = string
}

variable "primary_private_subnets" {
  description = "Primary private subnet IDs"
  type        = list(string)
}

variable "secondary_vpc_id" {
  description = "Secondary VPC ID (us-west-2)"
  type        = string
}

variable "secondary_private_subnets" {
  description = "Secondary private subnet IDs"
  type        = list(string)
}