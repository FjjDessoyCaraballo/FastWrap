import logging
# from .tools import check_products
from config import settings
from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain.chat_models import init_chat_model
from typing import Any

logger = logging.getLogger(__name__)

instructions = "you are a helpful assistant"

class ChatBot():
    def __init__(self):
        model = self._detect_provider()
        self.agent = create_agent(
                model=model,
                system_prompt=f"{instructions}",
                # tools=[check_products]
                )

    def chat(self, parsed_messages: list[dict[str, str]]) -> dict[str, Any]:
        response = self.agent.invoke({"messages": parsed_messages})
        return response

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



