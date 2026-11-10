from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader

from app.core.config import API_KEY

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_api_key(api_key: str = Security(api_key_header)) -> None:
    """
    Validates the X-API-Key header.
    If API_KEY is not set in the environment, authentication is disabled (dev mode).
    """
    if not API_KEY:
        return  # auth disabled — useful for local development
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key. Set the X-API-Key header.",
        )
