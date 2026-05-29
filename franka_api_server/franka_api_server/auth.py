from fastapi import HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader

from .config import settings

api_key_header = APIKeyHeader(name='X-API-Key', auto_error=False)


async def get_api_key(
    request: Request,
    api_key_header: str = Security(api_key_header),
):
    if not settings.auth_enabled:
        return True

    key = api_key_header or request.query_params.get('api_key')
    if key == settings.api_key:
        return key
        
    # Also allow passing API key via query parameter for WebSockets
    # This will be handled directly in the websocket endpoint
        
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API Key",
    )
