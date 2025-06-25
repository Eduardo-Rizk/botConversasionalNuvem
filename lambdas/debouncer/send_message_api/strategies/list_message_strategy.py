from lambdas.debouncer.send_message_api.strategies.base_message_strategy import BaseMessageStrategy


class ListMessageStrategy(BaseMessageStrategy):
    def send_message(self, phone_number: str, instance: str, **kwargs):
        payload = {
            "number": str(phone_number),
            "title": kwargs.get('title'),
            "description": kwargs.get('description'),
            "buttonText": kwargs.get('button_text'),
            "sections": kwargs.get('sections'),
            "footerText": kwargs.get('footerText')
        }

        return self._make_request('sendList', payload, instance)
