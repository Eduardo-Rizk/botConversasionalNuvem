import os
from typing import Dict

import boto3

from shared.configs.logging_config import logger


def verify_checkpointer(config: Dict) -> bool:
    thread_id = config["configurable"]["thread_id"]

    dynamodb_client = boto3.client('dynamodb')
    checkpointer_table = os.getenv('DYNAMODB_CHECKPOINT_TABLE')

    try:
        response = dynamodb_client.query(
            TableName=checkpointer_table,
            KeyConditionExpression="thread_id = :thread_id_value",
            ExpressionAttributeValues={":thread_id_value": {"S": thread_id}}
        )
        return response.get('Count', 0) > 0
    except Exception as e:
        logger.error(f"Erro ao verificar thread_id {thread_id} na tabela {checkpointer_table}: {e}")
        return False
