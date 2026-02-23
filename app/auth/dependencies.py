from fastapi import Header, HTTPException, status, Depends
from ..clients.repository import crud_management
# import bcrypt
from config import settings
import logging

logger = logging.getLogger(__name__)
crud = crud_management()

async def verify_api_key(x_api_key: str = Header(...)) -> dict:
    """
    Dependency that verifies API key from header.
    Returns user data if valid, raises 401 if not.
    """

    resource =  await crud.db_select_client_by_key(x_api_key)
    if resource is None:
        logger.error("Failure in API key authentication. No matching API key.")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    return resource

async def require_admin(user: dict = Depends(verify_api_key)) -> dict:
    """
    Dependency that enforces admin-only access.
    user dict: (id, email, api_key, is_admin)
    """
    if not bool(user.get("is_admin", False)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    return user

async def verify_internal_key(
    x_fastwrap_api_key: str = Header(..., alias="x-fastwrap-api-key")
) -> None:
    """
    Dependency for internal-only endpoints (bootstrapping).
    Uses settings.FASTWRAP_API_KEY.
    """
    if x_fastwrap_api_key != settings.FASTWRAP_API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid internal key")