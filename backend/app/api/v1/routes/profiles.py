from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.job_repository import JobSourceRepository
from app.schemas.domain import (
    CandidateProfileCreate,
    CandidateProfileRead,
    ExternalJobRead,
    JobSearchResponse,
    JobSourceAuthUpdateRequest,
    JobSourceImportRequest,
    JobSourceRead,
    MatchGenerationRequest,
    MatchRunRead,
    PortalProviderDescriptor,
    ResumeApprovalRequest,
)
from app.services.dependency_service import get_current_user
from app.services.portal_service import PortalService
from app.services.workflow_service import WorkflowService

router = APIRouter()


@router.get("/providers", response_model=list[PortalProviderDescriptor])
def list_providers() -> list[PortalProviderDescriptor]:
    return PortalService().list_supported_providers()


@router.get("/sources", response_model=list[JobSourceRead])
def list_sources(session: Session = Depends(get_db), user=Depends(get_current_user)) -> list[JobSourceRead]:
    return [
        JobSourceRead.model_validate(source).model_copy(update={"has_auth_config": bool(source.auth_config)})
        for source in JobSourceRepository().list_for_org(session, user.organization_id)
    ]


@router.post("/sources/{source_id}/auth", response_model=JobSourceRead)
def update_source_auth(
    source_id: int,
    payload: JobSourceAuthUpdateRequest,
    session: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> JobSourceRead:
    repository = JobSourceRepository()
    source = repository.get(session, user.organization_id, source_id)
    if not source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
    auth_config = {
        key: value
        for key, value in {
            "api_key": payload.api_key,
            "user_agent": payload.user_agent,
            "app_id": payload.app_id,
            "app_key": payload.app_key,
        }.items()
        if value
    }
    updated = repository.update_auth_config(session, source, auth_config)
    return JobSourceRead.model_validate(updated).model_copy(update={"has_auth_config": bool(updated.auth_config)})


@router.post("/sources/import", response_model=list[ExternalJobRead], status_code=status.HTTP_201_CREATED)
def import_source_jobs(payload: JobSourceImportRequest, session: Session = Depends(get_db), user=Depends(get_current_user)) -> list[ExternalJobRead]:
    try:
        return WorkflowService().import_jobs(
            session,
            user.organization_id,
            provider=payload.provider,
            board_token=payload.board_token,
            company_slug=payload.company_slug,
            keywords=payload.keywords,
            location=payload.location,
            country=payload.country,
            limit=payload.limit,
            auth_config={
                key: value
                for key, value in {
                    "api_key": payload.api_key,
                    "user_agent": payload.user_agent,
                    "app_id": payload.app_id,
                    "app_key": payload.app_key,
                }.items()
                if value
            }
            or None,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Import failed: {exc}") from exc


@router.get("/candidates", response_model=list[CandidateProfileRead])
def list_candidates(session: Session = Depends(get_db), user=Depends(get_current_user)) -> list[CandidateProfileRead]:
    return [CandidateProfileRead.model_validate(item) for item in CandidateRepository().list_for_org(session, user.organization_id)]


@router.post("/candidates", response_model=CandidateProfileRead, status_code=status.HTTP_201_CREATED)
def create_candidate(payload: CandidateProfileCreate, session: Session = Depends(get_db), user=Depends(get_current_user)) -> CandidateProfileRead:
    return CandidateProfileRead.model_validate(CandidateRepository().create(session, user.organization_id, payload))


@router.get("/jobs", response_model=JobSearchResponse)
def list_jobs(
    query: str | None = Query(default=None),
    provider: str | None = Query(default=None),
    location: str | None = Query(default=None),
    remote_only: bool = Query(default=False),
    candidate_profile_id: int | None = Query(default=None),
    session: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> JobSearchResponse:
    return WorkflowService().search_jobs(
        session,
        user.organization_id,
        query=query,
        provider=provider,
        location=location,
        remote_only=remote_only,
        candidate_profile_id=candidate_profile_id,
    )


@router.get("/matches", response_model=list[MatchRunRead])
def list_matches(session: Session = Depends(get_db), user=Depends(get_current_user)) -> list[MatchRunRead]:
    return [
        MatchRunRead.model_validate(item)
        for item in WorkflowService().match_repository.list_for_org(session, user.organization_id)
    ]


@router.post("/matches/generate", response_model=list[MatchRunRead], status_code=status.HTTP_201_CREATED)
def generate_matches(payload: MatchGenerationRequest, session: Session = Depends(get_db), user=Depends(get_current_user)) -> list[MatchRunRead]:
    try:
        return WorkflowService().generate_matches(
            session,
            user.organization_id,
            candidate_profile_id=payload.candidate_profile_id,
            external_job_ids=payload.external_job_ids,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/matches/{match_run_id}/approval", response_model=MatchRunRead)
def approve_match_resume(
    match_run_id: int,
    payload: ResumeApprovalRequest,
    session: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> MatchRunRead:
    run = WorkflowService().match_repository.get(session, match_run_id)
    if not run or run.organization_id != user.organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match run not found")
    updated = WorkflowService().match_repository.set_approval(session, run, payload.approved)
    return MatchRunRead.model_validate(updated)
