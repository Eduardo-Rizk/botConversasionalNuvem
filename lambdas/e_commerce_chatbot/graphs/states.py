from lambdas.e_commerce_chatbot.generics.states import MessagesState


from typing import Literal, Optional

Routes  = Literal["generic", "cancelation", "order_status"]

class GraphState(MessagesState):
    route: Routes
    order_id : Optional[str] = None
