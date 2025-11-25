# FastWrap

This is a wrapper backend service designed to simplify chatbot integrations through abstraction in backend. The service works by caching conversations in server-side and simplifying service through RESTful API calls. The main part of this project is the chat cahing logic:

```
routes.py (thin)
    ↓ calls
ChatCacheService (business logic)
    ↓ uses
RedisClient (data storage)
```

___

### FAQ

#### Question: What if someone tries to make a DDoS attack by using multiple instances to overwhelm the server?

- Answer: The server should and will contain rate limiting to make sure that abuse will get timed out just for enough time for Redis to cleanup first attempts, which should make the attempt fruitless.