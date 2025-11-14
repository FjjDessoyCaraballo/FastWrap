from fastapi import status, APIRouter, HTTPException
from ..models.schemas import RoleRequest, Completions
import logging
# NEED TO ADD TOKENIZED SECURITY LATER

router = APIRouter()
logger = logging.getLogger(__name__)

@app.get("/")
async def root(status_code=status.HTTP_200_OK):
    logger.info("Received request at root")
    return ({ "Title": "VanaciPrime Chatbot Wrapper",
             "Version": "1.0.0.",
             "Author": "Felipe",
             "Status": "Development"})

@app.post("/role")
async def role(request: RoleRequest):
    try:
        logger.info(f"Received role request: {request.agent_role}, TTL: {request.TTL}")
    except Exception as e:
        logger.error(f"Error in processing role request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat(request: Completions):
    return ({f"Role: {request.role} | Content: {request.content} "})

