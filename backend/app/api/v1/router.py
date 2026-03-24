from fastapi import APIRouter

from app.api.v1.routes import applications, auth, dashboard, internal, profiles

api_router = APIRouter()
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(profiles.router, prefix="/profiles", tags=["profiles"])
api_router.include_router(applications.router, prefix="/applications", tags=["applications"])
api_router.include_router(internal.router, prefix="/internal", tags=["internal"])

