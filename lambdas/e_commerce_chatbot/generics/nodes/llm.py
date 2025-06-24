from typing import Any, Dict
from langchain_core.messages import AIMessage

from lambdas.e_commerce_chatbot.generics.nodes.base import LLMNode


class SimpleLLMNode(LLMNode):
    def process(self, state: Any, config: Dict) -> Dict:
        messages = self._get_messages(state)
        tool_list_response = self._handle_list_tool_message(messages)
        if tool_list_response:
            return tool_list_response

        try:
            llm_instance = self.llm

            if self.tools:
                llm_instance = self.llm.bind_tools(
                    tools=self.tools,
                    tool_choice=self.tool_choice
                )

            result = llm_instance.invoke(messages, config)

            return {
                'messages': [AIMessage(content=result.content, tool_calls=result.tool_calls)]
            }
        except Exception as e:
            print(f'Erro ao gerar resposta: {e}')
            return {}


class StructuredOutputLLMNode(LLMNode):
    def process(self, state: Any, config: Dict) -> Dict:
        messages = self._get_messages(state)
        tool_list_response = self._handle_list_tool_message(messages)
        if tool_list_response:
            return tool_list_response

        try:
            llm_instance = self.llm.with_structured_output(
                self.output_model, 
                method='function_calling'
            )
            result = llm_instance.invoke(messages, config)
            return result.model_dump()
        except Exception as e:
            print(f'Erro ao gerar resposta estruturada: {e}')
            return {}


class StateUpdateLLMNode(LLMNode):
    """
    Node specifically for updating state without modifying messages
    This is different from just using the state update function
    Here it's the agent who does it
    """

    def __init__(self, state_field: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.state_field = state_field

    def process(self, state: Any, config: Dict) -> Dict:
        messages = self._get_messages(state)
        tool_list_response = self._handle_list_tool_message(messages)
        if tool_list_response:
            return tool_list_response

        try:
            result = self.llm.invoke(messages, config)

            return {self.state_field: result.content}
        except Exception as e:
            print(f'Erro ao atualizar estado: {e}')
            return {}


class StateUpdateStructureOutputLLMNode(LLMNode):
    """
    Node specifically for updating state without modifying messages
    This is different from just using the state update function
    Here it's the agent who does it
    """
    
    def __init__(self, state_field: str, attribute: str,*args, **kwargs):
        super().__init__(*args, **kwargs)
        self.state_field = state_field
        self.attribute = attribute

    def process(self, state: Any, config: Dict) -> Dict:
        messages = self._get_messages(state)
        tool_list_response = self._handle_list_tool_message(messages)
        if tool_list_response:
            return tool_list_response
        try: 
            llm_instance = self.llm.with_structured_output(
                self.output_model,
                method='function_calling'
            )
            result = llm_instance.invoke(messages, config)
            result_parsed = result.model_dump()
            return{self.state_field: result_parsed[self.attribute]}
        except Exception as e:
            print(f"Erro ao atualizar o state ao gerar a resposta estruturada:{e}")
        
            
    
    