import aiosqlite
import logging
from pathlib import Path
from ..models.schemas import RoleRequest

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.parent
DB_PATH = PROJECT_ROOT / "characters.db"

async def db_insertion(request: RoleRequest):
    logger.info(f"Inserting new character for ID {request.uuid}")
    logger.info(f"Role: {request.agent_role}")
    try:
        async with aiosqlite.connect(DB_PATH) as conn:
            if request.TTL is None:
                await conn.execute(f"""INSERT INTO characters ( uuid, agent_role ) 
                VALUES (?, ?)
                """, (request.uuid, request.agent_role))
            else:
                await conn.execute(f"""INSERT INTO characters ( uuid, agent_role, TTL ) 
                VALUES ( ?, ?, ? )
                """, (request.uuid, request.agent_role, request.TTL))
            await conn.commit()
            logger.info(f"Successfully created ID {request.uuid} with new role {request.agent_role}")
    except aiosqlite.DatabaseError as e:
        logger.error(f"Database error: {e}")
        raise

async def db_update(request: RoleRequest):
    logger.info(f"Updating role for ID: {request.uuid}")
    logger.info(f"New role: {request.agent_role}")
    try:
        async with aiosqlite.connect(DB_PATH) as conn:
            if request.TTL is None:
                await conn.execute("UPDATE OR ABORT characters SET agent_role = ? WHERE uuid = ?", 
                (request.agent_role, request.uuid))
            else:
                await conn.execute("UPDATE OR ABORT characters SET agent_role = ?, TTL = ? WHERE uuid = ?", 
                (request.agent_role, request.TTL, request.uuid))
            await conn.commit()
            logger.info(f"Successfully update ID {request.uuid} with new role {request.agent_role}")
    except aiosqlite.DatabaseError as e:
        logger.error(f"Database error: {e}")
        raise

async def db_delete(request: RoleRequest):
    logger.info(f"Deleting role for ID: {request.uuid}")
    logger.info(f"New role: {request.agent_role}")
    try:
        async with aiosqlite.connect(DB_PATH) as conn:
            await conn.execute("DELETE FROM characters WHERE uuid = ?", 
            (request.uuid))
            await conn.commit()
            logger.info(f"Successfully deleted ID {request.uuid}")
    except aiosqlite.DatabaseError as e:
        logger.error(f"Database error: {e}")
        raise

# async def db_select(request: RoleRequest):
#     logger.info(f"Updating role for ID: {request.uuid}")
#     logger.info(f"New role: {request.agent_role}")
#     try:
#         async with aiosqlite.connect(DB_PATH) as conn:
#             if request.TTL is None:
#                 await conn.execute("UPDATE OR ABORT characters SET agent_role = ? WHERE uuid == ?", 
#                 (request.agent_role, request.uuid))
#             else:
#                 await conn.execute("UPDATE OR ABORT characters SET agent_role = ?, TTL = ? WHERE uuid == ?", 
#                 (request.agent_role, request.TTL, request.uuid))
#             await conn.commit()
#             logger.info(f"Successfully update ID {request.uuid} with new role {request.agent_role}")
#     except aiosqlite.DatabaseError as e:
#         logger.error(f"Database error: {e}")
#         raise