
from fastapi import APIRouter, Depends, HTTPException, status, Path, Query
from ..auth.dependencies import require_admin, verify_internal_key
from ..clients.repository import crud_management
from ..models import schemas
import logging

logger = logging.getLogger(__name__)
crud = crud_management()

admin = APIRouter(prefix="/admin", tags=["admin"])
internal = APIRouter(prefix="/internal", tags=["internal"])

@internal.post("/bootstrap-admin", status_code=status.HTTP_201_CREATED, dependencies=[Depends(verify_internal_key)])
async def bootstrap_admin(request: schemas.AuthRequest):
	"""Create the very first admin account.

	Header required:
	  - x-fastwrap-api-key: <settings.FASTWRAP_API_KEY>
	"""
	if await crud.db_any_admin_exits():
		raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Admin already exists")
	resource = await crud.db_create_admin(request.email, request.password)
	if resource is None:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create admin")
	logger.info("Bootstrap admin created")
	return {"message" : "Admin created", "data" : resource}

@admin.post("/clients", status_code=status.HTTP_201_CREATED)
async def admin_create_client(
	request: schemas.AdminClientCreateRequest,
	_admin_user=Depends(require_admin)
):
	resource = await crud.db_insert_client(
		email=str(request.email),
		password=request.password,
		is_admin=request.is_admin,
		is_active=request.is_active,
		subscription=request.subscription,
		strore_name=request.store_name,
		phone=request.phone
	)
	if resource is None:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create account")
	return {"message": "Client created", "data": resource}

@admin.get("/clients", status_code=status.HTTP_200_OK)
async def admin_list_clients(
	include_deleted: bool = Query(False, description="Include soft-deleted clients"),
	_admin_user=Depends(require_admin)
):
	rows = await crud.db_admin_list_clients(include_deleted=include_deleted)
	if rows is None:
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to list clients")
	return {"message": "Clients fetched", "data": rows}

@admin.get("/clients/{client_id}", status_code=status.HTTP_200_OK)
async def admin_get_client(
	client_id: str = Path(..., min_length=36, description="Client UUID"),
	_admin_user=Depends(require_admin)
):
	row = await crud.db_admin_get_client(client_id)
	if row is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
	return {"message": "Client fetched", "data": row}

@admin.patch("/clients/{client_id}", status_code=status.HTTP_200_OK)
async def admin_update_client(
	request: schemas.AdminClientUpdateRequest,
	client_id: str = Path(..., min_length=36, description="Client UUID"),
	_admin_user=Depends(require_admin)
):
	row = await crud.db_admin_update_client(
		client_id,
		email=str(request.email) if request.email is not None else None,
		password=request.password,
		is_admin=request.is_admin,
		is_active=request.is_active,
		subscription=request.subscription,
		strore_name=request.store_name,
		phone=request.phone
	)
	if row is None:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Update failed")
	return {"message": "Client updated", "data": row}

@admin.delete("/clients/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_client(
	client_id: str = Path(..., min_length=36, description="Client UUID"),
	_admin_user=Depends(require_admin) 
):
	if str(_admin_user["id"]) == client_id:
		raise HTTPException(status_code=status.HTTP_BAD_REQUEST, detail="Refusing to delete the currently authenticated admin")
	http_status = await crud.db_delete_client(client_id)
	if http_status is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
	return None

router = APIRouter()
router.include_router(admin)
router.include_router(internal)