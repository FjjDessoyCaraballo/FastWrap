from fastapi import FastAPI, status
from config import settings
from app.api.routes import router
import sys
import logging

# Logging (terminal and logfile)
file_handler = logging.FileHandler('logfile.log')
console_handler = logging.StreamHandler(sys.stderr)

formatter= logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
if not logger.handlers:
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

# NEED TO COME BACK TO ADD PARAMETERS TO FASTAPI OBJECT
app = FastAPI(
    title="API-wrapper-backend",
    description="Wrapper para serviços de chatbot da VanaciPrime",
    version="1.0.0",
)

app.include_router(router)

if __name__ == "__main__":

    logger.info("Check README for instructions on how to use")

    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.HOST, 
        port=settings.PORT,
        reload=True
        )


