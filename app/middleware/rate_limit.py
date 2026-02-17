from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from collections import defaultdict
from datetime import datetime, timedelta
import asyncio
from typing import Callable


class RateLimiter:
    """Rate limiter simple en memoria para FastAPI"""
    
    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000
    ):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self._requests = defaultdict(list)
        self._lock = asyncio.Lock()
    
    def _cleanup_old_requests(self, client_id: str):
        """Eliminar peticiones antiguas del registro"""
        now = datetime.utcnow()
        minute_ago = now - timedelta(minutes=1)
        hour_ago = now - timedelta(hours=1)
        
        self._requests[client_id] = [
            req_time for req_time in self._requests[client_id]
            if req_time > hour_ago
        ]
    
    async def is_allowed(self, client_id: str) -> tuple[bool, dict]:
        """Verifica si el cliente puede hacer una petición"""
        async with self._lock:
            now = datetime.utcnow()
            minute_ago = now - timedelta(minutes=1)
            hour_ago = now - timedelta(hours=1)
            
            self._cleanup_old_requests(client_id)
            
            requests_last_minute = sum(
                1 for req_time in self._requests[client_id]
                if req_time > minute_ago
            )
            
            requests_last_hour = len(self._requests[client_id])
            
            if requests_last_minute >= self.requests_per_minute:
                return False, {
                    "error": "Rate limit excedido",
                    "retry_after": 60,
                    "limit": self.requests_per_minute,
                    "window": "minute"
                }
            
            if requests_last_hour >= self.requests_per_hour:
                return False, {
                    "error": "Rate limit excedido",
                    "retry_after": 3600,
                    "limit": self.requests_per_hour,
                    "window": "hour"
                }
            
            self._requests[client_id].append(now)
            return True, {}


rate_limiter = RateLimiter(requests_per_minute=60, requests_per_hour=1000)


async def rate_limit_middleware(request: Request, call_next: Callable):
    """Middleware de rate limiting"""
    
    if request.url.path in ["/", "/health", "/docs", "/redoc", "/openapi.json"]:
        return await call_next(request)
    
    client_id = request.client.host if request.client else "unknown"
    
    if "X-Forwarded-For" in request.headers:
        forwarded = request.headers["X-Forwarded-For"]
        client_id = forwarded.split(",")[0].strip()
    
    allowed, info = await rate_limiter.is_allowed(client_id)
    
    if not allowed:
        return JSONResponse(
            status_code=429,
            content={
                "detail": "Demasiadas peticiones. Por favor, espere antes de reintentar.",
                **info
            },
            headers={"Retry-After": str(info.get("retry_after", 60))}
        )
    
    response = await call_next(request)
    return response