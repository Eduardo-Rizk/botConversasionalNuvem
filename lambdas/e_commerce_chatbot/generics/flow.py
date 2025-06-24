from typing import Callable, Dict

from langchain_core.runnables.graph import MermaidDrawMethod
from langgraph.graph.state import CompiledStateGraph


def run_subgraph(create_subgraph_fn: Callable[[], CompiledStateGraph], initial_state: Dict):
    graph = create_subgraph_fn()

    try:
        for output in graph.stream(initial_state):
            print(f'Output: {output}')
    except Exception as e:
        print(f'Error during graph execution: {e}')


def run_subgraph_test(create_subgraph_fn: Callable[[], CompiledStateGraph], initial_state: Dict):
    graph = create_subgraph_fn()
    outputs = []

    try:
        for output in graph.stream(initial_state):
            outputs.append(output)
    except Exception as e:
        raise RuntimeError(f"Erro na execução do grafo: {e}")

    return outputs


def save_graph_as_png(graph, file_path):
    graph.get_graph(xray=1).draw_mermaid_png(
        draw_method=MermaidDrawMethod.PYPPETEER,
        output_file_path=file_path
    )
    print(f"Graph saved as '{file_path}'")
