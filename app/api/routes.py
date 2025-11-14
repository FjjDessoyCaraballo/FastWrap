from fastapi import status, APIRouter, HTTPException
from ..models.schemas import RoleRequest, Completions
import logging
import sys
# NEED TO ADD TOKENIZED SECURITY LATER
 
router = APIRouter()
logger = logging.getLogger(__name__)
#logging.StreamHandler(sys.stderr)
  
@router.get("/") 
async def root(status_code=status.HTTP_200_OK): 
    logger.info("Received request at root") 
    return ({ "Title": "VanaciPrime Chatbot Wrapper",
             "Version": "1.0.0.",
             "Author": "Felipe",
             "Status": "Development"})
 
@router.post("/api/character")
async def character(request: RoleRequest):
    try:
        logger.info(f"Received role request: {request.agent_role}, TTL: {request.TTL}")
    except Exception as e:
        logger.error(f"Error in processing role request: {e}")
        raise HTTPException(status_code=500, detail=str(e))
 
@router.post("/api/chat")
async def chat(request: Completions):
    return ({f"Role: {request.role} | Content: {request.content} "})

@router.get("/health")
async def health(status_code=status.HTTP_200_OK):
    return {"Health": "OK"}
