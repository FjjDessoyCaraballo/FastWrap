from ..models.schemas import RoleRequest, ServiceRoleRequest, PatchRole
from fastapi import HTTPException, Path
from .CRUD import crud_management

crud = crud_management()

async def store_character(request: RoleRequest) -> int:
    try:
        http_status = await crud.db_insertion(request)
        return http_status
    except:
        raise

async def update_character(uuid: str, request: PatchRole) -> int:
    try:
        http_status = await crud.db_update(uuid, request)
        return http_status
    except:
        raise

async def delete_character(uuid: str) -> int:
    try:
        http_status = await crud.db_delete(uuid)
        return http_status
    except:
        raise

async def get_character(uuid: str) -> tuple[str, int]:
    try:
        agent_role, http_status = await crud.db_select(uuid)
        return agent_role, http_status
    except:
        raise

async def get_all_character() -> tuple[str, int]:
    try:
        agent_role, http_status = await crud.db_select_all()
        return agent_role, http_status
    except:
        raise
