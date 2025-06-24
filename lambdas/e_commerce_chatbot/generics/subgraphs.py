from typing import Optional, Dict, TypedDict, Callable

from langgraph.graph import StateGraph


class SubgraphBuilder:
    def __init__(self, state: type(TypedDict), name: str, suffix: str):
        self.graph = StateGraph(state)
        self.name = name
        self.suffix = suffix

    def _format_node_name(self, name: str) -> str:
        return f"{name}#{self.suffix}"

    def add_node(self, node, process_func: Callable = None, config: Optional[Dict] = None) -> str:
        node_name = self._format_node_name(node.name)
        node.name = node_name

        if process_func is None:
            process_func = node.process

        if config is None:
            callable_process = process_func
        else:
            callable_process = lambda state: process_func(state, config)

        self.graph.add_node(node_name, callable_process)
        return node_name

    def add_edge(self, from_node: str, to_node: str):
        self.graph.add_edge(from_node, to_node)

    def compile(self):
        compiled_graph = self.graph.compile()
        compiled_graph.name = self.name
        return compiled_graph
