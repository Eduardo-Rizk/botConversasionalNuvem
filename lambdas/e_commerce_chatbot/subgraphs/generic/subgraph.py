from typing import Optional, Dict
from lambdas.e_commerce_chatbot.generics.subgraphs import SubgraphBuilder
from lambdas.e_commerce_chatbot.graphs.states import GraphState
from lambdas.e_commerce_chatbot.graphs.prompts import BOT_GENERIC
from lambdas.e_commerce_chatbot.generics.nodes.llm import SimpleLLMNode, StructuredOutputLLMNode, StateUpdateStructureOutputLLMNode
from lambdas.e_commerce_chatbot.generics.nodes.functional import ToolCallingNode, FunctionalNode, GetUserInputNode
from lambdas.e_commerce_chatbot.subgraphs.generic.tools import analyse_product_by_link
from langgraph.constants import START, END

from langgraph.prebuilt import tools_condition


def create_generic_subgraph(config: Optional[Dict] = None):
    
    builder = SubgraphBuilder(GraphState, name='subgraph_generic', suffix='generic')
    
    tools = [analyse_product_by_link]
    
    generic_node = builder.add_node(SimpleLLMNode(name="generic_node", tools = tools, system_message=BOT_GENERIC))

    generic_tool_call_node = builder.add_node(ToolCallingNode(name='contacts_tools_node', tools=tools))
    

    
    builder.add_edge(START, generic_node)
    
    builder.graph.add_conditional_edges(
    generic_node,
    tools_condition,
    {
        "tools": generic_tool_call_node,
        END: END,
    },
    )
    
    builder.add_edge(generic_tool_call_node, generic_node)
    return builder.compile()
