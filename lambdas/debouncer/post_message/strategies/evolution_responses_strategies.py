from abc import ABC, abstractmethod
from typing import Optional, Dict


class ResponseStrategy(ABC):
    @abstractmethod
    def process(self, content: Dict) -> Optional[str]:
        pass


class ListResponseStrategy(ResponseStrategy):
    def process(self, content: Dict) -> Optional[str]:
        try:
            list_response = content.get("listResponseMessage", {})
            selected_row_id = list_response.get("singleSelectReply", {}).get("selectedRowId")

            return f"Opção selecionada pelo user: {selected_row_id}"
        except Exception as e:
            print(f"Erro ao processar resposta de lista: {e}")
            return None
