import asyncpg
import logging
import uuid
from ..models import schemas
from fastapi import status
from ..database.init import init_db

logger = logging.getLogger(__name__)

class crud_management():
    async def db_insertion_character(self, request: schemas.ServiceRole, client_id: str):
        """
        Inserts into characters(client_id, agent_role, ttl). Returns full row tuple.
        """
        logger.info('Inserting new character')
        try:
            id = uuid.UUID(client_id)
            pool = await init_db()
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    INSERT INTO characters (client_id, agent_role, ttl)
                    VALUES ($1, $2, $3)
                    RETURNING id, client_id, agent_role, ttl, deleted_at
                    """,
                    id, request.agent_role, request.TTL
                )
            if row is None:
                logger.warning('Character could not be created.')
                return None
            return tuple(row)
        except (ValueError, TypeError):
            logger.error('Invalid ID')
            return None
        except asyncpg.PostgresError as e:
            logger.error(f"Database error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None
    
    async def db_update_character(self, uuid_str: str, request: schemas.ServiceRole, client_id: str):
        """
        Updates characters by (id, client_id) if not soft-deleted. Returns updated row tuple.
        """
        logger.info('Updating character')
        try:
            character_id = uuid.UUID(uuid_str)
            id = uuid.UUID(client_id)
            pool = await init_db()
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    UPDATE characters
                    SET agent_role = $1
                        ttl = $2
                    WHERE id = $3
                        AND client_id = $4
                        AND deleted_at IS NULL
                    RETURNING id, client_id, agent_role, ttl, deleted_at
                    """,
                    request.agent_role, request.TTL,
                    character_id, id
                )
            if row is None:
                logger.warning('Update character failed (not found/deleted)')
                return None
        except (ValueError, TypeError):
            logger.error("Invalid UUID for character id or store_id")
            return None
        except asyncpg.PostgresError as e:
            logger.error(f"Database error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None

    async def df_delete_character(self, uuid_str: str, client_id: str):
        """
        Soft delete characters row. Returns HTTP status code.
        """
        logger.info('Deleting character')
        try:
            character_id = uuid.UUID(uuid_str)
            id = uuid.UUID(client_id)
            pool = await init_db()
            async with pool.acquire() as conn:
                deleted = await conn.fetchval(
                    """
                    UPDATE characters
                    SET deleted_at = now()
                    WHERE id = $1
                        AND client_id = $2
                        AND deleted_at IS NULL
                    RETURNING id
                    """, character_id, id
                )
            if deleted is None:
                logger.warning('Character not deleted')
                return status.HTTP_404_NOT_FOUND
            return status.HTTP_204_NO_CONTENT
        except (ValueError, TypeError):
            logger.error('Invalid ID')
            return None
        except asyncpg.PostgresError as e:
            logger.error(f"Database error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None

    async def db_select_character(self, uuid_str: str, client_id: str):
        """
        Returns (agent_role,) tuple to keep your existing downstream code working.
        """
        logger.info('Fetching character role information')
        try:
            character_id = uuid.UUID(uuid_str)
            id = uuid.UUID(client_id)
            pool = await init_db()
            async with pool.acquire() as conn:
                role = await conn.fetchval(
                    """
                    SELECT agent_role
                    FROM characters
                    WHERE id = $1
                        AND client_id = $2
                        AND deleted_at IS NULL
                    """, character_id, id
                )
            if role is None:
                logger.warning('Character not found')
                return None
            return (role)
        except (ValueError, TypeError):
            logger.error('Invalid ID')
            return None
        except asyncpg.PostgresError as e:
            logger.error(f"Database error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None
    
    async def db_select_character_all(self, client_id: str):
        """
        Returns list[tuple] like your old sqlite fetchall().
        """
        try:
            id = uuid.UUID(client_id)
            pool = await init_db()
            async with pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT id, client_id, agent_role, ttl, deleted_at
                    FROM characters
                    WHERE client_id = $1
                        AND deleted_at IS NULL
                    ORDER BY id
                    """, id
                )
            if not rows:
                logger.warning('No characters found for client')
                return None
            return [tuple(r) for r in rows]
        except (ValueError, TypeError):
            logger.error('Invalid ID')
            return None
        except asyncpg.PostgresError as e:
            logger.error(f"Database error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None
