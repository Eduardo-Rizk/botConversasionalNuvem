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
from lambdas.e_commerce_chatbot.memory.log_manager import LogManager
from shared.configs.logging_config import logger

container = initialize_lambda_resources(['all'])


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

        # Check if the output is a tuple with two elements
        # If so, extract the second element (the node inside the subgraph or the graph)
        # Graph example: ((), {'judy_generic': ... })
        # Subgraph example: ((subgraph_greetings), {'judy_greetings': ... })
        if isinstance(output, tuple) and len(output) == 2:
            output_data = output[1]
        else:
            output_data = output  # Otherwise, use the output as is

        for key in output_data:
            # Identify the node by checking if it starts with 'judy' or 'list'
            # These prefixes indicate that the node contains the desired response from the LLM
            if key.startswith(('judy', 'list')):
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
    validation_error = validate_event(event, ['recipientNumber', 'message'])
    if validation_error:
        return validation_error

    logger.info(f"Received Event: {event}")

    recipient_number = event["recipientNumber"]
    message_content = ""

    original_message = event.get("originalMessage", {})
    message_type = original_message.get("type")

    if message_type == 'text':
        message_content = original_message.get("text", "")
    elif message_type == 'flow':
        flow_data = original_message.get("flow", {})
        message_content = flow_data.get("fields", {}).get("password", "")
    elif message_type == 'button':
        button_reply = original_message.get("button", {})
        message_content = button_reply.get("id", "")

    config = create_thread_config(recipient_number)

    amnesia_response = check_for_amnesia_commands(message_content, thread_id=config["configurable"]["thread_id"])
    if amnesia_response:
        return message_sender(TextMessage(to=recipient_number, text={"body": amnesia_response}))

    special_response = check_for_special_commands(message_content, thread_id=config["configurable"]["thread_id"])
    if special_response:
        return message_sender(TextMessage(to=recipient_number, text={"body": special_response}))

    graph = create_workflow(config=config)
    has_checkpoint = verify_checkpointer(config)
    state = _initialize_state(message_content, has_checkpoint, recipient_number)

    try:
        response_messages = process_graph(graph, state, config, message_content, has_checkpoint)
        logger.info(f"response_messages: {response_messages}")

        for message in response_messages:
            message = bold_correction(message)
            message_sender(message)
            time.sleep(0.8)  # delay entre as mensagens

        return {
            "statusCode": 200,
            "body": json.dumps({"messages_sent": len(response_messages)})
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
