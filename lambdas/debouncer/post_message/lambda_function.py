import json
import time

from lambdas.debouncer.post_message.configs.logging_config import logger
from lambdas.debouncer.post_message.services.dynamodb_service import DynamoDBService
from lambdas.debouncer.post_message.services.step_function_service import StepFunctionService
from lambdas.debouncer.post_message.webhook_handler import EvolutionHandler


class MessageProcessor:
    def __init__(self, dynamodb_service, step_function_service, evolution_handler):
        self.dynamodb_service = dynamodb_service
        self.step_function_service = step_function_service
        self.evolution_handler = evolution_handler

    def process_event(self, event):
        """Processa o evento recebido."""
        logger.info("Received event: %s", json.dumps(event))
        message = json.loads(event["body"])
        timestamp = int(time.time())

        # Processa a mensagem com o EvolutionHandler
        result = self.evolution_handler.process(message)
        if not result:
            logger.warning("Thread ID not found in checkpoint table, skipping processing.")
            return {
                "statusCode": 404,
                "body": json.dumps("Thread ID not found in checkpoint table"),
            }

        cellphone_number, text, instance_name = result
        logger.info("Received message from %s in app %s: %s", cellphone_number, instance_name, text)

        updated_message = self._handle_message(instance_name, cellphone_number, text, timestamp)
        execution_arn = self._start_execution_arn(instance_name, cellphone_number, updated_message)

        return {
            "statusCode": 200,
            "body": json.dumps("Message received and Step Functions execution started"),
        }

    def _handle_message(self, instance_name, cellphone_number, text, timestamp):
        """Verifica e atualiza mensagens no DynamoDB."""
        response = self.dynamodb_service.get_existing_message(instance_name, cellphone_number)

        if "Item" in response:
            existing_message = response["Item"]
            logger.info("Existing message found: %s", existing_message)
            self.step_function_service.cancel_existing_execution(existing_message)
            return self.dynamodb_service.update_existing_message(
                instance_name, cellphone_number, existing_message, text, timestamp
            )
        else:
            return self.dynamodb_service.create_new_message(
                instance_name, cellphone_number, text, timestamp
            )

    def _start_execution_arn(self, instance_name, cellphone_number, updated_message):
        """Inicia a execução do Step Functions e atualiza o ARN no DynamoDB."""
        execution_arn = self.step_function_service.start_step_function_execution(
            instance_name,
            cellphone_number,
            updated_message["text"],
            updated_message["last_update"],
        )
        self.dynamodb_service.update_execution_arn(instance_name, cellphone_number, execution_arn)
        return execution_arn


def lambda_handler(event, context):
    try:
        dynamodb_service = DynamoDBService()
        step_function_service = StepFunctionService()
        evolution_handler = EvolutionHandler()

        processor = MessageProcessor(dynamodb_service, step_function_service, evolution_handler)
        return processor.process_event(event)
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps("Internal server error"),
        }
