import aiosqlite
import logging
from pathlib import Path
from ..models.schemas import RoleRequest

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.parent
DB_PATH = PROJECT_ROOT / "characters.db"

table_format = """
CREATE TABLE IF NOT EXISTS characters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid TEXT UNIQUE NOT NULL,
    agent_role TEXT NOT NULL,
    TTL INTEGER
)
"""

async def db_creation() -> None:
    try:
        logger.info(f"Creating database {DB_PATH}...")
        async with aiosqlite.connect(DB_PATH) as conn:
            await conn.execute(table_format)
            await conn.commit()
        logger.info("Tables and database successfully created/updated")
    except Exception as e:
        logger.error(f"Database error: {e}")


async def db_insertion(request: RoleRequest):
    logger.info(f"Inserting new character for ID {request.agent_role}")
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
    except aiosqlite.DatabaseError as e:
        logger.error(f"Database error: {e}")
        raise aiosqlite.DatabaseError

