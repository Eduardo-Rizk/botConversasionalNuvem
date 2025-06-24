from typing import Annotated

from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages
from pydantic import BaseModel


class MessagesState(BaseModel):
    messages: Annotated[list[AnyMessage], add_messages]

    def __getitem__(self, item):
        return getattr(self, item, None)