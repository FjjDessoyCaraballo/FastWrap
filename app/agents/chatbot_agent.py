import logging
from .tools import check_products
from ...config import settings
from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain_chat_models import init_chat_model

logger = logging.getLogger(__name__)

# Instructions: this will come from db later
instructions = """
You are a store assistant that will help clients choose products from our store.

YOU CANNOT place products in cart without explicit authorization from the client.
"""

def detect_provider() -> BaseChatModel:
    try:
        model: BaseChatModel = init_chat_model(settings.MODEL)
        return model
    except:
        model: BaseChatModel = init_chat_model(settings.MODEL, model_provider=settings.MODEL_PROVIDER)
        return model

model = detect_provider()

agent = create_agent(
        model=model,
        system_prompt=f"{instructions}",
        tools=[check_products]
        )

