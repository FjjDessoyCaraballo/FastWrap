import logging
from ...config import settings
from langchain.agents import create_agent

# Instructions: this will come from db later
instructions = """
You are a store assistant that will help clients choose products from our store.

YOU CANNOT place products in cart without explicit authorization from the client.
"""

logger = logging.getLogger(__name__)

agent = create_agent(
        model=settings.MODEL
        system_prompt=f"{instructions}"
        )

