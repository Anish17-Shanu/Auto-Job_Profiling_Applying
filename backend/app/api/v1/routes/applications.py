from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.pipeline_repository import PipelineRepository
from app.schemas.domain import ApplicationDraftRead
from app.services.dependency_service import get_current_user

router = APIRouter()


@router.get("/drafts/{pipeline_run_id}", response_model=ApplicationDraftRead)
def get_application_draft(pipeline_run_id: int, session: Session = Depends(get_db), user=Depends(get_current_user)) -> ApplicationDraftRead:
    run = PipelineRepository().get(session, pipeline_run_id)
    if not run or run.organization_id != user.organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline run not found")
    draft = PipelineRepository().get_draft(session, pipeline_run_id)
    if not draft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not available yet")
    return ApplicationDraftRead.model_validate(draft)

