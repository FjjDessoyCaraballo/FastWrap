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

    async def db_insertion_character(self, request: schemas.RoleRequest) -> int:
        logger.info(f"Inserting new character")
        try:
            async with aiosqlite.connect(self.DB_PATH) as conn:

                if request.TTL is None:
                    await conn.execute(f"""INSERT INTO characters ( uuid, agent_role ) 
                    VALUES (?, ?)
                    """, (request.uuid, request.agent_role))
                else:
                    await conn.execute(f"""INSERT INTO characters ( uuid, agent_role, TTL ) 
                    VALUES ( ?, ?, ? )
                    """, (request.uuid, request.agent_role, request.TTL))

                await conn.commit()

                logger.info("Successfully created ID with new role")

                return status.HTTP_201_CREATED

        except aiosqlite.DatabaseError as e:
            logger.error(f"Database error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise

    async def db_update_character(self, uuid: str, request: schemas.RoleRequest) -> int:
        logger.info("Updating new role")
        try:
            async with aiosqlite.connect(self.DB_PATH) as conn:
        
                if request.TTL is None:
                    await conn.execute("UPDATE OR ABORT characters SET agent_role = ? WHERE uuid = ?", 
                    (request.agent_role, uuid))
                else:
                    await conn.execute("UPDATE OR ABORT characters SET agent_role = ?, TTL = ? WHERE uuid = ?", 
                    (request.agent_role, request.TTL, uuid))
        
                await conn.commit()
        
                logger.info(f"Successfully update ID with new role")
        
                return status.HTTP_200_OK
        
        except aiosqlite.DatabaseError as e:
            logger.error(f"Database error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise

    async def db_delete_character(self, uuid: str) -> int:
        logger.info(f"Deleting role for ID: {uuid}")
        try:
            async with aiosqlite.connect(self.DB_PATH) as conn:
        
                cursor = await conn.execute("DELETE FROM characters WHERE uuid = ?", 
                (uuid,))
        
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
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise

    async def db_select_character(self, uuid: str) -> tuple[str, int]:
        logger.info(f"Fetching information for role ID: {uuid}")
        try:
            async with aiosqlite.connect(self.DB_PATH) as conn:
        
                cursor = await conn.execute("SELECT agent_role FROM characters WHERE uuid = ?", (uuid,))
                row = await cursor.fetchone()
        
                if row is None:
                    logger.warning("uuid does not correspond to any existing IDs in database")
                    return None, status.HTTP_404_NOT_FOUND
        
                agent_role = row[0]
        
                logger.info(f"Successfully fetched data {agent_role}")
        
                return agent_role, status.HTTP_200_OK
        
        except aiosqlite.DatabaseError as e:
            logger.error(f"Database error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise

    async def db_select_character_all(self) -> tuple[list[tuple] | None, int]:
        try:
            async with aiosqlite.connect(self.DB_PATH) as conn:
        
                cursor = await conn.execute("SELECT * FROM characters")
                rows = await cursor.fetchall()
        
                if rows is None:
                    logger.warning("Database is empty")
                    return None, status.HTTP_404_NOT_FOUND
        
                logger.info("retrieving all characters information")
        
                return rows, status.HTTP_200_OK
        
        except aiosqlite.DatabaseError as e:
            logger.error(f"Database error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise

    async def db_insert_client(self, email: str, password: str):
        try:
            hashed_password: str = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode('utf-8')
            api_key: str = f"vcp_{secrets.token_urlsafe(32)}"
            hashed_key: str = bcrypt.hashpw(api_key.encode(), bcrypt.gensalt()).decode('utf-8')
            async with aiosqlite.connect(self.DB_PATH) as conn:
                
                await conn.execute('''
                    INSERT INTO clients ( email, password, api_key )
                    VALUES ( ? , ? , ? )
                ''', (email, hashed_password, hashed_key))
                
                logger.debug('user registered')
                
                await conn.commit()
                
                return api_key, status.HTTP_201_CREATED

        except aiosqlite.IntegrityError:
            logger.warning(f'Email already exists in database: {email}')
            return None, status.HTTP_409_CONFLICT
        except aiosqlite.DatabaseError as e:
            logger.error(f'Database error: {e}')
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {e}')
            raise

    async def db_select_client(self, email: str, password: str, api_key: str):
        try:
            async with aiosqlite.connect(self.DB_PATH) as conn:
                cursor = await conn.execute('''
                    SELECT id, password, api_key FROM clients WHERE email = ?
                ''', (email,))

                row = await cursor.fetchone()

                if row is None:
                    logger.warning("No matching email in attempt")
                    return status.HTTP_401_UNAUTHORIZED

                stored_pw_hash = row[1]
                stored_api_hash = row[2]

                if not bcrypt.checkpw(password.encode(), stored_pw_hash.encode()):
                    logger.warning("Wrong password attempt")
                    return status.HTTP_401_UNAUTHORIZED
                elif not bcrypt.checkpw(api_key.encode(), stored_api_hash.encode()):
                    logger.warning("Wrong api key attempt")
                    return status.HTTP_401_UNAUTHORIZED
                
                logger.info("User properly identified")
                
                return status.HTTP_200_OK

        except aiosqlite.DatabaseError as e:
            logger.error(f'Database error: {e}')
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {e}')
            raise