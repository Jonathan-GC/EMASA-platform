import jwt
import datetime
from django.conf import settings

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"


def generate_token(
    user_id: int = None, scope: str = "", expires_minutes: int = 30, **extras
) -> str:
    expiration = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        minutes=expires_minutes
    )
    if user_id is None:
        user_id = 0
    payload = {"user_id": user_id, "scope": scope, "exp": expiration}
    if extras:
        payload.update(extras)
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token


def verify_token(token: str, expected_scope: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("scope") not in expected_scope:
            raise ValueError("Invalid token scope")
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")
