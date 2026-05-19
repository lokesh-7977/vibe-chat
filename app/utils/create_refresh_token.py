from datetime import datetime, timedelta

from jose import jwt

from app.core.config import get_settings


def create_refresh_token(user_id: str) -> str:
    settings = get_settings()
    expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)

    claims = {
        "sub": user_id,
        "type": "refresh",
        "exp": int(expire.timestamp()),
    }

    return jwt.encode(
        claims,
        settings.secret_key,
        algorithm=settings.algorithm,
    )
