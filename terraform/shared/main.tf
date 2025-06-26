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




# --------------------------------
#   DynamoDB
# --------------------------------

module "dynamodb_received_messages" {
  source         = "./modules/aws/dynamodb"
  table_name     = "conversational_debouncer_received_messages"
  hash_key_name  = "instance_name"
  hash_key_type  = "S"
  range_key_name = "cellphone_number"
  range_key_type = "S"
}




# --------------------------------
#   IAM roles and permissions
# --------------------------------

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

resource "aws_iam_role_policy_attachment" "lambda_step_functions" {
  policy_arn = "arn:aws:iam::aws:policy/AWSStepFunctionsFullAccess"
  role       = aws_iam_role.lambda_role.name

  depends_on = [aws_iam_role.lambda_role]
}

resource "aws_iam_role_policy_attachment" "lambda_full_access_dynamodb" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess"
  role       = aws_iam_role.lambda_role.name

  depends_on = [aws_iam_role.lambda_role]
}

# Role para Step Functions
resource "aws_iam_role" "step_functions_role" {
  name = "conversational_step_functions_execution_role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Principal = {
          Service = "states.amazonaws.com"
        }
        Effect = "Allow"
        Sid    = ""
      }
    ]
  })
}
# Anexa a política à role, permitindo step functions invocar Lambdas
resource "aws_iam_role_policy" "step_functions_policy" {
  role = aws_iam_role.step_functions_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = "*"
      }
    ]
  })
}




# --------------------------------
#   Lambdas
# --------------------------------


# Cria a Lambda de post_message
module "lambda_post_message" {
  source        = "./modules/aws/lambda"
  function_name = "conversational_debouncer_post_message"
  role_arn      = aws_iam_role.lambda_role.arn
  zip_file      = "./deployments/post_message.zip"
  layers = []
  environment_variables = {
    STEP_FUNCTION_ARN        = module.step_function_whatsapp_debounce.state_machine_arn
    DYNAMODB_TABLE           = module.dynamodb_received_messages.table_name
    OPENAI_API_KEY           = var.openai_api_key
    OPENAI_AUDIO_MODEL_NAME  = "whisper-1"
    OPENAI_VISION_MODEL_NAME = "gpt-4o-mini"
  }

  create_api_gw        = true
  api_gw_execution_arn = aws_apigatewayv2_api.conversational_debouncer_http_api.execution_arn
}


# Cria a Lambda de process_message
module "lambda_process_message" {
  source        = "./modules/aws/lambda"
  function_name = "conversational_debouncer_process_message"
  role_arn      = aws_iam_role.lambda_role.arn
  zip_file      = "./deployments/process_message.zip"
  layers = []
  environment_variables = {
    DYNAMODB_TABLE             = module.dynamodb_received_messages.table_name
    PROCESSING_LAMBDA_FUNCTION = module.lambda_conversational.function_name
    # add your chatbot lambda function name here
  }

}

# Creates the lambda that send the messages to the APIs (WhatsApp, Telegram, etc)
module "lambda_send_message_api" {
  source        = "./modules/aws/lambda"
  function_name = "conversational_debouncer_send_message_api"
  role_arn      = aws_iam_role.lambda_role.arn
  zip_file = "./deployments/send_message_api.zip"
  # Use Klayers for requests https://github.com/keithrozario/Klayers
  layers = ["arn:aws:lambda:us-west-2:770693421928:layer:Klayers-p312-aws-requests-auth:14"]
  environment_variables = {
    EVOLUTION_API_KEY      = var.evolution_api_key,
    EVOLUTION_API_BASE_URL = var.evolution_api_base_url
  }

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
    DYNAMODB_LOGS_TABLE              = module.dynamodb_conversational_logs.table_name
    OPENAI_LLM_MODEL_NAME            = var.openai_llm_model_name
    ENV                              = var.environment
    FIRECRAWL_API_KEY                = var.firecrawl_api_key
    TARGET_LAMBDA                    = module.lambda_send_message_api.lambda_arn
  }

}


# --------------------------------
#   Step Functions
# --------------------------------

# Cria a step function
module "step_function_whatsapp_debounce" {
  source                     = "./modules/aws/step_functions"
  step_functions_role_arn    = aws_iam_role.step_functions_role.arn
  process_message_lambda_arn = module.lambda_process_message.lambda_arn
}


# --------------------------------
#   API Gateway
# --------------------------------

# Cria o API Gateway
resource "aws_apigatewayv2_api" "conversational_debouncer_http_api" {
  name          = "conversational-debouncer-http-api-whatsapp"
  protocol_type = "HTTP"
}

# Stage da API
resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.conversational_debouncer_http_api.id
  name        = "$default"
  auto_deploy = true
}

# Configura os endpoints do API Gateway
module "api_gateway_post_message" {
  source            = "./modules/aws/api_gateway"
  api_id            = aws_apigatewayv2_api.conversational_debouncer_http_api.id
  method            = "POST"
  path              = "/conversational-debouncer-post-message"
  lambda_invoke_arn = module.lambda_post_message.lambda_invoke_arn
}


# --------------------------------
#   DynamoDB - Checkpointer
# --------------------------------

# Cria a tabela de checkpoints
module "dynamodb_conversational_checkpoints" {
  source         = "./modules/aws/dynamodb"
  table_name     = "conversational_checkpoints"
  hash_key_name  = "thread_id"
  hash_key_type  = "S"
  range_key_name = "sort_key"
  range_key_type = "S"
}

module "dynamodb_conversational_writes" {
  source         = "./modules/aws/dynamodb"
  table_name     = "conversational_writes"
  hash_key_name  = "thread_id"
  hash_key_type  = "S"
  range_key_name = "sort_key"
  range_key_type = "S"
}

module "dynamodb_conversational_logs" {
  source         = "./modules/aws/dynamodb"
  table_name     = "conversational_logs"
  hash_key_name  = "thread_id"
  hash_key_type  = "S"
  range_key_name = "timestamp"
  range_key_type = "S"
}