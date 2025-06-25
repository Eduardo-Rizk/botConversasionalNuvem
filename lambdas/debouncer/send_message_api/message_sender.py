from lambdas.debouncer.send_message_api.strategies.list_message_strategy import ListMessageStrategy
from lambdas.debouncer.send_message_api.strategies.text_message_strategy import TextMessageStrategy


class MessageSender:
    def __init__(self):
        self._strategies = {
            'text': TextMessageStrategy(),
            'list': ListMessageStrategy()
        }

    def send_message(self, message_type: str, phone_number: str, instance: str, **kwargs):
        strategy = self._strategies.get(message_type)
        if not strategy:
            raise ValueError(f"Unsupported message type: {message_type}")

        return strategy.send_message(phone_number, instance, **kwargs)
