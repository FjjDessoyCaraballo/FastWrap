import aiosqlite
import logging
import secrets
import bcrypt
from pathlib import Path
from ..models import schemas
from fastapi import status

logger = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).parent.parent.parent

class crud_management():
    def __init__(self):
        self.DB_PATH = PROJECT_ROOT / "database/fastwrapper.db"

    async def db_insertion_character(self, request: schemas.RoleRequest, store_id: str) -> dict | None:
        logger.info(f"Inserting new character")
        try:
            async with aiosqlite.connect(self.DB_PATH) as conn:

                if request.TTL is None:
                    cursor = await conn.execute("""
                    INSERT INTO characters ( uuid, store_id, agent_role ) 
                    VALUES ( ? , ? , ? )
                    RETURNING *
                    """, (request.uuid, store_id, request.agent_role))
                else:
                    cursor = await conn.execute("""
                    INSERT INTO characters ( uuid, agent_role, TTL ) 
                    VALUES ( ? , ? , ? )
                    RETURNING *
                    """, (request.uuid, request.agent_role, request.TTL))

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

    async def db_update_character(self, uuid: str, request: schemas.RoleRequest, store_id: str) -> dict | None:
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
                    (request.agent_role, uuid))
                else:
                    cursor = await conn.execute('''
                    UPDATE OR ABORT characters 
                    SET agent_role = ?, TTL = ? 
                    WHERE uuid = ?
                    RETURNING *
                    ''', 
                    (request.agent_role, request.TTL, uuid, store_id))

                row = await cursor.fetchone()

                if row is None:
                    logger.warning("Update failed")
                    return None

                await conn.commit()
        
                logger.info(f"Successfully update ID with new role")
        
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

    async def db_insert_client(self, email: str, password: str) -> tuple[str] | None:
        try:
            hashed_password: str = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode('utf-8')
            api_key: str = f"fn_{secrets.token_urlsafe(32)}"
            async with aiosqlite.connect(self.DB_PATH) as conn:
                
                cursor = await conn.execute('''
                INSERT INTO clients ( email, password, api_key )
                VALUES ( ? , ? , ? )
                RETURNING *
                ''', (email, hashed_password, api_key))
                
                resource = await cursor.fetchone()

                if resource is None:
                    logger.warning("Failed to create resource")
                    return None, None

                logger.debug('user registered')
                
                await conn.commit()
                
                return api_key, resource

        except aiosqlite.IntegrityError:
            logger.warning(f'Email already exists in database: {email}')
            return None
        except aiosqlite.DatabaseError as e:
            logger.error(f'Database error: {e}')
            return None
        except Exception as e:
            logger.error(f'Unexpected error: {e}')
            return None

    async def db_select_client(self, email: str, password: str):
        try:
            async with aiosqlite.connect(self.DB_PATH) as conn:
                cursor = await conn.execute('''
                SELECT id, password 
                FROM clients 
                WHERE email = ?
                ''', (email,))

                row = await cursor.fetchone()

                if row is None:
                    logger.warning("No matching email in attempt")
                    return None

                stored_pw_hash = row[1]

                if not bcrypt.checkpw(password.encode(), stored_pw_hash.encode()):
                    logger.warning("Wrong password attempt")
                    return None
                
                logger.info("User properly identified")
                
                return row

        except aiosqlite.DatabaseError as e:
            logger.error(f'Database error: {e}')
            return None
        except Exception as e:
            logger.error(f'Unexpected error: {e}')
            return None


    async def db_select_client_by_key(self, api_key: str) -> dict | None:
        try:
            async with aiosqlite.connect(self.DB_PATH) as conn:
                cursor = await conn.execute('''
                SELECT id, email, api_key
                FROM clients 
                WHERE api_key = ?
                ''', (api_key,))

                resource = await cursor.fetchone()

                if resource is None:
                    logger.warning("No matching key in attempt")
                    return None
                
                logger.info("API key properly identified")
                
                return resource

        except aiosqlite.DatabaseError as e:
            logger.error(f'Database error: {e}')
            return None
        except Exception as e:
            logger.error(f'Unexpected error: {e}')
            return None

    async def db_delete_client(self, email: str, password: str) -> int | None:
        logger.info(f"Deleting client account")
        try:
            async with aiosqlite.connect(self.DB_PATH) as conn:
                
                cursor = await conn.execute('''
                SELECT id, password 
                FROM clients
                WHERE email = ?
                ''', (email,))

                row = await cursor.fetchone()

                if row is None:
                    logger.warning("Email not found")
                    return None

                stored_pw_hash = row[1]
                if not bcrypt.checkpw(password.encode(), stored_pw_hash.encode()):
                    logger.warning("Wrong password attempt")
                    return None  

                cursor = await conn.execute('''
                DELETE FROM clients 
                WHERE email = ?
                ''', 
                (email,))

                if cursor.rowcount == 0:
                    logger.warning("Email was deleted by another process")
                    return None

                http_status = status.HTTP_204_NO_CONTENT
        
                await conn.commit()
        
                return http_status
        
        except aiosqlite.DatabaseError as e:
            logger.error(f"Database error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None
