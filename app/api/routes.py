from fastapi import status, Path, APIRouter, Response, Header
from ..models import schemas
from ..clients.chat_service import store_message
from ..auth import client_service as auth
from ..clients import character_service
from typing import Any
from uuid import UUID
import logging
import sys
 
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
async def characters(request: schemas.RoleRequest, response: Response):
    
    http_status: int = await character_service.store_character(request)
    response.status_code = http_status
    logger.info(f"Received role creation request. Data: {request.dict()}")

    return {
        "message": "Character created",
        "data": request.dict()
        }

@router.delete("/api/characters/{uuid}")
async def characters(
    request: schemas.RoleRequest,
    response: Response,
    uuid: str = Path(min_length=36, description="Character UUID")
    ):
    http_status: int = await character_service.delete_character(uuid)
    response.status_code = http_status
    logger.info(f"Received role deletion request")

    if http_status == status.HTTP_404_NOT_FOUND:
        return {"message": "Resource not found"}
    return {}
 
@router.patch("/api/characters/{uuid}")
async def characters(
    request: schemas.PatchRole,
    response: Response,
    uuid: str = Path(min_length=36, description="Character UUID")
    ):
    
    http_status: int = await character_service.update_character(uuid, request)
    response.status_code = http_status
    logger.info(f"Received role update request: {request.dict()}")
    
    return {
        "message": "Resource updated",
        "data": request.dict()
        }

@router.get("/api/characters/{uuid}")
async def characters(
    response: Response,
    uuid: str = Path(min_length=36, description="Character UUID")
    ):
    
    http_status: int
    agent_role: str

    agent_role, http_status = await character_service.get_character(uuid)
    response.status_code = http_status
    
    if http_status == status.HTTP_404_NOT_FOUND:
        return {"message": "Resource does not exist"}
    
    logger.info(f"Received role fetch request: {agent_role}")
    
    return {
        "message": "Character fetched",
        "data": agent_role
        }

@router.get("/api/characters")
async def characters(response: Response):

    http_status: int
    agent_roles: dict

    agent_roles, http_status = await character_service.get_all_character()
    response.status_code = http_status
    
    if http_status == status.HTTP_404_NOT_FOUND:
        return {"message": "resource does not exist"}
    
    logger.info(f"Received role fetch request: {agent_roles}")
    
    return {
        "message": "Characters fetched",
        "data": agent_roles
        }

@router.post("/api/chat")
async def chat(
    response: Response, 
    request: schemas.Completions,
    x_store_id: str = Header(..., min_length=36, max_length=36)
    ):
    """
    This endpoint utilizes OpenAI API Completions pattern establishing user and content.
    The chat will be valid for a small amount of time, and after that it will be erased from memory.
    The endpoint itself needs an UUID to identify the user. If the chat is available still, the UUID
    will be used to identify the chat.

    :Parameters:
        `request: Completions` - Object that contains UUID, user, and content.
    """
    
    http_status: int 
    prompt: dict[str, Any]
    character_uuid: str = x_store_id
    logger.debug(f"header: {x_store_id}")
    http_status, prompt = await store_message(request, character_uuid)
    response.status_code = http_status

    return {
        "message": "Chat request posted",
        "data": prompt
        }

@router.get("/health")
async def health(status_code=status.HTTP_200_OK):
    return {"Health": "OK"}

@router.post("/auth/signup")
async def signup(
    response: Response,
    request: schemas.SignupRequest
):
    http_status = await auth.register_client
    return {
        "message": "Signup request received", 
        "status": http_status
        }

@router.post("/auth/login")
async def login(
    response: Response,
    request: schemas.LoginRequest
):
    return {}