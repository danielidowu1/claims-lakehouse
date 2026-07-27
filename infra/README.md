# Infrastructure

Terraform for the minimal AWS footprint: one versioned S3 bucket (with
bronze/silver/gold prefixes) and a Glue Catalog database.

## Apply

```bash
cd infra
terraform init
terraform apply -var="bucket_name=your-globally-unique-name"
```

## Teardown (important for cost)

```bash
terraform destroy -var="bucket_name=your-globally-unique-name"
```

> Empty the bucket first if `destroy` complains it's not empty.
