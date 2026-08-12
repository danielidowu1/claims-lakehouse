terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "5.0.0"
    }
  }
}

provider "aws" {
  region = var.region
}

# -----------------------------------------------------------------------------
# 1. STORAGE INFRASTRUCTURE
# -----------------------------------------------------------------------------
resource "aws_s3_bucket" "lake" {
  bucket        = var.bucket_name
  force_destroy = false 
}

resource "aws_s3_bucket_versioning" "lake" {
  bucket = aws_s3_bucket.lake.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "lake_sec" {
  bucket = aws_s3_bucket.lake.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "lake_private" {
  bucket                  = aws_s3_bucket.lake.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Folder prefixes inside S3
resource "aws_s3_object" "layers" {
  for_each = toset(["bronze/", "bronze/desynpuf/", "silver/", "gold/", "athena-results/"])
  bucket   = aws_s3_bucket.lake.id
  key      = each.value
  content  = ""
}

# -----------------------------------------------------------------------------
# 2. AWS GLUE DATABASES (MEDALLION SEPARATION)
# -----------------------------------------------------------------------------
resource "aws_glue_catalog_database" "claims_bronze" {
  name        = "${var.glue_db_name}"
  description = "Catalog tracking raw ingestion data structures."
}

resource "aws_glue_catalog_database" "claims_silver" {
  name        = "${var.glue_silver_db_name}"
  description = "Catalog tracking cleaned and typed parquet data structures."
}

resource "aws_glue_catalog_database" "claims_gold" {
  name        = "${var.glue_gold_db_name}"
  description = "Catalog tracking presentation star schemas."
}

# -----------------------------------------------------------------------------
# 3. AWS GLUE CRAWLER SETUP (UPDATED FOR INDEPENDENT ENTITY TABLES)
# -----------------------------------------------------------------------------
resource "aws_glue_crawler" "bronze_crawler" {
  database_name = aws_glue_catalog_database.claims_bronze.name
  name          = "healthcare-claims-bronze-crawler"
  role          = aws_iam_role.glue_service_role.arn

  # INDUSTRY STANDARD: Point to each subfolder independently 
  # This stops Glue from blending them into one single corrupted table!
  s3_target {
    path = "s3://${aws_s3_bucket.lake.id}/bronze/desynpuf/beneficiary/"
  }

  s3_target {
    path = "s3://${aws_s3_bucket.lake.id}/bronze/desynpuf/inpatient/"
  }

  s3_target {
    path = "s3://${aws_s3_bucket.lake.id}/bronze/desynpuf/outpatient/"
  }

  s3_target {
    path = "s3://${aws_s3_bucket.lake.id}/bronze/desynpuf/carrier/"
  }

  s3_target {
    path = "s3://${aws_s3_bucket.lake.id}/bronze/desynpuf/pde/"
  }

  configuration = jsonencode({
    Version = 1.0
    Grouping = {
      TableGroupingPolicy = "CombineCompatibleSchemas"
    }
    CrawlerOutput = {
      Partitions = { AddOrUpdateBehavior = "InheritFromTable" }
    }
  })
}


# -----------------------------------------------------------------------------
# 4. AWS ATHENA CATALOG CONFIGURATION (FIXED TO BYPASS USER ACCESS RESTRICTIONS)
# -----------------------------------------------------------------------------
# Removed the custom aws_athena_workgroup resource to bypass your AccessDeniedException.
# Athena queries will gracefully fall back to your default account workspace automatically.

# -----------------------------------------------------------------------------
# 5. IAM ROLE AND POLICIES FOR SECURITY SEPARATION
# -----------------------------------------------------------------------------
resource "aws_iam_role" "glue_service_role" {
  name = "glue-lakehouse-execution-role"

  # FIXED: Restored clean, uncorrupted standard service trust declaration mapping
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

resource "aws_iam_role_policy_attachment" "glue_service" {
  role       = aws_iam_role.glue_service_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
}

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

# -----------------------------------------------------------------------------
# 6. OUTPUTS (CLEANED)
# -----------------------------------------------------------------------------
output "bucket_id" { value = aws_s3_bucket.lake.id }
output "glue_role_arn" { value = aws_iam_role.glue_service_role.arn }
output "bronze_crawler_name" { value = aws_glue_crawler.bronze_crawler.name }
