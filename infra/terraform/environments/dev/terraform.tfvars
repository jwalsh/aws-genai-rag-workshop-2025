environment = "dev"

vpc_cidr_us_east_1 = "10.0.0.0/16"
vpc_cidr_us_west_2 = "10.1.0.0/16"

availability_zones_us_east_1 = ["us-east-1a", "us-east-1b"]
availability_zones_us_west_2 = ["us-west-2a", "us-west-2b"]

private_subnets_us_east_1 = ["10.0.1.0/24", "10.0.2.0/24"]
public_subnets_us_east_1  = ["10.0.101.0/24", "10.0.102.0/24"]

private_subnets_us_west_2 = ["10.1.1.0/24", "10.1.2.0/24"]
public_subnets_us_west_2  = ["10.1.101.0/24", "10.1.102.0/24"]

enable_vpc_endpoints            = true
enable_cross_region_replication = false

bedrock_model_ids = [
  "anthropic.claude-3-haiku-20240307-v1:0",
  "amazon.titan-embed-text-v1"
]

anthropic_model_ids = [
  "anthropic.claude-4-haiku-20250514-v1:0"
]