import os
from abc import ABC, abstractmethod

import requests

from lambdas.debouncer.send_message_api.configs.logging_config import logger


class BaseMessageStrategy(ABC):
    def __init__(self):
        self.api_base_url = os.environ.get('EVOLUTION_API_BASE_URL')
        self.api_key = os.environ.get('EVOLUTION_API_KEY')

    @abstractmethod
    def send_message(self, phone_number: str, instance: str, **kwargs):
        pass

    def _make_request(self, endpoint: str, payload: dict, instance: str):
        url = f"{self.api_base_url}/{endpoint}/{instance}"
        headers = {"Content-Type": "application/json", "apikey": self.api_key}

        response = requests.post(url, json=payload, headers=headers)

        if str(response.status_code).startswith('20'):
            logger.info('Message sent successfully to %s', payload.get('number'))
            return True
        else:
            logger.error('Failed to send message: %s', response.text)
            return False
