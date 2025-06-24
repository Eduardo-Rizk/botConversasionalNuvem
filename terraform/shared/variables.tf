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

variable "firecrawl_api_key"{}