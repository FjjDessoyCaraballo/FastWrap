from fastapi import Header, HTTPException, status
from ..clients.repository import crud_management
import bcrypt

crud = crud_management()

async def verify_api_key(x_api_key: str = Header(...)) -> dict:
    """
    Dependency that verifies API key from header.
    Returns user data if valid, raises 401 if not.
    """

    resource =  await crud.db_select_client_by_key(x_api_key)
    if resource is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    return resource

