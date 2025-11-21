from ..models.schemas import RoleRequest, ServiceRoleRequest, PatchRole
from fastapi import HTTPException, Path
from .CRUD import db_insertion, db_update, db_delete, db_select, db_select_all

async def store_character(request: RoleRequest) -> int:
    try:
        http_status = await db_insertion(request)
        return http_status
    except:
        raise

async def update_character(uuid: str, request: PatchRole) -> int:
    try:
        http_status = await db_update(uuid, request)
        return http_status
    except:
        raise

async def delete_character(uuid: str) -> int:
    try:
        http_status = await db_delete(uuid)
        return http_status
    except:
        raise

async def get_character(uuid: str) -> tuple[str, int]:
    try:
        agent_role, http_status = await db_select(uuid)
        return agent_role, http_status
    except:
        raise

async def get_all_character() -> tuple[str, int]:
    try:
        agent_role, http_status = await db_select_all()
        return agent_role, http_status
    except:
        raise