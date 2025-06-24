from typing import Any


def should_use_tools(state: Any, tool_node_name: str, return_node: str):
    messages = state['messages']
    last_message = messages[-1]
    tool_calls = last_message.tool_calls

    if tool_calls:
        return tool_node_name
    return return_node
