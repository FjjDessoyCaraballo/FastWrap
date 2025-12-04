from ..models import schemas
from .CRUD import crud_management

crud = crud_management()

async def store_character(request: schemas.RoleRequest) -> int:
    try:
        character = await crud.db_insertion_character(request)
        return character
    except:
        return None

async def update_character(uuid: str, request: schemas.PatchRole) -> int:
    try:
        updated_character = await crud.db_update_character(uuid, request)
        return updated_character
    except:
        return None

async def delete_character(uuid: str) -> int:
    try:
        http_status = await crud.db_delete_character(uuid)
        return http_status
    except:
        return None

async def get_character(uuid: str) -> tuple[str, int]:
    try:
        agent_role = await crud.db_select_character(uuid)
        return agent_role
    except:
        return None

async def get_all_character() -> tuple[str, int]:
    try:
        agent_role = await crud.db_select_character_all()
        return agent_role
    except:
        return None
