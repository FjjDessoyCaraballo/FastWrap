from ..models.schemas import Completions, RoleRequest
from ..clients.redis_client import redis_client as r
from fastapi import HTTPException

async def store_message(request: Completions):
    try: 
        await r.hset(f"chat:{request.uuid}", mapping={
            "uuid": request.uuid,
            "role": request.role,
            "content": request.content,
        })
        await r.expire(f"chat:{request.uuid}", 300)
        return 201
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def store_character(request: RoleRequest):
    return









# OLD CODE FROM STORE_CHARACTER (TO BE DELETED)
    # try:
    #     await r.hset(f"character:{request.uuid}", mapping={
    #         "uuid": request.uuid,
    #         "agent_role": request.agent_role,
    #     })
    #     if request.TTL:
    #         r.expire(f"character:{request.uuid}", request.TTL)
    #     return 201
    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=str(e))
    # returnk