import os

import boto3
from boto3.dynamodb.conditions import Key
from typing import Any, Tuple, Dict, Iterator, Optional, Sequence
import time

from langchain_core.runnables import RunnableConfig

from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    ChannelVersions,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
    get_checkpoint_id,
)

from langgraph.checkpoint.serde.base import SerializerProtocol

from lambdas.e_commerce_chatbot.memory.write import Write
from shared.configs.logging_config import logger


class DynamoDBSaver(BaseCheckpointSaver):
    """A checkpoint saver that stores checkpoints in DynamoDB using JSON-compatible formats."""

    WIDTH = 20  # Width for zero-padding timestamps

    def __init__(
            self,
            table_name: str,
            writes_table_name: str,
            region_name: str = os.getenv('CHECKPOINTER_AWS_REGION'),
            endpoint_url: Optional[str] = None,
            serde: Optional[SerializerProtocol] = None,
    ) -> None:
        super().__init__(serde=serde)
        self.dynamodb = boto3.resource('dynamodb', region_name=region_name, endpoint_url=endpoint_url)
        self.table = self.dynamodb.Table(table_name)
        self.writes_table = self.dynamodb.Table(writes_table_name)

    def get_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        """Fetch a checkpoint tuple using a given configuration."""
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
        checkpoint_id = get_checkpoint_id(config)

        if checkpoint_id:
            # Need to scan for item with matching checkpoint_id
            response = self.table.query(
                KeyConditionExpression=Key('thread_id').eq(thread_id) & Key('sort_key').begins_with(
                    f'{checkpoint_ns}#'),
                FilterExpression=Key('checkpoint_id').eq(checkpoint_id)
            )
            items = response.get('Items', [])
            if not items:
                return None
            item = items[0]
        else:
            # Fetch the latest checkpoint for the thread_id and checkpoint_ns
            response = self.table.query(
                KeyConditionExpression=Key('thread_id').eq(thread_id) & Key('sort_key').begins_with(
                    f'{checkpoint_ns}#'),
                ScanIndexForward=False,  # Descending order
                Limit=1
            )
            items = response.get('Items', [])
            if not items:
                return None
            item = items[0]

        # Reconstruct the checkpoint tuple from the item
        sort_key_parts = item['sort_key'].split('#')
        checkpoint_ns = sort_key_parts[0]
        checkpoint_id = item['checkpoint_id']

        config_values = {
            "thread_id": thread_id,
            "checkpoint_ns": checkpoint_ns,
            "checkpoint_id": checkpoint_id,
        }

        checkpoint_type = item['type']

        checkpoint_data = item['checkpoint']
        if hasattr(checkpoint_data, 'value'):
            checkpoint_data = bytes(checkpoint_data.value)

        # Deserialize checkpoint data
        checkpoint = self.serde.loads_typed((checkpoint_type, checkpoint_data))

        # Get pending writes from "checkpoint_writes" table
        write_sort_key_prefix = f'{checkpoint_ns}#{checkpoint_id}#'
        pending_writes = []

        # Query writes_table
        response = self.writes_table.query(
            KeyConditionExpression=Key('thread_id').eq(thread_id) & Key('sort_key').begins_with(write_sort_key_prefix),
            ScanIndexForward=True
        )
        write_items = response.get('Items', [])

        for write_item in write_items:
            task_id = write_item['task_id']
            channel = write_item['channel']
            value_type = write_item['type']
            value_data = write_item['value']

            if hasattr(value_data, 'value'):
                value_data = bytes(value_data.value)

            value = self.serde.loads_typed((value_type, value_data))
            pending_writes.append((task_id, channel, value))

        metadata = item['metadata']
        if hasattr(metadata, 'value'):
            metadata = bytes(metadata.value)

        logger.info(f"Checkpoint type: {checkpoint_type}")
        logger.info(f"Raw metadata type: {type(metadata)}")

        try:
            deserialized_metadata = self.serde.loads_typed((checkpoint_type, metadata))
            if isinstance(deserialized_metadata, (tuple, list)) and len(deserialized_metadata) > 1:
                metadata = deserialized_metadata[1]
            else:
                metadata = deserialized_metadata

            logger.info(f"Deserialized metadata type: {type(metadata)}")
        except Exception as e:
            logger.error(f"Erro ao deserializar metadata: {str(e)}", exc_info=True)
            metadata = {}

        # Get parent config if any
        parent_checkpoint_id = item.get('parent_checkpoint_id')
        if parent_checkpoint_id:
            parent_config = {
                "configurable": {
                    "thread_id": thread_id,
                    "checkpoint_ns": checkpoint_ns,
                    "checkpoint_id": parent_checkpoint_id,
                }
            }
        else:
            parent_config = None

        return CheckpointTuple(
            {"configurable": config_values},
            checkpoint,
            metadata,
            parent_config,
            pending_writes,
        )

    def list(
            self,
            config: Optional[RunnableConfig],
            *,
            filter: Optional[Dict[str, Any]] = None,
            before: Optional[RunnableConfig] = None,
            limit: Optional[int] = None,
    ) -> Iterator[CheckpointTuple]:
        """List checkpoints that match a given configuration and filter criteria."""

        if config is None:
            raise ValueError("config must be provided for listing checkpoints in DynamoDB")

        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
        checkpoint_ns_prefix = f'{checkpoint_ns}#'

        query_kwargs = {
            'KeyConditionExpression': Key('thread_id').eq(thread_id) & Key('sort_key').begins_with(
                checkpoint_ns_prefix),
            'ScanIndexForward': False  # Descending order
        }

        if limit is not None:
            query_kwargs['Limit'] = limit

        response = self.table.query(**query_kwargs)
        items = response.get('Items', [])

        for item in items:
            try:
                checkpoint_type = item['type']
                checkpoint_data = item['checkpoint']
                if hasattr(checkpoint_data, 'value'):
                    checkpoint_data = bytes(checkpoint_data.value)

                checkpoint = self.serde.loads_typed((checkpoint_type, checkpoint_data))

                sort_key_parts = item['sort_key'].split('#')
                checkpoint_ns = sort_key_parts[0]
                checkpoint_id = item['checkpoint_id']

                metadata = item['metadata']
                if hasattr(metadata, 'value'):
                    metadata = bytes(metadata.value)
                metadata = self.serde.loads_typed((checkpoint_type, metadata))[1]

                parent_checkpoint_id = item.get('parent_checkpoint_id')
                if parent_checkpoint_id:
                    parent_config = {
                        "configurable": {
                            "thread_id": item['thread_id'],
                            "checkpoint_ns": checkpoint_ns,
                            "checkpoint_id": parent_checkpoint_id,
                        }
                    }
                else:
                    parent_config = None

                yield CheckpointTuple(
                    {
                        "configurable": {
                            "thread_id": item['thread_id'],
                            "checkpoint_ns": checkpoint_ns,
                            "checkpoint_id": checkpoint_id,
                        }
                    },
                    checkpoint,
                    metadata,
                    parent_config,
                )
            except Exception as e:
                logger.error(f"Erro ao processar item {item}: {str(e)}", exc_info=True)
                continue

    def put(
            self,
            config: RunnableConfig,
            checkpoint: Checkpoint,
            metadata: CheckpointMetadata,
            new_versions: ChannelVersions,
    ) -> RunnableConfig:
        """Store a checkpoint with its configuration and metadata."""

        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
        checkpoint_id = checkpoint["id"]
        checkpoint_created_at = int(time.time() * 1000)
        sort_key = f'{checkpoint_ns}#{checkpoint_created_at:0{self.WIDTH}d}'

        type_, checkpoint_data = self.serde.dumps_typed(checkpoint)

        parent_checkpoint_id = config["configurable"].get("checkpoint_id")

        item = {
            'thread_id': thread_id,
            'sort_key': sort_key,
            'checkpoint_id': checkpoint_id,
            'parent_checkpoint_id': parent_checkpoint_id,
            'type': type_,
            'checkpoint': checkpoint_data,
            'metadata': self.serde.dumps_typed(metadata)[1],
        }

        self.table.put_item(Item=item)

        return {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_ns": checkpoint_ns,
                "checkpoint_id": checkpoint_id,
            }
        }

    def put_writes(
            self,
            config: RunnableConfig,
            writes: Sequence[Tuple[str, Any]],
            task_id: str,
            task_path: str = ""
    ) -> None:
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"]["checkpoint_ns"]
        checkpoint_id = config["configurable"]["checkpoint_id"]

        if checkpoint_id is None:
            raise ValueError("Missing checkpoint_id")

        with self.writes_table.batch_writer() as batch:
            for idx, (channel, value) in enumerate(writes):
                type_, serialized_value = self.serde.dumps_typed(value)

                write = Write(
                    thread_id=thread_id,
                    checkpoint_ns=checkpoint_ns,
                    checkpoint_id=checkpoint_id,
                    task_id=task_id,
                    idx=idx,
                    channel=channel,
                    type=type_,
                    value=serialized_value
                )

                batch.put_item(Item=write.to_dynamodb_item())
