
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS vector;

-- Minimal 'version marker' so startup knows whether schema is already applied
CREATE TABLE IF NOT EXISTS app_schema (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS clients (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           TEXT NOT NULL,
    password        TEXT NOT NULL,
    api_key         TEXT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at      TIMESTAMPTZ,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    subscription    TEXT NOT NULL DEFAULT 'free',
    store_name      TEXT,
    phone           TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_clients_email_active
ON clients (email)
WHERE deleted_at IS NULL;

CREATE TABLE IF NOT EXISTS characters (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id   UUID NOT NULL REFERENCES clients(id) ON DELETE RESTRICT,
    agent_role  TEXT NOT NULL,
    ttl         INTEGER,
    deleted_at  TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_characters_client_id ON characters (client_id);

CREATE TABLE IF NOT EXISTS embeddings (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id   UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    entity_type TEXT NOT NULL,
    entity_id   UUID NOT NULL,
    content     TEXT NOT NULL,
    embedding   vector(1536) NOT NULL,
    metadata    JSONB,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at  TIMESTAMPTZ
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_embeddings_unique_active
ON embeddings (client_id, entity_type, entity_id)
WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_embeddings_embedding_hnsw
    ON embeddings
    USING hnsw (embedding vector_cosine_ops)
    WHERE deleted_at IS NULL;

INSERT INTO app_schema(version) VALUES (3)
ON CONFLICT (version) DO NOTHING;
