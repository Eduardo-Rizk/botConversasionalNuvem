from lambdas.e_commerce_chatbot.generics.states import MessagesState

from typing import Optional, List, Dict, Union



class CancelationState(MessagesState):
    
    order_info: Optional[str] = None
    captured_motivation: Optional[str] = None