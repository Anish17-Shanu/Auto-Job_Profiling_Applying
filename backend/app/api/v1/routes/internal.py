from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import MessageResponse
from app.schemas.domain import WorkerClaimResponse, WorkerCompletionRequest
from app.services.dependency_service import verify_internal_api_key

router = APIRouter(dependencies=[Depends(verify_internal_api_key)])


@router.post("/match-runs/claim", response_model=WorkerClaimResponse | None)
def claim_match_run(session: Session = Depends(get_db)) -> WorkerClaimResponse | None:
    return None


@router.post("/match-runs/{match_run_id}/complete", response_model=MessageResponse)
def complete_match_run(match_run_id: int, payload: WorkerCompletionRequest, session: Session = Depends(get_db)) -> MessageResponse:
    return MessageResponse(message=f"Match run {match_run_id} completion endpoint is reserved for future async workers.")
