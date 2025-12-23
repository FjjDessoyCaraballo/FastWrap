# FastWrap

A wrapper backend service designed to simplify chatbot integrations through abstraction. The service works by caching conversations server-side and exposing functionality through a RESTful API.

## Overview

The core architecture follows a thin-controller pattern:
```
routes.py (thin)
    ↓ calls
Services (business logic)
    ↓ uses
CRUD / RedisClient (data storage)
```

## Features

- Multi-tenant chatbot configurations (characters) per store
- Conversation caching with automatic expiration
- API key authentication
- LangChain-powered AI responses
- Configurable LLM provider

## Tech Stack

- **Framework:** FastAPI
- **Package Manager:** uv
- **Cache:** Redis (5-minute TTL)
- **Database:** SQLite (aiosqlite)
- **AI:** LangChain + configurable LLM
- **Auth:** API key + bcrypt
- **Containerization:** Docker & Docker Compose

## Prerequisites

- Python 3.12+
- Docker & Docker Compose
- uv package manager

## Installation & Setup

1. Clone the repository
2. Install dependencies:
```bash
   uv sync
```
3. Copy `.env.example` to `.env` and fill in values
4. Start Redis:
```bash
   docker compose up redis -d
```
5. Run the application:
```bash
   uv run main.py
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `FASTWRAP_API_KEY` | Yes | Service API key |
| `REDIS_API_KEY` | Yes | Redis authentication key |
| `REDIS_HOST` | Yes | Redis host address |
| `REDIS_PORT` | Yes | Redis port |
| `PORT` | Yes | Server port (default: 8555) |
| `HOST` | Yes | Server host |
| `MODEL` | Yes | LLM model identifier |
| `MODEL_KEY` | Yes | LLM provider API key |
| `MODEL_PROVIDER` | No | LLM provider (if auto-detection fails) |
| `LANGCHAIN_API_KEY` | No | LangSmith API key for tracing |
| `LANGSMITH_TRACING_V2` | No | Enable LangSmith tracing (default: true) |

## API Endpoints

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/` | Service info | No |
| GET | `/health` | Health check | No |
| POST | `/auth/signup` | Register new client | No |
| GET | `/api/clients/me` | Get client info | Yes |
| DELETE | `/clients/me` | Delete client account | Yes |
| POST | `/api/characters` | Create character | Yes |
| GET | `/api/characters` | List all characters | Yes |
| GET | `/api/characters/{uuid}` | Get character | Yes |
| PATCH | `/api/characters/{uuid}` | Update character | Yes |
| DELETE | `/api/characters/{uuid}` | Delete character | Yes |
| POST | `/api/chat` | Send chat message | Yes |

For detailed request/response schemas, refer to the Swagger documentation at `/docs` when the server is running.

## Architecture

For a detailed system flowchart and data flow diagrams, see [FLOWCHART.md](documents/FLOWCHART.md).

## FAQ

**Q: What if someone tries a DDoS attack using multiple instances to overwhelm the server?**

A: Rate limiting is planned to ensure that abuse gets timed out, allowing Redis to clean up initial attempts and making the attack ineffective.