from jose import JWTError, jwt

from app.core.config import get_settings


def verify_refresh_token(token: str) -> str:
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
    except JWTError as exc:
        raise ValueError("Invalid refresh token") from exc

    if payload.get("type") != "refresh":
        raise ValueError("Invalid refresh token")

    subject = payload.get("sub")
    if not subject:
        raise ValueError("Invalid refresh token")

    return str(subject)

