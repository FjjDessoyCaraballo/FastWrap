from fastapi import status, APIRouter, HTTPException
from ..models.schemas import RoleRequest, Completions
from ..clients.chat_cache_service import store_message
from ..clients.character_service import store_character
import logging
import sys
# NEED TO ADD TOKENIZED SECURITY LATER
 
router = APIRouter()
logger = logging.getLogger(__name__)
  
@router.get("/") 
async def root(status_code=status.HTTP_200_OK): 
    logger.info("Received request at root") 
    return ({ "Title": "VanaciPrime Chatbot Wrapper",
             "Version": "1.0.0.",
             "Author": "Felipe",
             "Status": "Development"})
 
@router.post("/api/characters", status_code=status.HTTP_201_CREATED)
async def characters(request: RoleRequest):
    await store_character(request)
    logger.info(f"Received role request: {request.agent_role}, TTL: {request.TTL}") 
    return {"message": "Character created", "data": request.dict()}
 
@router.post("/api/chat")
async def chat(request: Completions):
    call_status: int = await store_message(request)
    return ({f"Role: {request.role} | Content: {request.content} | Status: {call_status} "})

@router.get("/health")
async def health(status_code=status.HTTP_200_OK):
    return {"Health": "OK"}
