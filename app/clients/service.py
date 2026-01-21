from ..models import schemas
from .repository import crud_management
from fastapi import HTTPException
import logging
 
logger = logging.getLogger(__name__)
crud = crud_management()

async def register_client(request: schemas.AuthRequest) -> dict:
    """
    """
    resource = await crud.db_insert_client(request.email, request.password)

    return resource

# DEPRECATED
# async def get_client(request: schemas.AuthRequest) -> dict:
#     resource: dict = await crud.db_select_client_by_key(request.email, request.password)
#     return resource

async def update_client(client_id: str, request: schemas.UpdateRequest) -> dict:
    """
    """
    if request.email is None and request.password is None:
        logger.error("Password and email cannot be both empty")
        return None, 404
    elif request.email is not None and request.password is not None:
        logger.error("Can only change email or password, not both at the same time")
        return None, 422

    resource = await crud.db_update_client(client_id, request.email, request.password)

    return resource, 201

async def delete_client(client_id: str) -> int:
    """
    """
    http_status: int = await crud.db_delete_client(client_id)

    return http_status

async def regenerate_key(client_id: str) -> str:
    """
    """
    new_key: str = await crud.db_regenerate_key(client_id)

    return new_key
