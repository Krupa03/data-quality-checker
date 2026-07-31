# Provisions the S3 bucket used to store quality-check report artifacts.
#
# This uses the real, official AWS Terraform provider -- the code is
# identical to what you'd write against a real AWS account. The only
# difference is `endpoints.s3` points at LocalStack (a local AWS
# emulator) instead of `s3.amazonaws.com`, so this can run with zero
# AWS account and zero cost. Point the endpoint at real AWS later
# and this file doesn't need to change.

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region                      = "us-east-1"
  access_key                  = "test"   # LocalStack ignores real credentials
  secret_key                  = "test"
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true

  endpoints {
    s3 = "http://localhost:4566"   # LocalStack endpoint
  }
}

resource "aws_s3_bucket" "quality_reports" {
  bucket = var.bucket_name

  tags = {
    Project     = "data-quality-checker"
    Environment = "local-dev"
  }
}

resource "aws_s3_bucket_versioning" "quality_reports_versioning" {
  bucket = aws_s3_bucket.quality_reports.id
  versioning_configuration {
    status = "Enabled"
  }
}

variable "bucket_name" {
  description = "Name of the S3 bucket that stores quality check report artifacts."
  type        = string
  default     = "dq-checker-reports"
}

output "bucket_name" {
  value = aws_s3_bucket.quality_reports.bucket
}
