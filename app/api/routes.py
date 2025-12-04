from fastapi import status, Path, APIRouter, Response, Header, HTTPException, Depends
from ..models import schemas
from ..clients.chat_service import store_message
from ..clients import client_service
from ..clients import character_service
from ..auth.dependencies import verify_api_key
from typing import Any
from uuid import UUID
import logging
import sys
 
router = APIRouter()
logger = logging.getLogger(__name__)
  
@router.get("/", status_code=status.HTTP_200_OK) 
async def root(): 
    
    logger.info("Received request at root") 
    
    return ({ 
        "Title": "VanaciPrime Chatbot Wrapper",
        "Version": "1.0.0.",
        "Author": "Felipe",
        "Status": "Development"
        })
 
@router.post("/api/characters")
async def characters(
    request: schemas.RoleRequest,
    user = Depends(verify_api_key) 
    ):
    
    resource: dict = await character_service.store_character(request)
    if resource is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")
    logger.info("Received role creation request.")

    return {
        "message": "Character created",
        "data": resource
        }

@router.delete("/api/characters/{uuid}", status_code=status.HTTP_204_NO_CONTENT)
async def characters(
    request: schemas.RoleRequest,
    user = Depends(verify_api_key),
    uuid: str = Path(min_length=36, description="Character UUID")
    ):
    http_status: int = await character_service.delete_character(uuid, user[0])
    logger.info(f"Received role deletion request")

    if http_status == status.HTTP_404_NOT_FOUND:
        raise HTTPException(status_code=404, detail="Resource not found")
 
@router.patch("/api/characters/{uuid}", status_code=status.HTTP_201_CREATED)
async def characters(
    request: schemas.PatchRole,
    uuid: str = Path(min_length=36, description="Character UUID"),
    user = Depends(verify_api_key)
    ):
    
    resource: dict = await character_service.update_character(uuid, request, user[0])
    logger.info(f"Received role update request")
    
    return {
        "message": "Resource updated",
        "data": resource
        }

@router.get("/api/characters/{uuid}", status_code=status.HTTP_200_OK)
async def characters(
    uuid: str = Path(min_length=36, description="Character UUID"),
    user = Depends(verify_api_key)
    ):

    agent_role: str

    agent_role = await character_service.get_character(uuid, user[0])

    if agent_role is None:
        raise HTTPException(status_code=404, detail="Resource not found")
    
    logger.info(f"Received role fetch request")
    
    return {
        "message": "Character fetched",
        "data": agent_role
        }

@router.get("/api/characters", status_code=status.HTTP_200_OK)
async def characters(
    user = Depends(verify_api_key)
):
    agent_roles: dict

    agent_roles = await character_service.get_all_character(user[0])
    
    if agent_role is None:
        raise HTTPException(status_code=404, detail="Resource not found")
    
    logger.info(f"Received role fetch request: {agent_roles}")
    
    return {
        "message": "Characters fetched",
        "data": agent_roles
        }

@router.post("/api/chat", status_code=status.HTTP_201_CREATED)
async def chat(
    request: schemas.Completions,
    user = Depends(verify_api_key)
    ):
    """
    This endpoint utilizes OpenAI API Completions pattern establishing user and content.
    The chat will be valid for a small amount of time, and after that it will be erased from memory.
    The endpoint itself needs an UUID to identify the user. If the chat is available still, the UUID
    will be used to identify the chat.

    :Parameters:
        `request: Completions` - Object that contains UUID, user, and content.
    """
    
    store_id: str = user[0]
    prompt: dict[str, Any] = await store_message(request, store_id)

    if prompt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detai="Character not set/found")

    return {
        "message": "Chat request posted",
        "data": prompt
        }

@router.get("/health", status_code=status.HTTP_200_OK)
async def health():
    return {"Health": "OK"}

@router.post("/auth/signup", status_code=status.HTTP_201_CREATED)
async def signup(
    request: schemas.AuthRequest
):
    api_key: str

    api_key, resource = await client_service.register_client(request)

    if api_key is None or resource is None:
        raise HTTPException(status_code=400, detail="Failed to create account")
    return {
        "message": "Signup request received",
        "api_key": api_key,
        "data": resource
        }

@router.get("/api/clients/me", status_code=status.HTTP_200_OK)
async def clients(
    request: schemas.AuthRequest,
    ):

    api_key: str = x_api_key

    resource: tuple[str, str] = await client_service.get_client(request)

    if resource is None:
        raise HTTPException(status_code=404, detail="Resource not found")
    
    logger.info(f"Received role fetch request")
    
    return {
        "message": "Character fetched",
        "data": resource
        }

@router.delete("/clients/me", status_code=status.HTTP_204_NO_CONTENT)
async def clients(
    request: schemas.AuthRequest,
):
    http_status: int = await client_service.delete_client(request, api_key)
    
    if http_status is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    
    return {
        "message": "Resource deleted"
    }