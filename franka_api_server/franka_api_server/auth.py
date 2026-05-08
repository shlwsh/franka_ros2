from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from .config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def get_api_key(api_key_header: str = Security(api_key_header)):
    if not settings.auth_enabled:
        return True
    
    if api_key_header == settings.api_key:
        return api_key_header
        
    # Also allow passing API key via query parameter for WebSockets
    # This will be handled directly in the websocket endpoint
        
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API Key",
    )
