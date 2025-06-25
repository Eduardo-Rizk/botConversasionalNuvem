from abc import ABC, abstractmethod
from typing import Optional, Tuple
import boto3

from lambdas.debouncer.post_message.strategies.evolution_responses_strategies import ListResponseStrategy
from lambdas.debouncer.post_message.strategies.text_extraction_strategies import AudioExtractionStrategy, ImageExtractionStrategy


class MessageHandler(ABC):
    @abstractmethod
    def process(self, message: dict) -> Optional[Tuple[str, str, Optional[str]]]:
        pass


class EvolutionHandler(MessageHandler):
    def __init__(self):
        self.strategies = {
            'audioMessage': AudioExtractionStrategy(),
            'imageMessage': ImageExtractionStrategy(),
            'listResponseMessage': ListResponseStrategy()
        }
        self.dynamodb_client = boto3.client('dynamodb')

    def process(self, message: dict) -> Optional[Tuple[str, str, Optional[str]]]:
        if not self._is_valid_evolution_message(message):
            return None

        data = message.get('data', {})
        content = data.get('message', {})

        cellphone_number = data['key']['remoteJid'].split('@')[0]
        instance_name = message.get('instance')
        text = self._process_message_content(content)

        return cellphone_number, text, instance_name

    @staticmethod
    def _is_valid_evolution_message(message: dict) -> bool:
        return (
                'data' in message and
                'message' in message.get('data', {}) and
                not message.get('data', {}).get('key', {}).get('fromMe', False)
        )

    def _process_message_content(self, content: dict) -> Optional[str]:
        if 'conversation' in content:
            return content.get('conversation')

        for message_type in self.strategies:
            if message_type in content:
                return self.strategies[message_type].process(content)

        return None
