import os
from typing import Any, Dict, List
from typing import Optional, Callable

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.constants import END
from langgraph.prebuilt import ToolNode
from langgraph.types import interrupt

from lambdas.e_commerce_chatbot.generics.nodes.base import Node


class StaticResponseNode(Node):
    def __init__(self, name: str, response: str, tool_calls=None, state_update_fn=None):
        super().__init__(name=name, state_update_fn=state_update_fn)
        self.response = response
        self.tool_calls = tool_calls or []

    def process(self, state: Any, config: Dict) -> Dict:
        self.update_state(state)
        return {
            'messages': [AIMessage(content=str(self.response), tool_calls=self.tool_calls)]
        }


class GetUserInputNode(Node):
    def __init__(
            self,
            name: str,
            update_field: str = 'messages',
            format_response: Callable = lambda response: [HumanMessage(content=response)]
    ):
        super().__init__(name=name)
        self.update_field = update_field
        self.format_response = format_response

    def process(self, state: Any, config: Dict) -> Dict[str, Any]:
        if os.getenv('ENV') == 'prod':
            response = interrupt("human_input")
            return {self.update_field: self.format_response(response)}

        if os.getenv('TEST_MODE') == 'true':
            if self.update_field == 'messages':
                messages = state.get("messages", [])
                if not messages:
                    raise ValueError("No messages found in state during test mode")
                return {'messages': messages}
            else:
                return {self.update_field: state.get(self.update_field, None)}

        response = input('User: ')
        if response.lower() == '/quit':
            return END

        return {self.update_field: self.format_response(response)}


class ToolCallingNode(Node):
    def __init__(self, name: str, tools: List[Any]):
        super().__init__(name=name)
        self.tools = tools
        self.tool_node = ToolNode(self.tools)

    def process(self, state: Any, config: Dict):
        try:
            tool_result = self.tool_node

            if isinstance(tool_result, dict) and tool_result.get("access_denied"):
                return {
                    "messages": [SystemMessage(content=f"🔒 {tool_result.get('error')}")],
                }

            return tool_result
        except Exception as e:
            return {
                "messages": [SystemMessage(content=f"Ocorreu um erro ao processar essa solicitação: {e}")]
            }


class FunctionalNode(Node):
    def __init__(self, name: str, fn: Optional[Callable] = None):
        super().__init__(name)
        self.fn = fn

    def process(self, state: Any, config: Dict) -> Dict:
        result = self.fn(state)

        if not isinstance(result, Dict):
            raise TypeError("The function must return a Dict")

        return result
