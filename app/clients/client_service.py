from ..models import schemas
from .CRUD import crud_management
from fastapi import HTTPException

crud = crud_management()

async def register_client(request: schemas.AuthRequest) -> tuple[str, list]:
    api_key: str
    api_key, resource = await crud.db_insert_client(request.email, request.password)
    return api_key, resource

async def get_client(request: schemas.AuthRequest) -> dict:
    resource = await crud.db_select_client(request.email, request.password)
    return resource

async def delete_client(request: schemas.AuthRequest) -> int:
    http_status = await crud.db_delete_client(request.email, request.password, api_key)
    return http_status