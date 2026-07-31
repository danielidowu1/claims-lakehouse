variable "region" {
  type        = string
  description = "The AWS deployment region."
}

variable "bucket_name" {
  type        = string
  description = "Globally-unique S3 bucket name for the lakehouse."
}

variable "glue_db_name" {
  type        = string
  description = "The name of the AWS Glue Catalog Database."
}
