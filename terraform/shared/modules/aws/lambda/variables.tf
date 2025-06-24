variable "function_name" {
  type = string
}

variable "role_arn" {
  type = string
}

variable "handler" {
  type    = string
  default = "lambda_function.lambda_handler"
}

variable "runtime" {
  type        = string
  description = "Runtime da função Lambda"
  default     = "python3.11"
  validation {
    condition = contains(["python3.11", "nodejs22.x"], var.runtime)
    error_message = "Runtime deve ser python3.11 ou nodejs22.x"
  }
}

variable "timeout" {
  type    = number
  default = 15
}

variable "memory_size" {
  type    = number
  default = 128
}

variable "zip_file" {
  type = string
}

variable "layers" {
  type = list(string)
}

variable "environment_variables" {
  type = map(string)
}
