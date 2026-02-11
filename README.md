# FastWrap

A wrapper backend service designed to simplify chatbot integrations through abstraction. The service works by caching conversations server-side and exposing functionality through a RESTful API.

## Overview

The core architecture follows a thin-controller pattern:
```
routes.py (thin)
    | calls
Services (business logic)
    | uses
Repository / RedisClient (data storage)
```

## Features

- Multi-tenant chatbot configurations (characters) per client
- Conversation caching with automatic expiration
- API key authentication with secure key regeneration
- LangChain-powered AI responses
- Configurable LLM provider with automatic detection
- Vector embeddings for semantic search
- PostgreSQL database with soft deletes
- Comprehensive client management

## Tech Stack

- **Framework:** FastAPI
- **Package Manager:** uv
- **Cache:** Redis (20-minute TTL)
- **Database:** PostgreSQL with asyncpg
- **Vector Store:** pgvector for embeddings
- **AI:** LangChain + configurable LLM
- **Embeddings:** OpenAI embeddings (text-embedding-3-small)
- **Auth:** API key + bcrypt
- **Containerization:** Docker & Docker Compose

## Prerequisites

- Python 3.12+
- Docker & Docker Compose
- uv package manager
- PostgreSQL (via Docker)
- Redis (via Docker)

## Installation & Setup

1. Clone the repository
2. Install dependencies:
```bash
uv sync
```
3. Copy `.example.env` to `.env` and fill in the required values:
```bash
cp .example.env .env
```
4. Start services:
```bash
docker compose up -d
```
5. Run the application:
```bash
uv run main.py
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `FASTWRAP_API_KEY` | Yes | `1234` | Service API key |
| `REDIS_HOST` | Yes | `redis` | Redis host address |
| `REDIS_PORT` | Yes | `6379` | Redis port |
| `REDIS_API_KEY` | Yes | - | Redis authentication key |
| `REDIS_USER` | No | `User123` | Redis username |
| `REDIS_USER_PW` | No | - | Redis user password |
| `PORT` | Yes | `8555` | Server port |
| `HOST` | Yes | `0.0.0.0` | Server host |
| `MODEL` | Yes | `gpt-4o-mini` | LLM model identifier |
| `MODEL_KEY` | Yes | - | LLM provider API key |
| `MODEL_PROVIDER` | No | - | LLM provider (if auto-detection fails) |
| `POSTGRES_HOST` | Yes | `postgres` | PostgreSQL host |
| `POSTGRES_PORT` | Yes | `5432` | PostgreSQL port |
| `POSTGRES_DB` | Yes | `fastwrap_db` | PostgreSQL database name |
| `POSTGRES_USER` | Yes | `postgres` | PostgreSQL username |
| `POSTGRES_PW` | Yes | `postgres` | PostgreSQL password |
| `DATABASE_URL` | Yes | - | Full PostgreSQL connection string |
| `EMBEDDING_MODEL` | No | `text-embedding-3-small` | Embedding model |
| `EMBEDDING_DIM` | No | `1536` | Embedding dimensions |
| `LANGCHAIN_API_KEY` | No | - | LangSmith API key for tracing |
| `LANGSMITH_TRACING_V2` | No | `true` | Enable LangSmith tracing |

## API Endpoints

### General
| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/` | Service info | No |
| GET | `/health` | Health check | No |

### Authentication
| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/auth/signup` | Register new client | No |

### Client Management
| Method | Path | Description | Auth |
|--------|------|-------------|------|
| PATCH | `/clients/me` | Update client email or password | Yes |
| POST | `/clients/me/regenerate-key` | Regenerate API key | Yes |
| DELETE | `/clients/me` | Delete client account (soft delete) | Yes |

### Characters
| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/api/characters` | Create character | Yes |
| GET | `/api/characters` | List all characters | Yes |
| GET | `/api/characters/{uuid}` | Get character | Yes |
| PATCH | `/api/characters/{uuid}` | Update character | Yes |
| DELETE | `/api/characters/{uuid}` | Delete character (soft delete) | Yes |

### Chat
| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/api/chat` | Send chat message | Yes |

### Vector Search
| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/api/vectors/upsert` | Store text snippet with embedding | Yes |
| POST | `/api/vectors/search` | Semantic search across embeddings | Yes |

For detailed request/response schemas, refer to the Swagger documentation at `/docs` when the server is running.

## Architecture

The system uses a layered architecture:

1. **Routes Layer** (`app/api/routes.py`): Thin controllers handling HTTP concerns
2. **Service Layer** (`app/*/service.py`): Business logic and orchestration
3. **Repository Layer** (`app/*/repository.py`): Database access with asyncpg
4. **Infrastructure Layer**: Redis client and database connections

### Key Components

- **Database**: PostgreSQL with schema versioning and soft deletes
- **Cache**: Redis for conversation state (20-minute TTL)
- **Agents**: LangChain agents with dynamic system prompts
- **Vectors**: pgvector for semantic search capabilities
- **Auth**: API key-based authentication with bcrypt password hashing

For detailed system flowchart and data flow diagrams, see [FLOWCHART.md](documents/FLOWCHART.md).

## Password Policy

Passwords must meet the following requirements:
- Minimum 10 characters
- At least one lowercase letter
- At least one uppercase letter
- At least one number
- At least one special character
- No whitespace characters

## Database Schema

The system uses PostgreSQL with the following main tables:

- **clients**: User accounts with soft deletes and unique email constraint
- **characters**: Agent configurations (system prompts) per client
- **embeddings**: Vector embeddings for semantic search with pgvector
- **app_schema**: Version tracking for schema migrations

All tables support soft deletes via `deleted_at` timestamp fields.

## Testing

Run the test suite:
```bash
uv run pytest
```

Tests are organized by feature:
- `tests/client_test.py`: Client management tests (signup, update, key regeneration, deletion)
- `tests/character_test.py`: Character CRUD tests (create, read, update, delete)

## Development

The application uses:
- **Hot reload**: Enabled in development mode
- **Logging**: Console and file-based logging (`logs/logfile.log`)
- **Type hints**: Python 3.12+ type annotations throughout
- **Async/await**: Full async support with asyncpg and asyncio

## Docker Deployment

The `docker-compose.yml` includes:
- **api**: FastAPI application
- **redis**: Redis cache server (redis:7-alpine)
- **postgres**: PostgreSQL database with pgvector extension (pgvector/pgvector:pg16)

Start all services:
```bash
docker compose up -d
```

## Known Limitations & Future Work

See [TECH_DEBT.md](documents/TECH_DEBT.md) for detailed technical debt tracking.

Key items:
- Rate limiting planned for DDoS protection
- LangSmith integration needs debugging
- RAG (Retrieval-Augmented Generation) planned for future releases

## FAQ

**Q: What if someone tries a DDoS attack using multiple instances to overwhelm the server?**

A: Rate limiting is planned to ensure that abuse gets timed out, allowing Redis to clean up initial attempts and making the attack ineffective.

**Q: Can I change both email and password at the same time?**

A: No, the `/clients/me` PATCH endpoint only allows updating one field at a time for security reasons.

**Q: What happens when a client is deleted?**

A: Clients are soft-deleted (marked with `deleted_at` timestamp). Their associated characters are also soft-deleted via CASCADE constraints.

**Q: How do vector embeddings work?**

A: Text snippets are converted to 1536-dimensional vectors using OpenAI's text-embedding-3-small model and stored in PostgreSQL with pgvector for semantic similarity search.
