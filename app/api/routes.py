from fastapi import status, Path, APIRouter, HTTPException, Response
from ..models.schemas import RoleRequest, ServiceRoleRequest, Completions, PatchRole
from ..clients.chat_service import store_message
from ..clients.character_service import store_character, update_character, delete_character, get_character, get_all_character
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
async def characters(request: RoleRequest, response: Response):
    
    http_status: int = await store_character(request)
    response.status_code = http_status
    logger.info(f"Received role creation request. Data: {request.dict()}")

    return {"message": "Character created", "data": request.dict()}

@router.delete("/api/characters/{uuid}")
async def characters(
    request: RoleRequest,
    response: Response,
    uuid: str = Path(min_length=36, description="Character UUID")
    ):
    http_status: int = await delete_character(uuid)
    response.status_code = http_status
    logger.info(f"Received role deletion request")

    if http_status == status.HTTP_404_NOT_FOUND:
        return {"message": "Resource not found"}
    return {}
 
@router.patch("/api/characters/{uuid}")
async def characters(
    request: PatchRole,
    response: Response,
    uuid: str = Path(min_length=36, description="Character UUID")
    ):
    
    http_status: int = await update_character(uuid, request)
    response.status_code = http_status
    logger.info(f"Received role update request: {request.dict()}")
    
    return {"message": "Resource updated", "data": request.dict()}

@router.get("/api/characters/{uuid}")
async def characters(
    response: Response,
    uuid: str = Path(min_length=36, description="Character UUID")
    ):
    
    http_status: int
    agent_role: str

    agent_role, http_status = await get_character(uuid)
    response.status_code = http_status
    
    if http_status == status.HTTP_404_NOT_FOUND:
        return {"message": "Resource does not exist"}
    
    logger.info(f"Received role fetch request: {agent_role}")
    
    return {"message": "Character fetched", "data": agent_role}

@router.get("/api/characters")
async def characters(response: Response):
    
    http_status: int
    agent_roles: dict

    agent_roles, http_status = await get_all_character()
    response.status_code = http_status
    
    if http_status == status.HTTP_404_NOT_FOUND:
        return {"message": "resource does not exist"}
    
    logger.info(f"Received role fetch request: {agent_roles}")
    
    return {"message": "Characters fetched", "data": agent_roles}

@router.post("/api/chat")
async def chat(request: Completions):
    
    call_status: int = await store_message(request)
    
    return {"Role": f"{request.role}", "Content": f"{request.content}", "Status": f"{call_status}"}

@router.get("/health")
async def health(status_code=status.HTTP_200_OK):
    return {"Health": "OK"}
