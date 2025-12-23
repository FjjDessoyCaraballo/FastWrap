from ..models import schemas
from .repository import crud_management
from fastapi import HTTPException

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

async def update_client(store_id: str, request: schemas.UpdateRequest) -> dict:
    """
    """
    if request.email is None and request.password is None:
        return None, 404
    elif request.email is not None and request.password is not None:
        return None, 422

    resource = await crud.db_update_client(store_id, request.email, request.password)

    return resource, 201

async def delete_client(store_id: str) -> int:
    """
    """
    http_status: int = await crud.db_delete_client(request.email, request.password, api_key)

    return http_status

async def regenerate_key(store_id: str) -> str:
    """
    """

    new_key: str = crud.db_regenerate_key(store_id)

    return new_key
