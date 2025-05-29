terraform {
  required_version = ">= 1.5.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  backend "s3" {
    bucket         = "genai-rag-workshop-terraform-state"
    key            = "infrastructure/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-state-lock"
    encrypt        = true
  }
}

provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"
  
  default_tags {
    tags = local.common_tags
  }
}

provider "aws" {
  alias  = "us_west_2"
  region = "us-west-2"
  
  default_tags {
    tags = local.common_tags
  }
}

locals {
  common_tags = {
    Project     = "GenAI-RAG-Workshop"
    Environment = var.environment
    ManagedBy   = "Terraform"
    CreatedBy   = "Workshop-Infrastructure"
  }
}

module "networking_us_east_1" {
  source = "./modules/networking"
  providers = {
    aws = aws.us_east_1
  }
  
  environment      = var.environment
  region           = "us-east-1"
  vpc_cidr         = var.vpc_cidr_us_east_1
  azs              = var.availability_zones_us_east_1
  private_subnets  = var.private_subnets_us_east_1
  public_subnets   = var.public_subnets_us_east_1
}

module "networking_us_west_2" {
  source = "./modules/networking"
  providers = {
    aws = aws.us_west_2
  }
  
  environment      = var.environment
  region           = "us-west-2"
  vpc_cidr         = var.vpc_cidr_us_west_2
  azs              = var.availability_zones_us_west_2
  private_subnets  = var.private_subnets_us_west_2
  public_subnets   = var.public_subnets_us_west_2
}

module "bedrock_us_east_1" {
  source = "./modules/bedrock"
  providers = {
    aws = aws.us_east_1
  }
  
  environment = var.environment
  vpc_id      = module.networking_us_east_1.vpc_id
  subnet_ids  = module.networking_us_east_1.private_subnet_ids
}

module "anthropic_us_west_2" {
  source = "./modules/anthropic"
  providers = {
    aws = aws.us_west_2
  }
  
  environment = var.environment
  vpc_id      = module.networking_us_west_2.vpc_id
  subnet_ids  = module.networking_us_west_2.private_subnet_ids
}

module "rag_infrastructure" {
  source = "./modules/rag"
  providers = {
    aws.primary   = aws.us_east_1
    aws.secondary = aws.us_west_2
  }
  
  environment                = var.environment
  primary_vpc_id            = module.networking_us_east_1.vpc_id
  primary_private_subnets   = module.networking_us_east_1.private_subnet_ids
  secondary_vpc_id          = module.networking_us_west_2.vpc_id
  secondary_private_subnets = module.networking_us_west_2.private_subnet_ids
}