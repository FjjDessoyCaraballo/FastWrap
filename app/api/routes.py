from fastapi import status, Path, APIRouter, Header, HTTPException, Depends
from .admin_routes import router as admin_router
from ..models import schemas
from ..database.init import init_db
from ..chat.service import store_message
from ..clients import service as client_service
from ..characters import service as character_service
from ..auth.dependencies import verify_api_key, require_admin, verify_internal_key
from ..clients.repository import crud_management
from ..vectors import service as vector_service
from typing import Any
from uuid import UUID
import sys
import logging
 
logger = logging.getLogger(__name__)
router = APIRouter()
crud = crud_management()

@router.get("/", status_code=status.HTTP_200_OK) 
async def root(): 
    
    logger.info("Received request at root") 
    
    return ({ 
        "Title": "FastWrap Chatbot wrapper",
        "Version": "1.0.0.",
        "Author": "Felipe Dessoy Caraballo && Nikolai Zharkevich",
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
    request : ServiceRole
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
    
    store_id: str = str(user["id"])

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
    store_id: str = str(user["id"])

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

    store_id: str = str(user["id"])
    
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

    agent_role = await character_service.get_character(uuid, str(user["id"]))

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
    agent_roles : dict
        Dictionary containing all roles from specific store_id.

    """
    agent_roles: dict = await character_service.get_all_character(str(user["id"]))
    
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
    
    store_id: str = str(user["id"])
    prompt: dict[str, Any] = await store_message(request, store_id)

    if prompt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not set/found")

    return {
        "message": "Chat request posted",
        "data": prompt
        }

@router.get("/health", status_code=status.HTTP_200_OK)
async def health():
    services = {}

    try:
        await redis_client.ping()
        services["redis"] = "OK"
    except Exception as e:
        services["redis"] = f"DOWN: {e}"
    try:
        pool = await init_db()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""SELECT 1""")
        services["postgres"] = "OK"
    except Exception as e:
        services["postgres"] = f"DOWN: {e}"

    if any(v.startswith("DOWN") for v in services.values()):
        return JSONResponse(status_code=503, content=services)
    return services

@router.post("/auth/signup", status_code=status.HTTP_201_CREATED)
async def signup(request: schemas.AuthRequest):
    """
    Signup endpoint for direct users. This endpoint is the entrypoint for usage of all
    other service endpoints. 
    
    Parameters:
    -----------
    request : AuthRequest
        Object that follows AuthRequest schema.

    Returns:
    --------
    resource : dict
        JSON containing data and metadata after registration is complete.
    """

    resource: dict = await client_service.register_client(request)

    if resource is None:
        raise HTTPException(status_code=400, detail="Failed to create account")
    return {
        "message": "Signup request received",
        "data": resource
        }

# @router.post("/internal/bootstrap-admin", status_code=status.HTTTP_201_CREATED)
# async def bootstrap_admin(
#     request: schemas.AuthRequest,
#     _ = Depends[verify_internal_key]
# ):
#     if await crud.db_any_admin_exits():
#         raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Admin already exists")
#     resource = await crud.db_create_admin(request.email, request.password)
#     if resource is None:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create admin")
#     return {"message": "Admin created", "data": resource}

# @router.post("/admin/clients", status_code=status.HTTP_201_CREATED)
# async def admin_create_client(
#     request: schemas.AdminClientCreateRequest,
#     _admin = Depends(require_admin)
# ):
#     resource = await crud.db_insert_client(
#         str(request.email),
#         request.password,
#         is_admin=request.is_admin,
#         is_active=request.is_active,
#         subscription=request.subscription,
#         strore_name=request.store_name
#         phone=request.phone
#     )
#     if resource is None:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create account")
#     return {"message": "Client created", "data": resource}

# @router.get("/admin/clients", status_code=status.HTTP_200_OK)
# async def admin_list_clients(
#     include_deleted: bool = False,
#     _admin = Depends(require_admin)
# ):
#     rows = await crud.db_admin_list_clients(include_deleted=include_deleted)
#     if rows is None:
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_ERROR, detail="Failed to list clients")
#     return {"message": "Clients fetched", "data": rows}

# @router.get("/admin/clients/{client_id}", status_code=status.HTTP_200_OK)
# async def admin_get_client(
#     client_id: str = Path(min_length=36, description="Client UUID"),
#     _admin = Depends(require_admin)
# ):
#     row = await crud.db_admin_get_client(client_id)
#     if row is None:
#         HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
#     return {"message": "Client fetched", "data": row}

# @router.patch("/admin/clients/{client_id}", status_code=status.HTTP_200_OK)
# async def admin_update_client(
#     request: schemas.AdminClientUpdateRequest,
#     client_id: str = Path(detail="Client not found"),
#     _admin = Depends(require_admin)
# ):
#     row = await crud.db_admin_update_client(
#         client_id,
#         email=str(request.email) if request.email is not None else None,
#         password=request.password,
#         is_admin=request.is_admin,
#         is_active=request.is_active,
#         subscription=request.subscription,
#         strore_name=request.store_name,
#         phone=request.phone
#     )
#     if row is None:
#         HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Update failed")
#     return {"message": "Client updated", "data": row}

# @router.delete("/clients/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
# async def admin_delete_client(
# 	client_id: str = Path(min_length=36, description="Client UUID"),
# 	admin=Depends(require_admin) 
# ):
# 	if str(admin[0]) == client_id:
# 		raise HTTPException(status_code=status.HTTP_BAD_REQUEST, detail="Refusing to delete the currently authenticated admin")
# 	http_status = await crud.db_delete_client(client_id)
# 	if http_status is None:
# 		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
# 	return None


@router.patch("/clients/me", status_code=status.HTTP_201_CREATED)
async def update_clients(
    request: schemas.UpdateRequest,
    user = Depends(require_admin)
    ):
    """
    Parameters:
    -----------
    
    user : dict
        Object that resulting from middleware verification of API key. If the API key is
        verified, we return the data to the user to be accessed in doing CRUD (Create, Read,
        Update, and Delete) operations.

    Returns:
    --------
    resource : dict
        JSON containing data and metadata after registration is complete.
    """
    store_id: str = str(user["id"])
    
    resource, http_status = await client_service.update_client(store_id, request)

    if resource is None:
        logger.error("No match for credentials provided in database")
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
    """
    Parameters:
    -----------
    user : dict
        Object that resulting from middleware verification of API key. If the API key is
        verified, we return the data to the user to be accessed in doing CRUD (Create, Read,
        Update, and Delete) operations.
    """    
    store_id: str = str(user["id"])

    new_key: str = await client_service.regenerate_key(store_id)

    if new_key is None:
        logger.error("Failed to recreate key for client")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")

    return {
        "message": "New key generated",
        "api_key": new_key
        }

@router.delete("/clients/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_clients(user = Depends(require_admin)):
    """
    Parameters:
    -----------
    user : dict
        Object that resulting from middleware verification of API key. If the API key is
        verified, we return the data to the user to be accessed in doing CRUD (Create, Read,
        Update, and Delete) operations.
    """
    client_id = str(user["id"])

    http_status: int = await client_service.delete_client(client_id)
    
    if http_status is None:
        logger.error("Could not delete clients account")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    
@router.post("/api/vectors/upsert", status_code=status.HTTP_201_CREATED)
async def vectors_upsert(
    request: schemas.VectorUpsertRequest, 
    user = Depends(verify_api_key)
    ):
    """
    Parameters:
    -----------
    user : dict
        Object that resulting from middleware verification of API key. If the API key is
        verified, we return the data to the user to be accessed in doing CRUD (Create, Read,
        Update, and Delete) operations.
    """    
    store_id = str(str(user["id"]))
    row = await vector_service.upsert_text_snippet(client_id=store_id, entity_type=request.entity_type,
                        entity_id=request.entity_id, content=request.content,metadata=request.metadata)
    if row is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Failed to upsert vector')

    return {
        "message": "Vector upserted",
        "data": row
        }

@router.post("/api/vectors/search", status_code=status.HTTP_200_OK)
async def vectors_search(
    request: schemas.VectorSearchRequest, 
    user = Depends(verify_api_key)
    ):
    """
    Parameters:
    -----------
    user : dict
        Object that resulting from middleware verification of API key. If the API key is
        verified, we return the data to the user to be accessed in doing CRUD (Create, Read,
        Update, and Delete) operations.
    """
    store_id = str(str(user["id"]))
    rows = await vector_service.semantic_search(client_id=store_id, query=request.query,
                                    top_k=request.top_k, entity_type=request.entity_type)
    return {
        "message": "Search results",
        "data": rows
        }

router.include_router(admin_router)