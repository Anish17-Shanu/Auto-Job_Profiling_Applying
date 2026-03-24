from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.domain import DashboardSummary
from app.services.dashboard_service import DashboardService
from app.services.dependency_service import get_current_user

router = APIRouter()


@router.get("/summary", response_model=DashboardSummary)
def summary(session: Session = Depends(get_db), user=Depends(get_current_user)) -> DashboardSummary:
    return DashboardService().get_summary(session, user.organization_id)

