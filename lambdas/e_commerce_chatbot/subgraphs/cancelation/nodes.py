
from typing import Dict, Any
import json
from lambdas.e_commerce_chatbot.subgraphs.cancelation.state import CancelationState
def load_order_info_node(state: CancelationState) -> Dict[str, Any]:
    """
    Lê o arquivo JSON do pedido, converte para string
    e devolve um diff que atualiza `order_info`.
    (Não acessa o state com [] para evitar KeyError.)
    """
    data = {
        "order_id": 12345,
        "order_number": "ABC12345",
        "purchase_date": "2025-03-14T10:32:00Z",
        "customer_name": "João da Silva",
        "email": "joao.silva@example.com",
        "items": [
            {
                "product_name": "Camiseta Básica",
                "quantity": 2,
                "unit_price": 49.99
            },
            {
                "product_name": "Boné Preto",
                "quantity": 1,
                "unit_price": 29.90
            }
        ],
        "billing_address": {
            "street": "Rua das Flores",
            "number": "123",
            "complement": "Apto 201",
            "district": "Centro",
            "city": "São Paulo",
            "state": "SP",
            "zip_code": "01010-000"
        },
        "shipping_address": {
            "street": "Av. Brasil",
            "number": "999",
            "complement": "Casa 2",
            "district": "Jardim América",
            "city": "São Paulo",
            "state": "SP",
            "zip_code": "01430-000"
        },
        "total_amount": 129.88,
        "payment_method": "credit_card",
        "tracking_code": "BR123456789XYZ",
        "shipping_status": "Em trânsito",
        "estimated_delivery_date": "2025-03-20T18:00:00Z",
        "notes": "Cliente solicitou entrega no período da tarde."
    }

    info_pedido = json.dumps(data)

    

    return {"order_info": info_pedido}