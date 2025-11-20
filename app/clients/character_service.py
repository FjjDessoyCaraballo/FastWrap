from ..models.schemas import RoleRequest
from fastapi import HTTPException
from .CRUD import db_insertion, db_update, db_delete

async def store_character(request: RoleRequest):
    try:
        http_status = await db_insertion(request)
        return http_status
    except:
        raise

async def update_character(request: RoleRequest):
    try:
        http_status = await db_update(request)
        return http_status
    except:
        raise

async def delete_character(request: RoleRequest):
    try:
        http_status = await db_delete(request)
        return http_status
    except:
        raise