from ..models.schemas import RoleRequest
from fastapi import HTTPException
from .CRUD import db_insertion, db_update, db_delete

async def store_character(request: RoleRequest):
    try:
        await db_insertion(request)
    except:
        raise

async def update_character(request: RoleRequest):
    try:
        await db_update(request)
    except:
        raise

async def delete_character(request: RoleRequest):
    try:
        await db_delete(request)
    except:
        raise