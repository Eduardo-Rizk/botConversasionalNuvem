variable "aws_region" {
  description = "The AWS region to deploy resources in"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment suffix for resources (e.g., '-dev' or '' for prod)"
  type        = string
}

variable "openai_api_key" {
  type        = string
  description = "OpenAI API Key"
}

variable "openai_llm_model_name" {
  type        = string
  default     = "gpt-4o-mini"
  description = "OpenAI model name"
}


variable "evolution_api_key" {
  description = "Chave da API do evolution"
  type        = string
}

variable "evolution_api_base_url" {
  description = "URL base da API do evolution"
  type        = string
}

variable "firecrawl_api_key"{}


