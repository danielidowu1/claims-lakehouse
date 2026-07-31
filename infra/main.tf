terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.region
}

# 1. The Storage Bucket
resource "aws_s3_bucket" "lake" {
  bucket        = var.bucket_name
  force_destroy = false 
}

# 2. Safety Net Versioning
resource "aws_s3_bucket_versioning" "lake" {
  bucket = aws_s3_bucket.lake.id
  versioning_configuration {
    status = "Enabled"
  }
}

# 3. Security: Force Server-Side Encryption (AES256)
resource "aws_s3_bucket_server_side_encryption_configuration" "lake_sec" {
  bucket = aws_s3_bucket.lake.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# 4. Security: Complete Public Access Block
resource "aws_s3_bucket_public_access_block" "lake_private" {
  bucket                  = aws_s3_bucket.lake.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# 5. Create Medallion Prefixes
resource "aws_s3_object" "layers" {
  for_each = toset(["bronze/", "silver/", "gold/"])
  bucket   = aws_s3_bucket.lake.id
  key      = each.value
  content  = ""
}

# 6. Central Directory Database Catalog
resource "aws_glue_catalog_database" "claims" {
  name        = var.glue_db_name
  description = "Data catalog database for processed medallion claims files."
}

# 7. Outputs for your Python Pipelines
output "bucket_id" {
  value       = aws_s3_bucket.lake.id
  description = "The verified S3 bucket ID used for data storage paths."
}

# 8. IAM ROLE AND POLICIES FOR AWS GLUE

# A. Create the Trust Policy (Allows the Glue service to assume this role)
resource "aws_iam_role" "glue_service_role" {
  name = "glue-lakehouse-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "glue.amazonaws.com"
        }
      }
    ]
  })
}

# B. Attach the Standard AWS Glue Service Policy (For logs, metrics, and catalog access)
resource "aws_iam_role_policy_attachment" "glue_service" {
  role       = aws_iam_role.glue_service_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
}

# C. Create an Inline Custom S3 Policy (Allows Glue to read/write your specific bucket)
resource "aws_iam_role_policy" "glue_s3_access" {
  name = "glue-s3-lakehouse-access"
  role = aws_iam_role.glue_service_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::${var.bucket_name}",
          "arn:aws:s3:::${var.bucket_name}/*"
        ]
      }
    ]
  })
}

# D. Output the Role ARN so your Python pipelines or tools can reference it
output "glue_role_arn" {
  value       = aws_iam_role.glue_service_role.arn
  description = "The IAM Role ARN that AWS Glue uses to execute tasks."
}
