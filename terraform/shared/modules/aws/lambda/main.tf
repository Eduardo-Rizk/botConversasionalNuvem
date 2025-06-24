resource "aws_lambda_function" "this" {
  function_name = var.function_name
  role          = var.role_arn
  handler       = var.handler
  runtime       = var.runtime
  timeout       = var.timeout
  memory_size   = var.memory_size
  filename = var.zip_file

  # Layer
  layers = var.layers

  environment {
    variables = var.environment_variables
  }

  source_code_hash = filebase64sha256(var.zip_file)
}