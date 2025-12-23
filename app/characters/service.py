from ..models import schemas
from .repository import crud_management

crud = crud_management()

async def store_character(request: schemas.ServiceRole, store_id: str) -> dict | None:
    try:
        character = await crud.db_insertion_character(request, store_id)
        return character
    except:
        return None

async def update_character(uuid: str, request: schemas.ServiceRole, store_id: str) -> dict | None:
    try:
        updated_character: dict = await crud.db_update_character(uuid, request, store_id)
        return updated_character
    except:
        return None

async def delete_character(uuid: str, store_id: str) -> int | None:
    try:
        http_status = await crud.db_delete_character(uuid, store_id)
        return http_status
    except:
        return None

async def get_character(uuid: str, store_id) -> dict | None:
    try:
        agent_role = await crud.db_select_character(uuid, store_id)
        return agent_role
    except:
        return None

async def get_all_character(store_id: str) -> dict | None:
    try:
        agent_role = await crud.db_select_character_all(store_id)
        return agent_role
    except:
        return None
