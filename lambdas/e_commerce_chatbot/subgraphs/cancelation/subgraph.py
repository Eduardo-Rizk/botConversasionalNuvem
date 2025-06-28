from lambdas.e_commerce_chatbot.subgraphs.cancelation.state import CancelationState
from typing import Optional, Dict
from lambdas.e_commerce_chatbot.generics.subgraphs import SubgraphBuilder

from lambdas.e_commerce_chatbot.subgraphs.cancelation.nodes import load_order_info_node

from lambdas.e_commerce_chatbot.generics.nodes.functional import ToolCallingNode, FunctionalNode, GetUserInputNode

from lambdas.e_commerce_chatbot.generics.nodes.llm import SimpleLLMNode
from lambdas.e_commerce_chatbot.graphs.prompts import HELP_WITH_ACTIVE_ORDER

from lambdas.e_commerce_chatbot.subgraphs.cancelation.prompts import FALLBACK_ASK_MOTIVATION, FALLBACK_NODE_PROMPT

from lambdas.e_commerce_chatbot.subgraphs.cancelation.tools import fallback_notification

from langgraph.graph import END, START
from langgraph.prebuilt import tools_condition





def create_fallback_subgraph(config: Optional[Dict] = None):
    
    builder = SubgraphBuilder(CancelationState, name='subgraph_fallback', suffix='fallback')
    
    fallback_tools = [fallback_notification]

    get_user_input = builder.add_node(GetUserInputNode(name='get_user_input_fallback'))
    
    ask_order_number = builder.add_node(SimpleLLMNode(name="ecom_ask_order_number", system_message = HELP_WITH_ACTIVE_ORDER), config=config)
    
    fetch_order_info = builder.add_node(FunctionalNode("fetch_order_info", load_order_info_node))
    
    ask_motivation = builder.add_node(SimpleLLMNode(name="ecom_ask_motivation", system_message = FALLBACK_ASK_MOTIVATION), config=config)
    
    fallback_tools_node = builder.add_node(ToolCallingNode(name='contacts_tools_node', tools=fallback_tools))

    
    fallback_node = builder.add_node(SimpleLLMNode(name="ecom_fallback_node", system_message= FALLBACK_NODE_PROMPT))
    
    
    builder.add_edge(START, ask_order_number)
    
    builder.add_edge(ask_order_number, get_user_input)
    
    builder.add_edge(get_user_input, fetch_order_info)
    
    builder.add_edge(fetch_order_info, ask_motivation)
    
    builder.add_edge(ask_motivation, get_user_input)
    
    
    builder.add_edge(get_user_input, fallback_node)
    
    builder.graph.add_conditional_edges(
    fallback_node,
    tools_condition,
    {
        "tools": fallback_tools_node,
        END: END,
    },
    )
    
    
    builder.add_edge(fallback_tools_node, fallback_node)
    return builder.compile()

    
    
    
    
    
    
    
    
    

    


    
    
    
    