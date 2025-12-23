import aiosqlite
import logging
import secrets
import bcrypt
from pathlib import Path
from fastapi import status

logger = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).parent.parent.parent

class crud_management():
    def __init__(self):
        self.DB_PATH = PROJECT_ROOT / "database/fastwrapper.db"

    async def db_insert_client(self, email: str, password: str) -> dict | None:
        try:
            hashed_password: str = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode('utf-8')
            api_key: str = f"vcp_{secrets.token_urlsafe(32)}"
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

                return resource

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

    async def db_delete_client(self, store_id: str) -> int | None:
        logger.info(f"Deleting client account")
        try:
            async with aiosqlite.connect(self.DB_PATH) as conn:

                cursor = await conn.execute('''
                DELETE FROM clients
                WHERE id = ?
                ''',
                (store_id,))

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

    async def db_update_client(self, store_id: str, email: str, password: str):
        logger.info('Updating client account')
        try:
            async with aiosqlite.connect(self.DB_PATH) as conn:
                if password is None:
                    cursor = await conn.execute('''
                        UPDATE OR ABORT clients
                        SET email = ?
                        WHERE id = ?
                        RETURNING *
                    ''', (email, store_id))
                elif email is None:
                    hashed_password: str = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode('utf-8')
                    cursor = await conn.execute('''
                        UPDATE OR ABORT clients
                        SET password = ?
                        WHERE id = ?
                        RETURNING *
                    ''', (hashed_password, store_id))

                row = await cursor.fetchone()

                if row is None:
                    logger.warning("Update client failed")
                    return None

                await conn.commit()

                logger.info("Updated client successfully")
                return row
        except aiosqlite.DatabaseError as e:
            logger.error(f"Database error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None


    async def db_regenerate_key(self, store_id: str):
        try:
            async with aiosqlite.connect(self.DB_PATH) as conn:

                new_key: str = f"vcp_{secrets.token_urlsafe(32)}"

                cursor = await conn.execute('''
                    UPDATE OR ABORT clients
                    SET api_key = ?
                    WHERE id = ?
                ''', (new_key, store_id))

                row = await cursor.fetchone()

                if row is None:
                    logger.warning("Failed to regenerate key")
                    return None

                return new_key
        except aiosqlite.DatabaseError as e:
            logger.error(f"Database error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None
