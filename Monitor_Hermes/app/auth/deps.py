"""
Dependencias de autenticación para FastAPI
"""

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader
from app.settings import settings

# Header para la API Key
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_service_api_key(api_key: str = Security(api_key_header)) -> bool:
    """
    Verifica que la API Key proporcionada coincida con la configurada.
    Esta dependencia se usa para endpoints de comunicación service-to-service.
    """
    if api_key is None or api_key != settings.SERVICE_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid or missing API Key"
        )
    return True
