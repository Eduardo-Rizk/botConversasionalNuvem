locals {
  region_configs = {
    "us-west-2" = {
      chatbots_general_layer_arn = "arn:aws:lambda:us-west-2:619071345960:layer:chatbots-general-layer:1"
    }
  }

  # Get the correct ARN based on current region
  chatbots_general_layer_arn = local.region_configs[var.aws_region].chatbots_general_layer_arn
}


module "test_memory" {
  source      = "./modules/arboria/memory"
  prefix      = "test"
  environment = var.environment
}

# Cria a role IAM para as Lambdas
resource "aws_iam_role" "lambda_role" {
  name = "lambda_execution_role${var.environment}"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
      Effect = "Allow"
      Sid    = ""
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.lambda_role.name

  depends_on = [aws_iam_role.lambda_role]
}

resource "aws_iam_role_policy_attachment" "lambda_full_access" {
  policy_arn = "arn:aws:iam::aws:policy/AWSLambda_FullAccess"
  role       = aws_iam_role.lambda_role.name

  depends_on = [aws_iam_role.lambda_role]
}


module "lambda_conversational" {
  source        = "./modules/aws/lambda"
  function_name = "test-conversational${var.environment}"
  role_arn      = aws_iam_role.lambda_role.arn
  zip_file      = "./deployments/e_commerce_chatbot.zip"
  layers = [
    local.chatbots_general_layer_arn,
  ]
  environment_variables = {
    OPENAI_API_KEY = var.openai_api_key
    DYNAMODB_CHECKPOINT_TABLE        = module.test_memory.checkpoints_table_name
    DYNAMODB_WRITES_TABLE            = module.test_memory.writes_table_name
    OPENAI_LLM_MODEL_NAME            = var.openai_llm_model_name
    ENV                              = var.environment
    FIRECRAWL_API_KEY                = var.firecrawl_api_key
  }
}