from fastapi import status, Path, APIRouter, Response, Header, HTTPException, Depends
from ..models import schemas
from ..chat.service import store_message
from ..clients import service as client_service
from ..characters import service as character_service
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
        "Title": "FastWrap Chatbot wrapper",
        "Version": "1.0.0.",
        "Author": "Felipe",
        "Status": "Development"
        })
 
@router.post("/api/characters", status_code=status.HTTP_201_CREATED)
async def create_characters(
    request: schemas.ServiceRole,
    user = Depends(verify_api_key) 
    ):
    """
    Endpoint responsible to for storage of characters in the database. Characters 
    are an agent configuration system doing dynamic system prompt injection. In simpler
    words it gives a characteristic, a personality, to the chatbot, and because of that
    they should be essential instructions.

    Parameters
    ----------
    request : RoleRequest
        Object defined and validated by pydantic class BaseModel in `/app/models/schemas.py`.
        Mandatorily, it requires an `uuid` and `agent_role`, with the optional setting of a TTL
        (Time To Live).
    user : dict
        Object that resulting from middleware verification of API key. If the API key is
        verified, we return the data to the user to be accessed in doing CRUD (Create, Read,
        Update, and Delete) operations.

    Returns
    -------
    resource : dict
        Created object that mirrors the data inserted into the database.
    """
    
    store_id: str = user[0]

    resource: dict = await character_service.store_character(request, store_id)

    if resource is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Character not found"
            )
    logger.info("Received role creation request.")

    return {
        "message": "Character created",
        "data": resource
        }

@router.delete("/api/characters/{uuid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_characters(
    user = Depends(verify_api_key),
    uuid: str = Path(min_length=36, description="Character UUID")
    ):
    """
    Endpoint for deletion of characters. Characters are an agent configuration system 
    doing dynamic system prompt injection. In simpler words it gives a characteristic, 
    a personality, to the chatbot, and because of that they should be essential instructions.
    
    Parameters:
    -----------
    user : dict
        Object that resulting from middleware verification of API key. If the API key is
        verified, we return the data to the user to be accessed in doing CRUD (Create, Read,
        Update, and Delete) operations.

    uuid : str
        String containing unique user ID given during creation of character.

    Returns:
    --------
    None
    """
    store_id: str = user[0]

    http_status: int = await character_service.delete_character(uuid, store_id)
    logger.info(f"Received role deletion request")

    if http_status == status.HTTP_404_NOT_FOUND:
        raise HTTPException(status_code=404, detail="Resource not found")
 
@router.patch("/api/characters/{uuid}", status_code=status.HTTP_201_CREATED)
async def update_characters(
    request: schemas.ServiceRole,
    uuid: str = Path(min_length=36, description="Character UUID"),
    user = Depends(verify_api_key)
    ):
    """
    Endpoint for patching pre-existing characters. Characters are an agent configuration 
    system doing dynamic system prompt injection. In simpler words it gives a characteristic,
    a personality, to the chatbot, and because of that they should be essential instructions.
    
    Parameters:
    -----------
    request : ServiceRole
        Object defined by schema ServiceRole that should contain the `agent_role` and,
        optionally, a TTL in seconds.
    
    uuid : str
        String containing unique user ID given during creation of character.    

    user : dict
        Object that resulting from middleware verification of API key. If the API key is
        verified, we return the data to the user to be accessed in doing CRUD (Create, Read,
        Update, and Delete) operations.

    Returns:
    --------
    resource : dict
        Created object that mirrors the data inserted into the database.
    """

    store_id: str = user[0]
    
    resource: dict = await character_service.update_character(uuid, request, store_id)
    logger.info(f"Received role update request")
    
    return {
        "message": "Resource updated",
        "data": resource
        }

@router.get("/api/characters/{uuid}", status_code=status.HTTP_200_OK)
async def get_characters(
    uuid: str = Path(min_length=36, description="Character UUID"),
    user = Depends(verify_api_key)
    ):
    """
    Getter endpoint for a single character object under specific API key. Characters are an 
    agent configuration system doing dynamic system prompt injection. In simpler words it
    gives a characteristic, a personality, to the chatbot, and because of that they should 
    be essential instructions.

    Parameters:
    -----------
    uuid : str
        String containing unique user ID given during creation of character.

    user : dict
        Object that resulting from middleware verification of API key. If the API key is
        verified, we return the data to the user to be accessed in doing CRUD (Create, Read,
        Update, and Delete) operations.
    
    Returns:
    --------
    agent_role : str
        String containing requested role from uuid.
    """

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
async def get_all_characters(user = Depends(verify_api_key)):
    """
    Getter endpoint for all characters objects under specific API key. Characters are an agent
    configuration system doing dynamic system prompt injection. In simpler words it gives a 
    characteristic, a personality, to the chatbot, and because of that they should be essential 
    instructions.

    Parameters:
    -----------
    user : dict
        Object that resulting from middleware verification of API key. If the API key is
        verified, we return the data to the user to be accessed in doing CRUD (Create, Read,
        Update, and Delete) operations.

    Returns:
    --------
    agent_roles : str
        Dictionary containing all roles from specific store_id.

    """
    agent_roles: dict = await character_service.get_all_character(user[0])
    
    if agent_roles is None:
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

    Parameters:
    -----------
    request : Completions
        Object that contains UUID, user, and content.
    
    user : dict
        Object that resulting from middleware verification of API key. If the API key is
        verified, we return the data to the user to be accessed in doing CRUD (Create, Read,
        Update, and Delete) operations.

    Returns:
    --------
    prompt : dict[str, Any]
        OpenAI Completions JSON formatted object. If you are unfamiliar with such concept, you
        can check the documentation of this object at https://platform.openai.com/docs/api-reference/completions
    """
    
    store_id: str = user[0]
    prompt: dict[str, Any] = await store_message(request, store_id)

    if prompt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not set/found")

    return {
        "message": "Chat request posted",
        "data": prompt
        }

@router.get("/health", status_code=status.HTTP_200_OK)
async def health():
    return {"Health": "OK"}

@router.post("/auth/signup", status_code=status.HTTP_201_CREATED)
async def signup(request: schemas.AuthRequest):
    """
    Signup endpoint for direct users. This endpoint is the entrypoint for usage of all
    other service endpoints. 
    """

    resource: dict = await client_service.register_client(request)

    if resource is None:
        raise HTTPException(status_code=400, detail="Failed to create account")
    return {
        "message": "Signup request received",
        "data": resource
        }

# DEPRECATED
# @router.get("/api/clients/me", status_code=status.HTTP_200_OK)
# async def get_clients(user = Depends(verify_api_key)):
#     """
    
#     Parameters:
#     -----------
#     user : dict
#         Object that resulting from middleware verification of API key. If the API key is
#         verified, we return the data to the user to be accessed in doing CRUD (Create, Read,
#         Update, and Delete) operations.
#     """

#     logger.info(f"Received role fetch request")
    
#     return {
#         "message": "Character fetched",
#         "data": user
#         }

@router.patch("/clients/me", status_code=status.HTTP_201_CREATED)
async def update_clients(
    request: schemas.UpdateRequest,
    user = Depends(verify_api_key)
    ):
    """
    """
    store_id: str = user[0]
    
    resource, http_status = await client_service.update_client(store_id, request)

    if resource is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
        detail="No maching credentials")
    elif http_status == 422:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail="Malformed JSON")
    
    return {
        "message": "Resource updated",
        "data": resource
    }

@router.post("/clients/me/regenerate-key", status_code=status.HTTP_201_CREATED)
async def update_client_key(user = Depends(verify_api_key)):
    
    store_id: str = user[0]

    new_key: str = await client_service.regenerate_key(store_id)

    if new_key is None:
        logger.error("Failed to recreate key for client")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")

    return {
        "message": "New key generated",
        "API key": new_key
        }

@router.delete("/clients/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_clients(user = Depends(verify_api_key)):
    """
    Parameters:
    -----------
    
    user : dict
        Object that resulting from middleware verification of API key. If the API key is
        verified, we return the data to the user to be accessed in doing CRUD (Create, Read,
        Update, and Delete) operations.
    """
    store_id = user[0]

    http_status: int = await client_service.delete_client(store_id)
    
    if http_status is None:
        logger.error("Could not delete clients account")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    