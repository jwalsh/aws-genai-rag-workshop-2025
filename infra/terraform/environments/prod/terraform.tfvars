environment = "prod"

vpc_cidr_us_east_1 = "10.20.0.0/16"
vpc_cidr_us_west_2 = "10.21.0.0/16"

availability_zones_us_east_1 = ["us-east-1a", "us-east-1b", "us-east-1c"]
availability_zones_us_west_2 = ["us-west-2a", "us-west-2b", "us-west-2c"]

private_subnets_us_east_1 = ["10.20.1.0/24", "10.20.2.0/24", "10.20.3.0/24"]
public_subnets_us_east_1  = ["10.20.101.0/24", "10.20.102.0/24", "10.20.103.0/24"]

private_subnets_us_west_2 = ["10.21.1.0/24", "10.21.2.0/24", "10.21.3.0/24"]
public_subnets_us_west_2  = ["10.21.101.0/24", "10.21.102.0/24", "10.21.103.0/24"]

enable_vpc_endpoints            = true
enable_cross_region_replication = true

bedrock_model_ids = [
  "anthropic.claude-3-sonnet-20240229-v1:0",
  "anthropic.claude-3-haiku-20240307-v1:0",
  "anthropic.claude-3-opus-20240229-v1:0",
  "amazon.titan-embed-text-v1"
]

anthropic_model_ids = [
  "anthropic.claude-4-sonnet-20250514-v1:0",
  "anthropic.claude-4-haiku-20250514-v1:0",
  "anthropic.claude-4-opus-20250514-v1:0"
]