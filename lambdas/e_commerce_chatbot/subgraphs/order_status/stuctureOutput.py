from pydantic import BaseModel, Field


class GetsOrderNumber(BaseModel):
    '''
    Class thats gets the order number and saves
    '''
    
    order_id: str = Field(description = "Esse é o id fornecido pelo cliente que se refere ao id do pedido que o própio cliente informou"
                              "O id do pedido é formado por letras e números")