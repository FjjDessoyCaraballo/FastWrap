import asyncpg
import uuid
import logging
import secrets
import bcrypt
from asyncpg.exceptions import UniqueViolationError
from pathlib import Path
from fastapi import status
from ..database.init import init_db

logger = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).parent.parent.parent

class crud_management:
    async def db_insert_client(self, email: str, password: str):
        """
        Inserts a new client (active) and returns a dict-like row (keeps your existing calling style).
        """
        try:
            hashed_pw: str = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode("utf-8")
            api_key: str = f"fn_{secrets.token_urlsafe(32)}"
            pool = await init_db()
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    INSERT INTO clients (email, password, api_key)
                    VALUES ($1, $2, $3)
                    RETURNING id, email, api_key, created_at, deleted_at, is_active, subscription, store_name, phone
                    """,
                    email, hashed_pw, api_key
                )
            if row is None:
                logger.warning('Failed to create client resource')
                return None
            return dict(row)
        except UniqueViolationError:
            # Our partial unique index on (email) WHERE deleted_at IS NULL triggers this.
            logger.warning(f"Email already exists (active client): {email}")
            return None
        except asyncpg.PostgresError as e:
            logger.error(f"Database error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None
    

    
    async def db_select_client(self, email: str, password: str):
        """
        Auth-like lookup. Returns (id, password_hash) if password matches, else None.
        """
        try:
            pool = await init_db()
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT id, password
                    FROM clients
                    WHERE email = $1
                        AND deleted_at IS NULL
                        AND is_active = TRUE
                    """, email
                )
            if row is None:
                logger.warning('No matching email (or client inactive/deleted)')
                return None
            stored_pw = row['password']
            if not bcrypt.checkpw(password.encode(), stored_pw.encode()):
                logger.warning('Invalid credentials')
                return None
            return (row['id'], row['password'])
        except asyncpg.PostgresError as e:
            logger.error(f"Database error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None
    
    async def db_select_client_by_key(self, api_key: str):
        """
        Used by verify_api_key dependency. Returns (id, email, api_key) dict.
        """
        try:
            pool = await init_db()
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT id, email, api_key
                    FROM clients
                    WHERE api_key = $1
                        AND deleted_at IS NULL
                        AND is_active = TRUE
                    """, api_key
                )
            if row is None:
                logger.warning('No matching API key (or client inactive/deleted)')
                return None
            return (row['id'], row['email'], row['api_key'])
        except asyncpg.PostgresError as e:
            logger.error(f"Database error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None

    async def db_delete_client(self, client_id: str) -> int | None:
        """
        Soft delete client.
        """
        logger.info("Deleting client account")
        try:
            id = uuid.UUID(client_id)

            pool = await init_db()
            async with pool.acquire() as conn:
                deleted = await conn.fetchval(
                    """
                    UPDATE clients
                    SET deleted_at = now(),
                        is_active = FALSE
                    WHERE id = $1
                      AND deleted_at IS NULL
                    RETURNING id
                    """, id
                )
            if deleted is None:
                logger.warning('Client not deleted (not found or already deleted)')
                return None
            return status.HTTP_204_NO_CONTENT
        except (ValueError, TypeError):
            logger.error('Invalid UUID for store_id')
            return None
        except asyncpg.PostgresError as e:
            logger.error(f"Database error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None
    
    async def db_update_client(self, client_id: str, email: str | None, password: str | None):
        """
        Updates either email or password (your service layer prevents both at once).
        Returns updated row dict or None.
        """
        logger.info('Updating client account')
        try:
            id = uuid.UUID(client_id)
            pool = await init_db()
            async with pool.acquire() as conn:
                if password is None and email is not None:
                    row = await conn.fetchrow(
                        """
                        UPDATE clients
                        SET email = $1
                        WHERE id = $2
                            AND deleted_at IS NULL
                        RETURNING id, email, api_key, created_at, deleted_at, is_active, subscription, store_name, phone
                        """,
                        email, id
                    )
                elif email is None and password is not None:
                    hashed_pw: str = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode("utf-8")
                    row = await conn.fetchrow(
                        """
                        UPDATE clients
                        SET password = $1
                        WHERE id = $2
                            AND deleted_at IS NULL
                        RETURNING id, email, api_key, created_at, deleted_at, is_active, subscription, store_name, phone
                        """,
                        hashed_pw, id 
                    )
                else:
                    return None
            if row is None:
                logger.warning("Update client failed (not found or deleted)")
                return None

            return dict(row)

        except UniqueViolationError:
            logger.warning(f"Email already exists (active client): {email}")
            return None
        except (ValueError, TypeError):
            logger.error("Invalid UUID for store_id")
            return None
        except asyncpg.PostgresError as e:
            logger.error(f"Database error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None
    
    async def db_regenerate_key(self, client_id: str) -> str | None:
        """
        Generates and stores a new api_key, returns it.
        """
        try:
            id = uuid.UUID(client_id)
            new_key: str = f"fn_{secrets.token_urlsafe(32)}"
            pool = await init_db()
            async with pool.acquire() as conn:
                updated = await conn.fetchval(
                    """
                    UPDATE clients
                    SET api_key = $1
                    WHERE id = $2
                      AND deleted_at IS NULL
                      AND is_active = TRUE
                    RETURNING api_key
                    """,
                    new_key, id
                )
            if updated is None:
                logger.warning('Failed to regenerate key (not found/inactive/deleted)')
                return None
            return updated
        except (ValueError, TypeError):
            logger.error("Invalid UUID for store_id")
            return None
        except asyncpg.PostgresError as e:
            logger.error(f"Database error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None