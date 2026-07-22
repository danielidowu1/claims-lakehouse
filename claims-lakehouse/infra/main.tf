# Minimal starter infra: one S3 bucket for the lakehouse + a Glue catalog DB.
# Run: cd infra && terraform init && terraform apply
# NOTE: bucket names are globally unique — change `bucket_name` before applying.

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

variable "region" {
  type    = string
  default = "us-east-1"
}

variable "bucket_name" {
  type        = string
  description = "Globally-unique S3 bucket name for the lakehouse."
}

provider "aws" {
  region = var.region
}

resource "aws_s3_bucket" "lake" {
  bucket = var.bucket_name
}

resource "aws_s3_bucket_versioning" "lake" {
  bucket = aws_s3_bucket.lake.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Medallion prefixes are just object key prefixes; no resource needed.
# Create an empty marker object per layer so they're visible in the console.
resource "aws_s3_object" "layers" {
  for_each = toset(["bronze/", "silver/", "gold/"])
  bucket   = aws_s3_bucket.lake.id
  key      = each.value
  content  = ""
}

resource "aws_glue_catalog_database" "claims" {
  name = "claims_lakehouse"
}

output "bucket" {
  value = aws_s3_bucket.lake.bucket
}
