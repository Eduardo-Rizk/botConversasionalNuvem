resource "aws_dynamodb_table" "this" {
  name         = var.table_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key = var.hash_key_name

  # Adiciona a chave de ordenação se ela for fornecida
  range_key = var.range_key_name != "" ? var.range_key_name : null

  attribute {
    name = var.hash_key_name
    type = var.hash_key_type
  }

  # Adiciona a chave de ordenação se ela for fornecida
  dynamic "attribute" {
    for_each = var.range_key_name != "" ? [1] : []
    content {
      name = var.range_key_name
      type = var.range_key_type
    }
  }

  dynamic "attribute" {
    for_each = var.attributes
    content {
      name = attribute.value.name
      type = attribute.value.type
    }
  }

  dynamic "global_secondary_index" {
    for_each = var.global_secondary_indexes
    content {
      name               = global_secondary_index.value.name
      hash_key           = global_secondary_index.value.hash_key
      range_key          = global_secondary_index.value.range_key
      projection_type    = global_secondary_index.value.projection_type
      non_key_attributes = global_secondary_index.value.non_key_attributes
    }
  }
}