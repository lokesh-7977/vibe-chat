from jose import JWTError, jwt

from app.core.config import get_settings

def verify_access_token(token: str) -> str:
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
    except JWTError as exc:
        raise ValueError("Invalid access token") from exc

    subject = payload.get("sub")
    if not subject:
        raise ValueError("Invalid access token")

    return str(subject)

