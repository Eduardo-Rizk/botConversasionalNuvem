import os
import boto3
from boto3.dynamodb.conditions import Attr

from shared.configs.logging_config import logger


def _clear_table(table_name: str, partition_key: str = None, partition_value: str = None) -> None:
    dynamodb_resource = boto3.resource('dynamodb')
    table = dynamodb_resource.Table(table_name)

    scan_kwargs = {}
    if partition_key and partition_value:
        scan_kwargs['FilterExpression'] = Attr(partition_key).eq(partition_value)

    logger.info(f"Iniciando limpeza na tabela '{table_name}' com scan_kwargs: {scan_kwargs}")
    response = table.scan(**scan_kwargs)
    items = response.get('Items', [])

    with table.batch_writer() as batch:
        for item in items:
            key = {key_attr['AttributeName']: item[key_attr['AttributeName']]
                   for key_attr in table.key_schema}
            batch.delete_item(Key=key)
            logger.debug(f"Deletando item: {key}")

    while 'LastEvaluatedKey' in response:
        scan_kwargs['ExclusiveStartKey'] = response['LastEvaluatedKey']
        response = table.scan(**scan_kwargs)
        items = response.get('Items', [])
        with table.batch_writer() as batch:
            for item in items:
                key = {key_attr['AttributeName']: item[key_attr['AttributeName']]
                       for key_attr in table.key_schema}
                batch.delete_item(Key=key)
                logger.debug(f"Deletando item: {key}")

    logger.info(f"Limpeza concluída na tabela '{table_name}'.")


def amnesia() -> None:
    checkpoint_table = os.getenv('DYNAMODB_CHECKPOINT_TABLE')
    writes_table = os.getenv('DYNAMODB_WRITES_TABLE')

    if not checkpoint_table or not writes_table:
        raise ValueError("As variáveis de ambiente DYNAMODB_CHECKPOINT_TABLE e DYNAMODB_WRITES_TABLE devem estar definidas.")

    logger.info("Iniciando o amnesia total (clear all).")
    _clear_table(checkpoint_table)
    _clear_table(writes_table)
    logger.info("Amnesia total concluída.")


def partial_amnesia(thread_id: str) -> None:
    checkpoint_table = os.getenv('DYNAMODB_CHECKPOINT_TABLE')
    writes_table = os.getenv('DYNAMODB_WRITES_TABLE')

    if not checkpoint_table or not writes_table:
        raise ValueError("As variáveis de ambiente DYNAMODB_CHECKPOINT_TABLE e DYNAMODB_WRITES_TABLE devem estar definidas.")

    logger.info(f"Iniciando o partial amnesia para thread_id: {thread_id}")
    _clear_table(checkpoint_table, partition_key='thread_id', partition_value=thread_id)
    _clear_table(writes_table, partition_key='thread_id', partition_value=thread_id)
    logger.info("Partial amnesia concluída.")


def check_for_amnesia_commands(user_message: str, thread_id: str):
    logger.info(f"Check amnesia: Mensagem recebida -> {user_message}")
    command = user_message.strip().lower()
    logger.info(f'Command:{command}')

    if command in ["/clear-all", "/amnesia"]:
        try:
            amnesia()
            return f"Log: Memória total do agente apagada com sucesso."
        except Exception as e:
            logger.error(f"Erro ao executar amnesia total: {e}")
            return f"Erro ao apagar memória total: {str(e)}"

    if command in ["/clear-this", "/partial-amnesia"]:
        try:
            partial_amnesia(thread_id)
            return f"Log: Memória da thread {thread_id} apagada com sucesso."
        except Exception as e:
            logger.error(f"Erro ao executar partial amnesia: {e}")
            return f"Erro ao apagar memória total: {str(e)}"

    return None
