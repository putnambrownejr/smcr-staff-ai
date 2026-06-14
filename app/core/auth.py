from typing import Annotated

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.core.config import get_settings

api_key_header = APIKeyHeader(name="X-Local-API-Key", auto_error=False)


def require_local_api_key(api_key: Annotated[str | None, Security(api_key_header)] = None) -> None:
    """Optional local API key gate for personal stores and write-capable connectors."""

    expected = get_settings().local_api_key or None
    if expected is None:
        return
    if api_key != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid local API key.",
        )


LocalApiKeyDependency = Depends(require_local_api_key)
