from fastapi import FastAPI, status
from config import settings
from contextlib import asynccontextmanager
from app.api.routes import router
from app.infrastructure.redis_client import redis_client
from app.database.init import db_creation
from pathlib import Path
import sys
import os
import logging

# Logging (terminal and logfile)
PROJECT_ROOT = Path(__file__).parent
if os.path.isdir('logs') is False:
    os.mkdir(f'{PROJECT_ROOT}/logs')

file_handler = logging.FileHandler('logs/logfile.log')
console_handler = logging.StreamHandler(sys.stderr)
formatter= logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

if not logger.handlers:
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

@asynccontextmanager
async def lifespan(app: FastAPI) -> None:
    logger.info("Initializing database...")
    await db_creation()
    logger.info("Database ready!")
    yield
    # Shut down functions later go here
    logger.info("Shutting down application...")

app = FastAPI(
    title="API-wrapper-backend",
    description="Wrapper para serviços de chatbot",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router)

if __name__ == "__main__":
    logger.info("Check README for instructions on how to use")

    PROJECT_ROOT = Path(__file__).parent

    if os.path.isdir('database') is False:
        logger.info("Database directory not found. Creation new one...")
        os.mkdir(f'{PROJECT_ROOT}/database')
    
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.HOST, 
        port=settings.PORT,
        reload=True
    )


