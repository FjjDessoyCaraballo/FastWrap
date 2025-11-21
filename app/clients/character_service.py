from ..models.schemas import RoleRequest, ServiceRoleRequest
from fastapi import HTTPException
from .CRUD import db_insertion, db_update, db_delete, db_select

async def store_character(request: RoleRequest) -> int:
    try:
        http_status = await db_insertion(request)
        return http_status
    except:
        raise

async def update_character(request: RoleRequest) -> int:
    try:
        http_status = await db_update(request)
        return http_status
    except:
        raise

async def delete_character(request: RoleRequest) -> int:
    try:
        http_status = await db_delete(request)
        return http_status
    except:
        raise

async def get_character(request: ServiceRoleRequest) -> tuple[str, int]:
    try:
        agent_role, http_status = await db_select(request)
        return agent_role, http_status
    except:
        raise