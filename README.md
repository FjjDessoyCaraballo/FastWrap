# FastWrap

This is a wrapper backend service designed to simplify chatbot integrations through abstraction in backend. The service works by caching conversations in server-side and simplifying service through RESTful API calls. The main part of this project is the chat cahing logic:

```
routes.py (thin)
    ↓ calls
ChatCacheService (business logic)
    ↓ uses
RedisClient (data storage)
```
