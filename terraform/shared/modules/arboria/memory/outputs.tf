output "checkpoints_table_name" {
  description = "Name of the checkpoints DynamoDB table"
  value       = module.dynamodb_checkpoints.table_name
}

output "writes_table_name" {
  description = "Name of the writes DynamoDB table"
  value       = module.dynamodb_writes.table_name
}

output "checkpoints_table_arn" {
  description = "ARN of the checkpoints DynamoDB table"
  value       = module.dynamodb_checkpoints.table_arn
}

output "writes_table_arn" {
  description = "ARN of the writes DynamoDB table"
  value       = module.dynamodb_writes.table_arn
}