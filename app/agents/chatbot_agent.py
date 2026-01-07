import logging
from ..characters.repository import crud_management
# from .tools import check_products
from config import settings
from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain.chat_models import init_chat_model
from typing import Any
from langsmith import Client
 
client = Client()
logger = logging.getLogger(__name__)
instructions = "you are a helpful assistant"

class ChatBot():
    def __init__(self):
        model = self._detect_provider() # probably will change to let store choose
        self.agent = create_agent(
                model=model,
                system_prompt=f"{instructions}",
                # tools=[check_products]
                )

    async def chat(self, parsed_messages: list[dict[str, str]]) -> dict[str, Any]:
        try:
            response = self.agent.invoke({"messages": parsed_messages})
        except Exception as e:
            logger.error(f"Unexpected error at chat method: {e}")
        return response

    async def context(self, messages: list[dict[str, str]], uuid: str, store_id: str) -> list[dict[str, str]]:
        try:
            crud = crud_management()
            context = await crud.db_select_character(uuid, store_id)
            return context
        except Exception as e:
            logger.error(f"Caught unexpected error at context: {e}")
            raise

    def _detect_provider(self) -> BaseChatModel:
        try:
            model: BaseChatModel = init_chat_model(
                settings.MODEL,
                api_key=settings.MODEL_KEY
                )
            return model
        except:
            model: BaseChatModel = init_chat_model(
                settings.MODEL, 
                model_provider=settings.MODEL_PROVIDER,
                api_key=settings.MODEL_KEY
                )
            return model



