from typing import Any


class Write:
    def __init__(
            self,
            thread_id: str,
            checkpoint_ns: str,
            checkpoint_id: str,
            task_id: str,
            idx: int,
            channel: str,
            type: str,
            value: Any,
    ):
        self.thread_id = thread_id
        self.checkpoint_ns = checkpoint_ns
        self.checkpoint_id = checkpoint_id
        self.task_id = task_id
        self.idx = idx
        self.channel = channel
        self.type = type
        self.value = value

    def to_dynamodb_item(self):
        return {
            'thread_id': self.thread_id,
            'sort_key': f"{self.checkpoint_ns}#{self.checkpoint_id}#{self.task_id}#{self.idx:010d}",
            'task_id': self.task_id,
            'idx': self.idx,
            'channel': self.channel,
            'type': self.type,
            'value': self.value
        }

    @classmethod
    def from_dynamodb_item(cls, item):
        sort_key_parts = item['sort_key'].split('#')
        value = item['value']

        if hasattr(value, 'value'):
            value = bytes(value.value)

        return cls(
            thread_id=item['thread_id'],
            checkpoint_ns=sort_key_parts[0],
            checkpoint_id=sort_key_parts[1],
            task_id=item['task_id'],
            idx=item['idx'],
            channel=item['channel'],
            type=item['type'],
            value=value
        )
