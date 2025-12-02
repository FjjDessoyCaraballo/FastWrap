import aiosqlite
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.parent
DB_PATH = PROJECT_ROOT / "database/fastwrapper.db"

clients_table = """
CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1,
    subscription TEXT DEFAULT 'free',
    store_name TEXT,
    phone TEXT
)
"""

characters_table = """
CREATE TABLE IF NOT EXISTS characters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    store_id INTEGER REFERENCES clients(id),
    uuid TEXT UNIQUE NOT NULL,
    agent_role TEXT NOT NULL,
    TTL INTEGER
)
"""

async def db_creation() -> None:
    try:
        logger.info(f"Creating database {DB_PATH}...")
        async with aiosqlite.connect(DB_PATH) as conn:
            await conn.execute(clients_table)
            await conn.execute(characters_table)
            await conn.commit()
        logger.info("Tables and database successfully created/updated")
    except Exception as e:
        logger.error(f"Database error: {e}")