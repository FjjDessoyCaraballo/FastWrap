from fastapi import FastAPI, status
import logging
from .config import settings

logger = logging.getLogger(__name__)
logging.basicConfig(filename='logfile.log', level=logging.INFO)

logger.INFO(f"VanaciPrime key: {settings.vanaciprime_api_key})


# NEED TO COME BACK TO ADD PARAMETERS TO FASTAPI OBJECT
app = FastAPI(
    title="API-wrapper-backend",
    description="Wrapper para serviços de chatbot da VanaciPrime",
    version="1.0.0",
)

app.include_router(router)

if __name__ == "__main__":

    logger.INFO("Check README for instructions on how to use")

    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        )


