import json
import os
from abc import ABC, abstractmethod
from typing import Optional, Any, Callable, List, Dict

from dotenv import load_dotenv
from langchain_core.messages import SystemMessage, ToolMessage, AIMessage
from langchain_openai import ChatOpenAI

load_dotenv()


class Node(ABC):
    def __init__(
            self,
            name: str,
            tools: Optional[List] = None,
            state_update_fn: Optional[Callable] = None
    ):
        self.name = name
        self.tools = tools
        self.state_update_fn = state_update_fn

    @abstractmethod
    def process(self, state: Any, config: Dict) -> Dict:
        pass

    def update_state(self, state: Any):
        if self.state_update_fn:
            self.state_update_fn(state)


class LLMNode(Node, ABC):
    def __init__(
            self,
            name: str,
            system_message: str = '',
            msgs_to_extend: int = -12,
            output_model: Optional[Any] = None,
            tool_choice: str = 'auto',
            tools: Optional[List] = None,
            state_update_fn: Optional[Callable] = None
    ):
        super().__init__(name=name, tools=tools, state_update_fn=state_update_fn)
        self.system_message = system_message
        self.msgs_to_extend = msgs_to_extend
        self.output_model = output_model
        self.tool_choice = tool_choice
        self.llm = ChatOpenAI(
            temperature=0,
            model=os.getenv('OPENAI_LLM_MODEL_NAME')
        )

    def _get_messages(self, state: Any) -> List:
        messages = [SystemMessage(content=self.system_message)]

        start_index = len(state['messages']) + self.msgs_to_extend if self.msgs_to_extend < 0 else self.msgs_to_extend
        start_index = max(0, start_index)

        candidate_messages = state['messages'][start_index:]
        valid_messages = self._validate_message_sequence(candidate_messages)

        messages.extend(valid_messages)
        return messages

    @staticmethod
    def _validate_message_sequence(messages: List) -> List:
        valid_messages = []
        i = 0
        tool_call_ids_to_match = set()

        while i < len(messages):
            current_msg = messages[i]

            if hasattr(current_msg, 'tool_calls') and current_msg.tool_calls:
                for tool_call in current_msg.tool_calls:
                    tool_call_ids_to_match.add(tool_call.get('id'))
                valid_messages.append(current_msg)

            elif isinstance(current_msg, ToolMessage):
                if current_msg.tool_call_id in tool_call_ids_to_match:
                    valid_messages.append(current_msg)
                    tool_call_ids_to_match.remove(current_msg.tool_call_id)

            else:
                valid_messages.append(current_msg)

            i += 1

        return valid_messages

    @staticmethod
    def _handle_list_tool_message(messages: List) -> Optional[Dict]:
        if isinstance(messages[-1], ToolMessage):
            try:
                content = json.loads(messages[-1].content)
                if isinstance(content, Dict) and 'list_response' in content:
                    return {
                        'messages': [AIMessage(content=str(content), tool_calls=[])]
                    }
            except json.JSONDecodeError:
                pass
        return None
