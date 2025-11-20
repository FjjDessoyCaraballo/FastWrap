from fastapi import status, APIRouter, HTTPException, Response
from ..models.schemas import RoleRequest, Completions
from ..clients.chat_service import store_message
from ..clients.character_service import store_character, update_character, delete_character
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
 
@router.post("/api/characters")
async def characters(request: RoleRequest, response: Response):
    http_status = await store_character(request)
    response.status_code = http_status
    logger.info(f"Received role creation request. Data: {request.dict()}")

    return {"message": "Character created", "data": request.dict()}

@router.delete("/api/characters")
async def characters(request: RoleRequest, response: Response):
    http_status = await delete_character(request)
    response.status_code = http_status
    logger.info(f"Received role deletion request")

    if http_status == status.HTTP_404_NOT_FOUND:
        return {"message": "Character not found"}
    return {"message": "Character deleted"}
 
@router.patch("/api/characters")
async def characters(request: RoleRequest):
    http_status = await update_character(request)
    response.status_code = http_status
    logger.info(f"Received role update request: {request.dict()}")

    return {"message": "Character updated", "data": request.dict()}

@router.post("/api/chat")
async def chat(request: Completions):
    call_status: int = await store_message(request)
    return {"Role": f"{request.role}", "Content": f"{request.content}", "Status": f"{call_status}"}

@router.get("/health")
async def health(status_code=status.HTTP_200_OK):
    return {"Health": "OK"}
