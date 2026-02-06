from .redis_client import redis_client as r
from fastapi import status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from config import settings
import logging
import time

logger = logging.getLogger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next
        ) -> Response:
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
        request : Request
            HTTP request coming from an user.

        call_next
            Complex type defined by base class BaseHTTPMiddleware

        Returns:
        -------- 
        response : Response
            HTTP response sent to user.
        """        
        ip = request.headers.get("x-forwarded-for")
        if ip is None:
            logger.debug("x-forwarded-for not present in headers")
            if request.client is not None:
                logger.debug("fallback to request.client.host")
                # fallback in case headers do not contain IP
                ip = request.client.host
            else:
                logger.error("No IP present in headers, sending JSON with HTTP code 400")
                return JSONResponse(
                    status_code=400,
                    content={"detail": "IP not present in headers"}
                    )

        # At this point, we are certain to have an IP
        logger.info(f"ip: {ip}") # Check logs

        try:
            now = int(time.time())
            bucket = now // settings.API_WINDOW

            attempts: int = await r.incr(f"middleware:{ip}:{bucket}")
            if attempts == 1:
                await r.expire(f"middleware:{ip}:{bucket}", settings.API_WINDOW_EXPIRE)
            elif attempts > settings.API_LIMIT:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too many requests"}
                )
        except Exception as e:
            logger.error(f"Unexpected error with Redis: {e}")

        response: Response = await call_next(request)
        return response
