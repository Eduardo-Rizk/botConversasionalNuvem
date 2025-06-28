import json
import os
import time
from textwrap import dedent
from typing import Dict, List

import boto3
from langchain_core.messages import HumanMessage
from langgraph.types import Command

from lambdas.e_commerce_chatbot.graph import create_workflow
from lambdas.e_commerce_chatbot.memory.amnesia import check_for_amnesia_commands
from lambdas.e_commerce_chatbot.memory.utils import verify_checkpointer
from shared.configs.logging_config import logger
from lambdas.e_commerce_chatbot.memory.log_manager import LogManager
from lambdas.e_commerce_chatbot.utils.lambda_utils import validate_event, split_message, bold_correction

from lambdas.e_commerce_chatbot.send_message import send_message_to_wpp

def create_thread_config(instance: str, cellphone: str) -> dict:
    """
    Cria a configuração do thread baseado na instância e número do celular.
    """
    thread_id = f'{instance}#{cellphone}'
    return {"configurable": {"thread_id": thread_id}}


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


def initialize_state(user_message: str, has_checkpoint: bool) -> dict:
    if has_checkpoint:
        return {"messages": HumanMessage(content=user_message)}
    return {
        'messages': HumanMessage(content=user_message),
        'route': 'generic'
    }


def stream_graph(graph, input_data, config: Dict):
    collected_outputs = []

    stream = graph.stream(input_data, config=config, subgraphs=True)

    for output in stream:
        logger.info(f"Output: {output}")

        if isinstance(output, tuple) and len(output) == 2:
            output_data = output[1]
        else:
            output_data = output

        for key in output_data:
            # Identify the node by checking if it starts with 'judy' or 'list'
            # These prefixes indicate that the node contains the desired response from the LLM
            if key.startswith(('ecom')):
                collected_outputs.append((key, output_data[key]))

    if not collected_outputs:
        raise RuntimeError("Nenhum output gerado pelo grafo")

    return collected_outputs


def process_graph(graph, state, config, user_message, has_checkpoint) -> list:
    log_manager = LogManager()
    thread_id = config["configurable"]["thread_id"]

    try:
        input_data = state
        if has_checkpoint:
            input_data = Command(resume=user_message) if user_message else state
        collected_outputs = stream_graph(graph, input_data, config)

        log_manager.format_and_save(thread_id, state, user_message, dict(collected_outputs))

        return [output['messages'][-1].content for _, output in collected_outputs]
    except Exception as e:
        logger.error(f"Erro no processamento do grafo: {e}")
        raise


def lambda_handler(event, context):
    validation_error = validate_event(event, ['phone_number', 'message', 'instance'])
    if validation_error:
        return validation_error

    phone_number = event["phone_number"]
    user_message = event["message"]
    instance = event["instance"]

    config = create_thread_config(instance, phone_number)

    special_response = check_for_amnesia_commands(user_message=user_message, thread_id=config["configurable"]["thread_id"])
    if special_response:
        return send_message_to_wpp(phone_number, special_response, instance)

    graph = create_workflow(config=config)
    has_checkpoint = verify_checkpointer(config)
    state = initialize_state(user_message, has_checkpoint)

    try:
        response_messages = process_graph(graph, state, config, user_message, has_checkpoint)
        logger.info(f"response_messages: {response_messages}")

        for message in response_messages:
            message = bold_correction(message)
            split_messages = split_message(message)
            for part in split_messages:
                send_message_to_wpp(phone_number, part, instance)

        return {
            "statusCode": 200,
            "body": json.dumps({"messages_sent": len(response_messages)})
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
