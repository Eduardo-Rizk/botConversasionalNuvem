variable "table_name" {
  type = string
}

variable "hash_key_name" {
  type = string
}

variable "hash_key_type" {
  type    = string
  default = "S"
}

variable "range_key_name" {
  type    = string
  default = ""
}

variable "range_key_type" {
  type    = string
  default = ""  # Define um valor padrão vazio para o tipo da chave de ordenação
}

variable "global_secondary_indexes" {
  description = "List of GSI configurations"
  type = list(object({
    name            = string
    hash_key        = string
    range_key = optional(string)
    projection_type = string
    non_key_attributes = optional(list(string))
  }))
  default = []
}

variable "attributes" {
  description = "Additional attributes for indexes"
  type = list(object({
    name = string
    type = string
  }))
  default = []
}