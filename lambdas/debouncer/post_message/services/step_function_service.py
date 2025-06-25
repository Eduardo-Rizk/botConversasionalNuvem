import os
import json
import boto3
from typing import Dict, Any, Optional

from lambdas.debouncer.post_message.configs.logging_config import logger
from lambdas.debouncer.post_message.services.dynamodb_service import DynamoDBService


class StepFunctionService:
    def __init__(self, step_function_arn: Optional[str] = None):
        """
        Initialize Step Functions service.
        """
        self._step_functions = boto3.client('stepfunctions')
        self._step_function_arn = step_function_arn or os.environ['STEP_FUNCTION_ARN']
        self._dynamodb_service = DynamoDBService()

    def cancel_existing_execution(self, existing_message: Dict[str, Any]) -> None:
        """
        Cancel an existing Step Functions execution if it exists.
        """
        if 'execution_arn' in existing_message:
            execution_arn = existing_message['execution_arn']
            logger.info(f"Cancelling existing execution {execution_arn}")

            try:
                self._step_functions.stop_execution(
                    executionArn=execution_arn,
                    error='NewMessageReceived',
                    cause='A new message was received, cancelling processing.'
                )
            except self._step_functions.exceptions.ExecutionDoesNotExist:
                logger.warning(f"Execution {execution_arn} does not exist, might have completed already.")
            except Exception as e:
                logger.error(f"Failed to cancel execution {execution_arn}: {str(e)}")

    def start_step_function_execution(
            self,
            instance_name: str,
            cellphone_number: str,
            message_text: str,
            last_update: int
    ) -> str:
        """
        Start a new Step Functions execution.
        """
        try:
            execution = self._step_functions.start_execution(
                stateMachineArn=self._step_function_arn,
                input=json.dumps({
                    'instance_name': instance_name,
                    'cellphone_number': cellphone_number,
                    'message': message_text,
                    'last_update': last_update
                }, default=self._dynamodb_service.decimal_to_float)
            )
            return execution['executionArn']
        except Exception as e:
            logger.error(
                f"Failed to start Step Function execution for instance_name {instance_name} and phone {cellphone_number}: {str(e)}")
            raise
