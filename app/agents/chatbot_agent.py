import logging
from ...config import settings
from langchain.agents import create_agent

logger = logging.getLogger(__name__)

agent = create_agent(
        model=settings.MODEL
        )

