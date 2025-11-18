from ..models.schemas import RoleRequest
from fastapi import HTTPException
from .db_character import db_insertion

async def store_character(request: RoleRequest):
    try:
        await db_insertion(request)
    except:
        raise

# async def retrieve_character(request: RoleRequest):
#     return
