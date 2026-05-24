import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError
from starlette.exceptions import HTTPException as StarletteHTTPException

try:
    from starlette.middleware.sessions import SessionMiddleware
except Exception:  # itsdangerous may be missing -> avoid crashing at import
    SessionMiddleware = None
    logging.getLogger(__name__).warning(
        "starlette.middleware.sessions.SessionMiddleware unavailable (itsdangerous missing). Session middleware will not be added."
    )

from app.api.router import api_router, public_router
from app.core.config import get_settings
from app.core.rate_limiter import RateLimitMiddleware
from app.db.schemas.common import ApiResponse

logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
    )

    if settings.cors_allow_origins:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_allow_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    if SessionMiddleware is not None:
        application.add_middleware(
            SessionMiddleware,
            secret_key=settings.secret_key,
            https_only=not settings.debug,
            same_site="strict",
        )
    else:
        logger.warning("Skipping session middleware because SessionMiddleware is unavailable.")
    auth_prefix = f"{settings.api_prefix}/auth"
    application.add_middleware(
        RateLimitMiddleware,
        rules={
            f"{auth_prefix}/register": (
                settings.auth_rate_limit_register_requests,
                settings.auth_rate_limit_window_seconds,
            ),
            f"{auth_prefix}/login": (
                settings.auth_rate_limit_login_requests,
                settings.auth_rate_limit_window_seconds,
            ),
            f"{auth_prefix}/refresh": (
                settings.auth_rate_limit_refresh_requests,
                settings.auth_rate_limit_window_seconds,
            ),
            f"{auth_prefix}/get-profile": (
                settings.auth_rate_limit_profile_requests,
                settings.auth_rate_limit_window_seconds,
            ),
            f"{auth_prefix}/delete-account": (
                settings.auth_rate_limit_delete_requests,
                settings.auth_rate_limit_window_seconds,
            ),
            f"{auth_prefix}/logout": (
                settings.auth_rate_limit_logout_requests,
                settings.auth_rate_limit_window_seconds,
            ),
        },
    )

    @application.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        _request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=ApiResponse(
                success=False,
                message=str(exc.detail),
                data=None,
            ).model_dump(),
        )

    @application.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=ApiResponse(
                success=False,
                message="Validation error",
                data=exc.errors(),
            ).model_dump(),
        )

    @application.exception_handler(OperationalError)
    async def db_operational_error_handler(
        _request: Request, exc: OperationalError
    ) -> JSONResponse:
        # Most common case during local dev: DB container is stopped.
        return JSONResponse(
            status_code=503,
            content=ApiResponse(
                success=False,
                message="Database unavailable",
                data=None,
            ).model_dump(),
        )

    @application.exception_handler(Exception)
    async def unhandled_exception_handler(
        _request: Request, exc: Exception
    ) -> JSONResponse:
        logger.exception("Unhandled exception", exc_info=exc)
        message = (
            f"{exc.__class__.__name__}: {exc}"
            if settings.debug
            else "Internal server error"
        )
        return JSONResponse(
            status_code=500,
            content=ApiResponse(
                success=False,
                message=message,
                data=None,
            ).model_dump(),
        )

    application.include_router(public_router)
    application.include_router(api_router, prefix=settings.api_prefix)
    return application


app = create_app()
