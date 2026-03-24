from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.common import HealthResponse
from app.schemas.domain import UserRead
from app.services.auth_service import AuthService
from app.services.dependency_service import get_current_user

router = APIRouter()


@router.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, session: Session = Depends(get_db)) -> TokenResponse:
    token = AuthService().authenticate(session, payload.email, payload.password)
    return TokenResponse(access_token=token)


@router.get("/auth/me", response_model=UserRead)
def current_user(user=Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(user)


@router.get("/health", response_model=HealthResponse)
def healthcheck() -> HealthResponse:
    return HealthResponse(status="ok", timestamp=datetime.utcnow())

