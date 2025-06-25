from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import boto3
import os
from datetime import datetime
import json

from langchain_core.messages import AIMessage


@dataclass
class LogStructure:
    thread_id: str
    timestamp: str
    state: Dict[str, Any]
    messages: List[Dict[str, str]]
    conversation_history: List[Dict[str, str]]
    tool_calling: Optional[List[Dict[str, Any]]] = None


class LogManager:
    def __init__(self):
        self.dynamodb_client = boto3.client('dynamodb')
        self.table_name = os.getenv('DYNAMODB_LOGS_TABLE')

    def get_conversation_history(self, thread_id: str) -> List[Dict[str, str]]:
        try:
            response = self.dynamodb_client.query(
                TableName=self.table_name,
                KeyConditionExpression='thread_id = :thread_id',
                ExpressionAttributeValues={
                    ':thread_id': {'S': thread_id}
                },
                ScanIndexForward=True  # Ordem cronológica
            )

            if not response['Items']:
                return []

            last_item = response['Items'][-1]
            if 'conversation_history' in last_item:
                return json.loads(last_item['conversation_history']['S'])
            return []

        except Exception as e:
            print(f"Erro ao recuperar histórico: {e}")
            return []

    def save_log(self, log: LogStructure):
        item = {
            'thread_id': {'S': log.thread_id},
            'timestamp': {'S': log.timestamp},
            'state': {'S': str(log.state)},
            'messages': {'S': str(log.messages)},
            'conversation_history': {'S': json.dumps(log.conversation_history, ensure_ascii=False, indent=4)}
        }
        if log.tool_calling:
            item['tool_calling'] = {'S': str(log.tool_calling)}

        try:
            self.dynamodb_client.put_item(TableName=self.table_name, Item=item)
        except Exception as e:
            print(f"Failed to save log: {e}")

    def format_and_save(self, thread_id: str, state: Dict, user_message: str, output: Dict):
        conversation_history = self.get_conversation_history(thread_id)

        messages = output.get('generate_output', {}).get('messages', [])
        if messages:
            last_message = messages[-1]
            ai_message = last_message.content if isinstance(last_message, AIMessage) else ""
            tool_calls = last_message.additional_kwargs.get('tool_calls', None) if isinstance(last_message, AIMessage) else None
        else:
            ai_message = ""
            tool_calls = None

        current_messages = [
            {"role": "user", "message": user_message},
            {"role": "AI", "message": ai_message},
        ]

        conversation_history.extend(current_messages)

        log = LogStructure(
            thread_id=thread_id,
            timestamp=datetime.utcnow().isoformat(),
            state=state,
            messages=current_messages,
            conversation_history=conversation_history,
            tool_calling=tool_calls,
        )

        self.save_log(log)
