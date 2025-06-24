import json
from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from firecrawl import FirecrawlApp, JsonConfig  # ← Versão síncrona
from dotenv import load_dotenv
import os

class ProdutoSchema(BaseModel):
    name: str                                
    description: Optional[str] = None        
    category: Optional[str] = None          
    price: Optional[float] = Field(None, ge=0)
    color: Optional[List[str]] = None
    in_stock: Optional[bool] = None          

load_dotenv()

json_config = JsonConfig(schema=ProdutoSchema)

@tool
def analyse_product_by_link(url_site: str):  # ← Removido async
    """
    Analisa um produto a partir de um link/URL de site de e-commerce.
    
    Esta ferramenta utiliza web scraping para extrair informações estruturadas
    de produtos de páginas web, incluindo nome, descrição, categoria, preço,
    cores disponíveis e status de estoque.
    
    Args:
        url_site (str): URL completa da página do produto que será analisada
        
    Returns:
        dict: Dados estruturados do produto
    """
    API_KEY_FIRECRAWLER = os.getenv('FIRECRAWL_API_KEY')
    app = FirecrawlApp(api_key=API_KEY_FIRECRAWLER)  # ← Versão síncrona

    result = app.scrape_url(  # ← Removido await
        url=url_site,
        formats=["json"],                     
        only_main_content=True,
        json_options=json_config
    )

    return result.json