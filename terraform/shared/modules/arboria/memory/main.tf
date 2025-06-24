module "dynamodb_checkpoints" {
  source         = "../../aws/dynamodb"
  table_name     = "${var.prefix}_checkpoints${var.environment}"
  hash_key_name  = var.hash_key_name
  hash_key_type  = var.hash_key_type
  range_key_name = var.range_key_name
  range_key_type = var.range_key_type
}

module "dynamodb_writes" {
  source         = "../../aws/dynamodb"
  table_name     = "${var.prefix}_writes${var.environment}"
  hash_key_name  = var.hash_key_name
  hash_key_type  = var.hash_key_type
  range_key_name = var.range_key_name
  range_key_type = var.range_key_type
}