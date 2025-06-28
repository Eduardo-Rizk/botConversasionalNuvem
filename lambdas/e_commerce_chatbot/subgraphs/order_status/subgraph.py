from typing import Optional, Dict
from langgraph.graph import END, START

from lambdas.e_commerce_chatbot.graphs.prompts import HELP_WITH_ACTIVE_ORDER
from lambdas.e_commerce_chatbot.subgraphs.order_status.prompts import STATUS_ORDER_PROMPT
from lambdas.e_commerce_chatbot.generics.nodes.llm import SimpleLLMNode, StructuredOutputLLMNode, StateUpdateStructureOutputLLMNode
from lambdas.e_commerce_chatbot.generics.nodes.functional import ToolCallingNode, GetUserInputNode
from lambdas.e_commerce_chatbot.subgraphs.order_status.stuctureOutput import GetsOrderNumber
from lambdas.e_commerce_chatbot.subgraphs.order_status.tools import check_status

from langgraph.prebuilt import tools_condition
from lambdas.e_commerce_chatbot.generics.subgraphs import SubgraphBuilder
from lambdas.e_commerce_chatbot.graphs.states import GraphState

from dotenv import load_dotenv
from lambdas.e_commerce_chatbot.graphs.states import GraphState
from langchain_core.messages import HumanMessage


    

def create_order_status_subgraph(config: Optional[Dict] = None):
    
    builder = SubgraphBuilder(GraphState, name = 'subgraph_order_status', suffix = 'order_status')
    
    order_tools = [ check_status]
    
    ask_order_number = builder.add_node(SimpleLLMNode(name="ecom_ask_order_number", system_message = HELP_WITH_ACTIVE_ORDER), config=config)
    
    saves_order_number = builder.add_node(StateUpdateStructureOutputLLMNode(name= "saves_order_number_state",output_model=GetsOrderNumber,state_field="order_id", attribute="order_id"), config=config)
    
    order_status_node = builder.add_node(SimpleLLMNode(name = "ecom_order_status_node", system_message=STATUS_ORDER_PROMPT, tools = order_tools), config=config)
    
    order_status_tools_node = builder.add_node(ToolCallingNode(name='order_status_tools_nodes', tools=order_tools))
    
    get_user_input_order_status = builder.add_node(GetUserInputNode(name='get_user_input_order_status'))

    
    
    builder.graph.add_edge(START, ask_order_number)
    builder.graph.add_edge(ask_order_number, get_user_input_order_status)
    
    builder.graph.add_edge(get_user_input_order_status, saves_order_number)

    builder.graph.add_edge(saves_order_number, order_status_node)
    
    builder.graph.add_conditional_edges(
    order_status_node,
    tools_condition,
    {
        "tools": order_status_tools_node,
        END: END,
    },
    )
    
    builder.graph.add_edge(order_status_tools_node, order_status_node)
    return builder.compile()




load_dotenv()

def test_order_status_subgraph():
    
    subgraph = create_order_status_subgraph()
    
    initial_state = GraphState(
        messages=[HumanMessage(content="Quero saber o status do meu pedido")],
        order_id=None,
        route="order_status"
    )
    
    config = {"configurable": {"thread_id": "test-thread-1"}}
    
    for step in subgraph.stream(initial_state, config=config):
        print(f"Executando: {list(step.keys())}")
        for node_name, node_output in step.items():
            print(f"{node_name}: {node_output}")
        print("-" * 50)
    


if __name__ == "__main__":
    test_order_status_subgraph()
    
    
    
    
    