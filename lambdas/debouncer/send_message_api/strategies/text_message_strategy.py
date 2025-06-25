from lambdas.debouncer.send_message_api.strategies.base_message_strategy import BaseMessageStrategy


class TextMessageStrategy(BaseMessageStrategy):
    def send_message(self, phone_number: str, instance: str, **kwargs):
        payload = {
            "number": str(phone_number),
            "text": kwargs.get('message_to_send')
        }

        return self._make_request('sendText', payload, instance)
