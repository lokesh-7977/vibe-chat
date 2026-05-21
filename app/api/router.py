from fastapi import APIRouter

from app.api.routes.activities import router as activities_router
from app.api.routes.auth import router as auth_router
from app.api.routes.channels import router as channels_router
from app.api.routes.health import router as health_router
from app.api.routes.workspaces import router as workspaces_router

public_router = APIRouter()
public_router.include_router(health_router, tags=["health"])

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(workspaces_router)
api_router.include_router(channels_router)
api_router.include_router(activities_router)
