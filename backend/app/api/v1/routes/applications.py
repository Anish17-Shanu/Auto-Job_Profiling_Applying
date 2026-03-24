from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.domain import ApplicationQueueRequest, ApplicationSubmitRequest, ApplicationTargetRead
from app.services.dependency_service import get_current_user
from app.services.workflow_service import WorkflowService

router = APIRouter()


@router.get("/targets", response_model=list[ApplicationTargetRead])
def list_application_targets(session: Session = Depends(get_db), user=Depends(get_current_user)) -> list[ApplicationTargetRead]:
    return [
        ApplicationTargetRead.model_validate(target)
        for target in WorkflowService().application_repository.list_for_org(session, user.organization_id)
    ]


@router.post("/targets/queue", response_model=list[ApplicationTargetRead], status_code=status.HTTP_201_CREATED)
def queue_application_targets(
    payload: ApplicationQueueRequest,
    session: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> list[ApplicationTargetRead]:
    return WorkflowService().queue_applications(session, user.organization_id, payload.match_run_ids)


@router.post("/targets/submit", response_model=list[ApplicationTargetRead])
def submit_application_targets(
    payload: ApplicationSubmitRequest,
    session: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> list[ApplicationTargetRead]:
    try:
        return WorkflowService().submit_applications(session, user.organization_id, payload.application_target_ids)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
