from datetime import datetime, timedelta

from jose import jwt

from app.core.config import get_settings


def create_access_token(data: dict) -> str:
    settings = get_settings()
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(
        minutes=settings.access_token_expire_minutes
    )

    # python-jose expects JSON-serializable claims; use a Unix timestamp for "exp".
    to_encode.update({"exp": int(expire.timestamp())})
    return jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm,
    )
