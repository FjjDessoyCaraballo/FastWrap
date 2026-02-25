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
    async def db_any_admin_exits(self) -> bool:
        """True if at least one active (not deleted) admin exists."""
        try:
            pool = await init_db()
            async with pool.acquire() as conn:
                found = await conn.fetchval(
                    """
                    SELECT 1
                    FROM clients
                    WHERE is_admin = TRUE
                        AND deleted_at IS NULL
                        AND is_active = TRUE
                    LIMIT 1
                    """
                )
            return found is not None
        except asyncpg.PostgresError as e:
            logger.error(f"Database error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return False

    async def db_create_admin(self, email: str, password: str):
        """
        Inserts a new client (active) that is admin and returns a dict-like row (keeps your existing calling style).
        """
        try:
            hashed_pw: str = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode("utf-8")
            api_key: str = f"fn_{secrets.token_urlsafe(32)}"
            pool = await init_db()
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    INSERT INTO clients (email, password, api_key, is_admin)
                    VALUES ($1, $2, $3, TRUE)
                    RETURNING id, email, api_key, created_at, deleted_at, is_active, subscription, store_name, phone, is_admin
                    """,
                    email, hashed_pw, api_key
                )
                if row is None:
                    logger.warning('Failed to create client (admin) resource')
                    return None
                return dict(row)
        except UniqueViolationError:
            logger.warning(f"Email already exists (active client): {email}")
            return None
        except asyncpg.PostgresError as e:
            logger.error(f"Database error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None


    async def db_insert_client(
        self,
        email: str,
        password: str,
        *,
        is_admin: bool = False,
        is_active: bool = True,
        subscription: str = "free",
        strore_name: str | None = None,
        phone: str | None = None
    ):
        """
        Inserts a new client and returns a dict-like.
        Backwards compatible with old calls: db_insert_client(email, password)
        """
        try:
            hashed_pw: str = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode("utf-8")
            api_key: str = f"fn_{secrets.token_urlsafe(32)}"
            pool = await init_db()
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    INSERT INTO clients (email, password, api_key, is_active, subscription, store_name, phone, is_admin)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    RETURNING id, email, api_key, created_at, deleted_at, is_active, subscription, store_name, phone, is_admin
                    """,
                    email, hashed_pw, api_key, is_active,
                    subscription, strore_name, phone, is_admin
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
        Used by verify_api_key dependency. Returns (id, email, api_key, is_admin) dict.
        """
        try:
            pool = await init_db()
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT id, email, api_key, COALESCE(is_admin, FALSE) AS is_admin
                    FROM clients
                    WHERE api_key = $1
                        AND deleted_at IS NULL
                        AND is_active = TRUE
                    """, api_key
                )
            if row is None:
                logger.warning('No matching API key (or client inactive/deleted)')
                return None
            return dict(row) if row else None
            # return (row['id'], row['email'], row['api_key'], row['is_admin'])
        except asyncpg.PostgresError as e:
            logger.error(f"Database error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None

    async def db_admin_list_clients(self, *, include_deleted: bool = False) -> list[dict] | None:
        try:
            pool = await init_db()
            async with pool.acquire() as conn:
                if include_deleted:
                    rows = await conn.fetch(
                        """
                        SELECT id, email, api_key, is_active, subscription, store_name, phone,
                            COALESCE(is_admin, FALSE) AS is_admin
                        FROM clients
                        ORDER BY created_at DESC
                        """
                    )
                else:
                    rows = await conn.fetch(
                        """
                        SELECT id, email, api_key, is_active, subscription, store_name, phone,
                            COALESCE(is_admin, FALSE) AS is_admin
                        FROM clients
                        WHERE deleted_at IS NULL
                        ORDER BY created_at DESC
                        """
                    )
                return [dict(r) for r in rows]
        except asyncpg.PostgresError as e:
            logger.error(f"Database error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None

    async def db_admin_get_client(self, client_id: str) -> dict | None:
        try:
            id_ = client_id if isinstance(client_id, uuid.UUID) else uuid.UUID(client_id)
            pool = await init_db()
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT id, email, api_key, created_at, deleted_at, is_active, subscription, store_name, phone,
                        COALESCE(is_admin, FALSE) AS is_admin
                    FROM clients
                    WHERE id = $1
                    """, id_
                )
            return dict(row) if row else None
        except (ValueError, TypeError):
            logger.error("Invalid UUID for client_id")
            return None
        except asyncpg.PostgresError as e:
            logger.error(f"Database error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None  

    async def db_admin_update_client(
        self,
        client_id: str,
        *,
        email: str | None = None,
        password: str | None = None,
        is_admin: bool | None = None,
        is_active: bool | None = None,
        subscription: str | None = None,
        strore_name: str | None = None,
        phone: str | None = None
    ) -> dict | None:
        """
        Admin update: can update multiple fields at once.
        """
        try:
            id_ = client_id if isinstance(client_id, uuid.UUID) else uuid.UUID(client_id)
            hashed_pw: str | None = None
            if password is not None:
                hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode("utf-8")
            pool = await init_db()
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    UPDATE clients
                    SET email        = COALESCE($1, email),
                        password     = COALESCE($2, password),
                        is_admin     = COALESCE($3, is_admin),
                        is_active    = COALESCE($4, is_active),
                        subscription = COALESCE($5, subscription),
                        store_name   = COALESCE($6, store_name),
                        phone        = COALESCE($7, phone)
                    WHERE id = $8
                        AND deleted_at IS NULL
                    RETURNING id, email, api_key, created_at, is_active, subscription, store_name, phone,
                        COALESCE(is_admin, FALSE) AS is_admin
                    """, email, hashed_pw, is_admin, is_active, subscription, strore_name, phone, id_
                )
            return dict(row) if row else None
        except UniqueViolationError:
            logger.warning(f"Email already exists (active client): {email}")
            return None
        except (ValueError, TypeError):
            logger.error("Invalid UUID for client_id")
            return None
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
            id = client_id if isinstance(client_id, uuid.UUID) else uuid.UUID(client_id)
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
    
    async def db_update_client(self, client_id: str, email: str | None, password: str | None) -> dict | None:
        """
        Non-admin update (your existing behavior): update email OR password.
        """
        logger.info('Updating client account')
        try:
            id = client_id if isinstance(client_id, uuid.UUID) else uuid.UUID(client_id)
            pool = await init_db()
            async with pool.acquire() as conn:
                if password is None and email is not None:
                    row = await conn.fetchrow(
                        """
                        UPDATE clients
                        SET email = $1
                        WHERE id = $2
                            AND deleted_at IS NULL
                        RETURNING id, email, api_key, created_at, deleted_at, is_active, subscription, store_name, phone,
                            COALESCE(is_admin, FALSE) AS is_admin
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
                        RETURNING id, email, api_key, created_at, deleted_at, is_active, subscription, store_name, phone,
                            COALESCE(is_admin, FALSE) AS is_admin
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
    
    async def db_regenerate_key(self, client_id: str) -> dict | None:
        """
        Generates and stores a new api_key, returns it.
        """
        try:
            id = client_id if isinstance(client_id, uuid.UUID) else uuid.UUID(client_id)
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