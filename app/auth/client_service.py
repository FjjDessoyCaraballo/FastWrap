from ..models import schemas
from ..clients.CRUD import crud_management
from fastapi import HTTPException
import bcrypt

crud = crud_management()

async def register_client(request: schemas.SignupRequest) -> int:
    http_status = await crud.db_insert_client(request.email, request.password)
    return http_status

async def login_client(request: schemas.LoginRequest) -> int:
    http_status = await crud.db_select_client(request.email, request.password)
    return http_status