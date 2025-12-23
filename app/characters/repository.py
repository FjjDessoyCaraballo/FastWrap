import aiosqlite
import logging
from pathlib import Path
from ..models import schemas
from fastapi import status
import uuid

logger = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).parent.parent.parent

class crud_management():
    def __init__(self):
        self.DB_PATH = PROJECT_ROOT / "database/fastwrapper.db"

    async def db_insertion_character(self, request: schemas.ServiceRole, store_id: str) -> dict | None:
        logger.info(f"Inserting new character")
        try:
            async with aiosqlite.connect(self.DB_PATH) as conn:
                uid = str(uuid.uuid4())
                if request.TTL is None:
                    cursor = await conn.execute("""
                    INSERT INTO characters ( uuid, store_id, agent_role )
                    VALUES ( ? , ? , ? )
                    RETURNING *
                    """, (uid, store_id, request.agent_role))
                else:
                    cursor = await conn.execute("""
                    INSERT INTO characters ( uuid, store_id, agent_role, TTL )
                    VALUES ( ? , ? , ? , ? )
                    RETURNING *
                    """, (uid, store_id, request.agent_role, request.TTL))

                row = cursor.fetchone()

                if row is None:
                    logger.warning("Resource could not be created.")
                    return None

                await conn.commit()

                logger.info("Successfully created ID with new role")

                return row

        except aiosqlite.DatabaseError as e:
            logger.error(f"Database error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None

    async def db_update_character(self, uuid: str, request: schemas.ServiceRole, store_id: str) -> dict | None:
        logger.info("Updating new role")
        try:
            async with aiosqlite.connect(self.DB_PATH) as conn:

                if request.TTL is None:
                    cursor = await conn.execute('''
                    UPDATE OR ABORT characters
                    SET agent_role = ?
                    WHERE uuid = ? AND store_id = ?
                    RETURNING *
                    ''',
                    (request.agent_role, uuid, store_id))
                else:
                    cursor = await conn.execute('''
                    UPDATE OR ABORT characters
                    SET agent_role = ?, TTL = ?
                    WHERE uuid = ? AND store_id = ?
                    RETURNING *
                    ''',
                    (request.agent_role, request.TTL, uuid, store_id))

                row = await cursor.fetchone()

                if row is None:
                    logger.warning("Update character failed")
                    return None

                await conn.commit()

                logger.info("Successfully update ID with new role")

                return row

        except aiosqlite.DatabaseError as e:
            logger.error(f"Database error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None

    async def db_delete_character(self, uuid: str, store_id: str) -> dict | None:
        logger.info(f"Deleting role for ID")
        try:
            async with aiosqlite.connect(self.DB_PATH) as conn:

                cursor = await conn.execute('''
                DELETE FROM characters
                WHERE uuid = ? AND store_id = ?
                ''',
                (uuid, store_id))

                if cursor.rowcount == 0:
                    logger.warning("Resource not deleted because it does not exist.")
                    http_status = status.HTTP_404_NOT_FOUND
                else:
                    logger.info(f"Successfully deleted ID {uuid}")
                    http_status = status.HTTP_204_NO_CONTENT

                await conn.commit()

                return http_status

        except aiosqlite.DatabaseError as e:
            logger.error(f"Database error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None

    async def db_select_character(self, uuid: str, store_id: str) -> dict | None:
        logger.info(f"Fetching role information")
        try:
            async with aiosqlite.connect(self.DB_PATH) as conn:

                cursor = await conn.execute('''
                SELECT agent_role
                FROM characters
                WHERE uuid = ? AND store_id = ?
                ''', (uuid, store_id))
                row = await cursor.fetchone()

                if row is None:
                    logger.warning("uuid does not correspond to any existing IDs in database")
                    return None

                logger.info(f"Successfully fetched data")

                return row

        except aiosqlite.DatabaseError as e:
            logger.error(f"Database error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None

    async def db_select_character_all(self, store_id: str) -> tuple[list[tuple] | None]:
        try:
            async with aiosqlite.connect(self.DB_PATH) as conn:

                cursor = await conn.execute('''
                SELECT *
                FROM characters
                WHERE store_id = ?
                ''', (store_id,))

                rows = await cursor.fetchall()

                if rows is None:
                    logger.warning("Database is empty")
                    return None

                logger.info("retrieving all characters information")

                return rows

        except aiosqlite.DatabaseError as e:
            logger.error(f"Database error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None
