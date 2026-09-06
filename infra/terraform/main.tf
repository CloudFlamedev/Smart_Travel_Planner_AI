terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Dummy remote state config — point this at a real S3 bucket + DynamoDB
  # lock table before running against an actual AWS account.
  backend "s3" {
    bucket         = "smart-travel-planner-tfstate"
    key            = "eks/terraform.tfstate"
    region         = "ap-south-1"
    dynamodb_table = "smart-travel-planner-tf-locks"
    encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}
