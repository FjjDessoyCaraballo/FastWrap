from ..models import schemas
from ..clients.CRUD import crud_management
from fastapi import HTTPException

crud = crud_management()

async def register_client(request: schemas.SignupRequest) -> int:
    http_status: int
    api_key: str
    api_key, http_status = await crud.db_insert_client(request.email, request.password)
    return api_key, http_status

# async def login_client(request: schemas.LoginRequest, api_key: str) -> int:
#     http_status: int = await crud.db_select_client(request.email, request.password)
#     return http_status