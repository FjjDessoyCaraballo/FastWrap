from fastapi import FastAPI, status
from config import settings
from contextlib import asynccontextmanager
from app.api.routes import router
from app.infrastructure.redis_client import redis_client
from app.infrastructure.middleware import RateLimitMiddleware
from app.database.init import init_db, close_db
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
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

if not logger.handlers:
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

@asynccontextmanager
async def lifespan(app: FastAPI) -> None:
    try:
        logger.info("Initializing database...")
        await init_db()
        logger.info("Database ready!")
        logger.info ("Pinging redis...")
        await redis_client.ping()
        logger.info("Redis client pinged")
    except Exception as e:
        logger.error(f"failed to initialize dependencies: {e}")
        raise
    yield
    logger.info("Shutting down application...")
    await close_db()

app = FastAPI(
    title="FastWrap",
    description="Wrapper for chatbots",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(RateLimitMiddleware)
app.include_router(router)

if __name__ == "__main__":
    logger.info("Check README for instructions on how to use this service.")

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


