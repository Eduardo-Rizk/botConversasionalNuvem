variable "prefix" {
  description = "Prefix to be used in table names (e.g., 'eva', 'gaia')"
  type        = string
}

variable "hash_key_name" {
  description = "Name of the hash key"
  type        = string
  default     = "thread_id"
}

variable "hash_key_type" {
  description = "Type of the hash key"
  type        = string
  default     = "S"
}

variable "range_key_name" {
  description = "Name of the range key"
  type        = string
  default     = "sort_key"
}

variable "range_key_type" {
  description = "Type of the range key"
  type        = string
  default     = "S"
}

variable "environment" {
  type = string
}