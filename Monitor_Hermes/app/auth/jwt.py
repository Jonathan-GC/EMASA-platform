from jose import JWTError, jwt
from app.settings import settings
import loguru

ALGORITHM = settings.JWT_ALGORITHM
SECRET_KEY = settings.JWT_SECRET_KEY


def verify_jwt(token: str) -> dict | None:
    """
    Verifies and decodes a JWT token.

    Args:
        token (str): The JWT token to verify.

    Returns:
        dict | None: A dictionary containing user information if the token is valid, otherwise raises ValueError.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload:
            user_id: str = payload.get("user_id")
            username: str = payload.get("username")
            tenant_id: str = payload.get("cs_tenant_id", None)
            is_superuser: bool = payload.get("is_superuser", False)
            is_global: bool = payload.get("is_global", False)
        else:
            raise ValueError("Invalid token: empty payload")

        if user_id is None:
            raise ValueError("Invalid token: missing user_id")

        return {
            "user_id": user_id,
            "username": username,
            "tenant_id": tenant_id,
            "is_superuser": is_superuser,
            "is_global": is_global,
        }
    except JWTError as e:
        raise ValueError(f"Invalid token: {str(e)}")
