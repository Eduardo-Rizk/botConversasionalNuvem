from langchain_core.messages import HumanMessage
from langgraph.constants import START
from langgraph.graph import StateGraph
from pydantic import BaseModel
from lambdas.e_commerce_chatbot.generics.nodes.functional import GetUserInputNode, ToolCallingNode, FunctionalNode
from lambdas.e_commerce_chatbot.generics.nodes.llm import StructuredOutputLLMNode, SimpleLLMNode
from lambdas.e_commerce_chatbot.graphs.prompts import ROUTER_PROMPT
from lambdas.e_commerce_chatbot.memory.checkpointer import DynamoDBSaver
from lambdas.e_commerce_chatbot.generics.flow import save_graph_as_png

from lambdas.e_commerce_chatbot.subgraphs.generic.subgraph import create_generic_subgraph
from lambdas.e_commerce_chatbot.subgraphs.cancelation.subgraph import create_fallback_subgraph
from lambdas.e_commerce_chatbot.subgraphs.order_status.subgraph import create_order_status_subgraph


import os
from typing import Dict

from lambdas.e_commerce_chatbot.graphs.states import Routes, GraphState


class Router(BaseModel):
    route: Routes
    
    
    

get_user_input = GetUserInputNode(name="get_user_input")

router_node = StructuredOutputLLMNode(name="router_node", system_message=ROUTER_PROMPT, output_model=Router)

checkpointer = DynamoDBSaver(
    table_name=os.getenv('DYNAMODB_CHECKPOINT_TABLE'),
    writes_table_name=os.getenv('DYNAMODB_WRITES_TABLE')
)




def create_workflow(config: Dict = None):
    workflow = StateGraph(GraphState)
    
    subgraph_generic = create_generic_subgraph(config=config)
    subgraph_fallback = create_fallback_subgraph(config=config)
    subgraph_order_status = create_order_status_subgraph(config=config)
    
    
    workflow.add_node(subgraph_generic.name, subgraph_generic)
    workflow.add_node(subgraph_fallback.name, subgraph_fallback)
    workflow.add_node(subgraph_order_status.name, subgraph_order_status)
    
    
    
    # router
    def route_after_prediction(state: GraphState) -> str:
        routes = {
            'cancellation': subgraph_fallback.name,
            'generic': subgraph_generic.name,
            'order_status': subgraph_order_status.name
            
        }
        return routes.get(state['route'], subgraph_generic.name)
    
    
    workflow.add_node(get_user_input.name, lambda state: get_user_input.process(state, config))
    workflow.add_node(router_node.name, lambda state: router_node.process(state, config))
    
    
    workflow.add_edge(START, router_node.name)
    
    path_map = [subgraph_fallback.name, subgraph_generic.name, subgraph_order_status.name]
    
    workflow.add_conditional_edges(router_node.name, route_after_prediction, path_map=path_map)
    
    
    workflow.add_edge(subgraph_fallback.name, get_user_input.name)
    workflow.add_edge(subgraph_order_status.name, get_user_input.name)
    workflow.add_edge(subgraph_generic.name, get_user_input.name)
    
    
    workflow.add_edge(get_user_input.name, router_node.name)
    
    if os.getenv('ENV') == 'prod':
        return workflow.compile(checkpointer=checkpointer)

    return workflow.compile()



def run_graph():
    config = {"configurable": {"thread_id": "+5511999999999"}}

    graph = create_workflow(config=config)
    if os.getenv('ENV') == 'dev':
        save_graph_as_png(graph, 'docs/graph_img/graph.png')
        pass

    initial_state = {
        'messages': HumanMessage(content='Olá, tudo bem?'),
        'route': 'generic',
    }

    try:
        for output in graph.stream(initial_state, config=config, subgraphs=True):
            print(f'output: {output}')

    except Exception as e:
        print(f'Error: {e}')


if __name__ == '__main__':
    run_graph()


    
    
    
    