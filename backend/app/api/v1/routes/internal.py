from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.entities import PipelineStatus
from app.repositories.pipeline_repository import PipelineRepository
from app.schemas.common import MessageResponse
from app.schemas.domain import WorkerClaimResponse, WorkerCompletionRequest
from app.services.dependency_service import verify_internal_api_key

router = APIRouter(dependencies=[Depends(verify_internal_api_key)])


@router.post("/pipeline-runs/claim", response_model=WorkerClaimResponse | None)
def claim_pipeline_run(session: Session = Depends(get_db)) -> WorkerClaimResponse | None:
    run = PipelineRepository().claim_next(session)
    if not run:
        return None
    return WorkerClaimResponse(id=run.id, job=run.job_profile, candidate=run.candidate_profile)


@router.post("/pipeline-runs/{pipeline_run_id}/complete", response_model=MessageResponse)
def complete_pipeline_run(pipeline_run_id: int, payload: WorkerCompletionRequest, session: Session = Depends(get_db)) -> MessageResponse:
    run = PipelineRepository().get(session, pipeline_run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline run not found")
    try:
        status_value = PipelineStatus(payload.status)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported status") from exc

    PipelineRepository().complete(session, run, status_value, payload.score, payload.stage_results, payload.error_message)
    if payload.tailored_resume and payload.cover_letter and payload.recruiter_notes:
        PipelineRepository().upsert_draft(
            session,
            pipeline_run_id,
            payload.tailored_resume,
            payload.cover_letter,
            payload.recruiter_notes,
        )
    return MessageResponse(message="Pipeline run updated")

