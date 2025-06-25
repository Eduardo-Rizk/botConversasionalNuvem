provider "aws" {
  profile = "arboria-dudu"
  region  = "us-west-2" # dev region - take the west cowboys
}

data "aws_region" "current" {}


module "test_infrastructure" {
  source = "../../shared"

  environment              = "-dev"
  aws_region               = data.aws_region.current.name
  openai_api_key           = var.openai_api_key
  openai_llm_model_name    = var.openai_llm_model_name
  firecrawl_api_key        = var.firecrawl_api_key
  evolution_api_base_url   = var.evolution_api_base_url
  evolution_api_key        = var.evolution_api_key
}