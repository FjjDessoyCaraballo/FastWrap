import asyncio
import logging
import json
from pathlib import Path
import asyncpg
from pgvector.asyncpg import register_vector
from config import settings

logger = logging.getLogger(__name__)

SCHEMA_PATH = Path(__file__).with_name('schema.sql')
SCHEMA_VERSION = 6

_pool: asyncpg.Pool | None = None

async def _init_conn(conn: asyncpg.Connection) -> None:
    await conn.execute('CREATE EXTENSION IF NOT EXISTS vector;')
    # asyncpg defaults json/jsonb to str. These codecs allow passing dict/list directly.
    await conn.set_type_codec(
        "json",
        encoder=json.dumps,
        decoder=json.loads,
        schema="pg_catalog",
        format="text",
    )
    await conn.set_type_codec(
        "jsonb",
        encoder=json.dumps,
        decoder=json.loads,
        schema="pg_catalog",
        format="text",
    )
    await register_vector(conn)

def _split_sql_statements(sql: str) -> list[str]:
    """
    Very simple splitter for a schema file (no functions/procs with $$ blocks).
    Good enough for your current schema.sql.
    """
    lines = []
    for line in sql.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith('--'):
            continue
        lines.append(line)
    cleaned = '\n'.join(lines)

    statements = []
    for stmt in cleaned.split(';'):
        stmt = stmt.strip()
        if stmt:
            statements.append(stmt + ';')
    return statements

async def _create_pool_with_retry(dsn: str, attempts: int = 30, delay_s: float = 1.0) -> asyncpg.Pool:
    last_err: Exception | None = None
    for i in range(attempts):
        try:
            return await asyncpg.create_pool(dsn=dsn, min_size=1, max_size=10, init=_init_conn)
        except Exception as e:
            last_err = e
            logger.warning(f"Postgres not ready yet ({i+1}/{attempts}): {e}")
            await asyncio.sleep(delay_s)
    raise RuntimeError(f"Could not connect to Postgres after {attempts} attempts: {last_err}")

async def _ensure_schema(pool: asyncpg.Pool) -> None:
    sql_text = SCHEMA_PATH.read_text(encoding="utf-8")
    statements = _split_sql_statements(sql_text)

    async with pool.acquire() as conn:
        reg = await conn.fetchval("SELECT to_regclass('public.app_schema')")
        if reg is not None:
            current = await conn.fetchval("SELECT MAX(version) FROM app_schema")
            if current is not None and int(current) >= SCHEMA_VERSION:
                logger.info(f"Schema already applied (version {current}). Skipping.")
                return

        logger.info("Applying schema.sql ...")
        async with conn.transaction():
            for stmt in statements:
                await conn.execute(stmt)

    logger.info("Schema applied successfully.")

async def init_db() -> asyncpg.Pool:
    """
    Called once at startup.
    Creates a pool and applies schema.sql once (via app_schema marker).
    """
    global _pool
    if _pool is not None:
        return _pool
    if not getattr(settings, 'DATABASE_URL', None):
        raise RuntimeError('DATABASE_URL is missing. Set it in .env/docker-compose')
    _pool = await _create_pool_with_retry(settings.DATABASE_URL)
    await _ensure_schema(_pool)
    return _pool

async def close_db() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None