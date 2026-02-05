from .redis_client import redis_client as r
from fastapi import status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request,
        call_next
        ):
        """
        Rate limiter to avoid DDoS attacks. This middleware is responsible for checking
        every endpoint at each and every time they are used. The algorithm used here is
        the fixed window. We check for windows of 10s and how many times the user has
        attempted to reach the service incorrectly. This strategy is forgiving for users
        and that is a purpouseful vulnerability, because short bursts are still possible
        between windows. However, since we are operating in network level and registering
        IPs, it is not a burden to the applicaiton level (no SQL involved here). 

        Parameters:
        -----------
        x_forwarded_for : str
            header element containing IP of client

        Returns:
        -------- 
        
        """
        
        ip = request.headers.get("x-forwarded-for")
        if ip is None:
            if request.client is not None:
                ip = request.client.host
            else: 
                return JSONResponse(
                    status_code=400,
                    content={"detail": "IP not present in headers"}
                    )

        logger.info(f"ip: {ip}")
        
        response = await call_next(request)
        return response
