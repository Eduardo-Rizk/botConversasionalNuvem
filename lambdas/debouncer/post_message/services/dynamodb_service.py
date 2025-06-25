import boto3
import os
from decimal import Decimal
from typing import Dict, Any, Optional

from lambdas.debouncer.post_message.configs.logging_config import logger


class DynamoDBService:
    def __init__(self, table_name: Optional[str] = None):
        """
        Initialize DynamoDB service with a specific table.
        """
        self._dynamodb = boto3.resource('dynamodb')
        self._table_name = table_name or os.environ['DYNAMODB_TABLE']
        self._table = self._dynamodb.Table(self._table_name)

    @staticmethod
    def decimal_to_float(obj: Any) -> float:
        """
        Convert Decimal objects to float for JSON serialization.
        """
        if isinstance(obj, Decimal):
            return float(obj)
        raise TypeError(f'Type {obj.__class__.__name__} not serializable')

    def get_existing_message(self, instance_name: str, cellphone_number: str) -> Dict[str, Any]:
        """
        Retrieve an existing message from DynamoDB.
        """
        try:
            return self._table.get_item(
                Key={'instance_name': instance_name, 'cellphone_number': cellphone_number}
            )
        except Exception as e:
            logger.error(
                f"Failed to retrieve message for instance_name {instance_name} and phone {cellphone_number}: {str(e)}")
            raise

    def update_existing_message(
            self,
            instance_name: str,
            cellphone_number: str,
            existing_message: Dict[str, Any],
            new_text: str,
            timestamp: int
    ) -> Dict[str, Any]:
        """
        Update the existing message in DynamoDB.
        """
        logger.info(f"Updating existing message for {cellphone_number} in app {instance_name}")
        existing_text = existing_message.get('text', '')
        concatenated_text = f"{existing_text} {new_text}".strip()

        try:
            return self._table.update_item(
                Key={'instance_name': instance_name, 'cellphone_number': cellphone_number},
                UpdateExpression="SET #txt = :t, last_update = :lu",
                ExpressionAttributeNames={'#txt': 'text'},
                ExpressionAttributeValues={
                    ':t': concatenated_text,
                    ':lu': timestamp
                },
                ReturnValues="ALL_NEW"
            )['Attributes']
        except Exception as e:
            logger.error(
                f"Failed to update message for instance_name {instance_name} and phone {cellphone_number}: {str(e)}")
            raise

    def create_new_message(
            self,
            instance_name: str,
            cellphone_number: str,
            text: str,
            timestamp: int
    ) -> Dict[str, Any]:
        """
        Create a new message entry in DynamoDB.
        """
        logger.info(f"Creating new message for {cellphone_number} in app {instance_name}")
        try:
            self._table.put_item(
                Item={
                    'instance_name': instance_name,
                    'cellphone_number': cellphone_number,
                    'text': text,
                    'last_update': timestamp
                }
            )
            return {'text': text, 'last_update': timestamp}
        except Exception as e:
            logger.error(
                f"Failed to create new message for instance_name {instance_name} and phone {cellphone_number}: {str(e)}")
            raise

    def update_execution_arn(
            self,
            instance_name: str,
            cellphone_number: str,
            execution_arn: str
    ) -> None:
        """
        Update the execution ARN in the DynamoDB table.
        """
        self._table.update_item(
            Key={'instance_name': instance_name, 'cellphone_number': cellphone_number},
            UpdateExpression="SET execution_arn = :arn",
            ExpressionAttributeValues={':arn': execution_arn}
        )
