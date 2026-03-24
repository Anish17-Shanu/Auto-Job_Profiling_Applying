from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.job_repository import JobRepository
from app.repositories.pipeline_repository import PipelineRepository
from app.schemas.domain import CandidateProfileCreate, CandidateProfileRead, JobProfileCreate, JobProfileRead, PipelineRunCreate, PipelineRunRead
from app.services.dependency_service import get_current_user

router = APIRouter()


@router.get("/jobs", response_model=list[JobProfileRead])
def list_jobs(session: Session = Depends(get_db), user=Depends(get_current_user)) -> list[JobProfileRead]:
    return [JobProfileRead.model_validate(item) for item in JobRepository().list_for_org(session, user.organization_id)]


@router.post("/jobs", response_model=JobProfileRead, status_code=status.HTTP_201_CREATED)
def create_job(payload: JobProfileCreate, session: Session = Depends(get_db), user=Depends(get_current_user)) -> JobProfileRead:
    return JobProfileRead.model_validate(JobRepository().create(session, user.organization_id, payload))


@router.get("/candidates", response_model=list[CandidateProfileRead])
def list_candidates(session: Session = Depends(get_db), user=Depends(get_current_user)) -> list[CandidateProfileRead]:
    return [CandidateProfileRead.model_validate(item) for item in CandidateRepository().list_for_org(session, user.organization_id)]


@router.post("/candidates", response_model=CandidateProfileRead, status_code=status.HTTP_201_CREATED)
def create_candidate(payload: CandidateProfileCreate, session: Session = Depends(get_db), user=Depends(get_current_user)) -> CandidateProfileRead:
    return CandidateProfileRead.model_validate(CandidateRepository().create(session, user.organization_id, payload))


@router.get("/pipeline-runs", response_model=list[PipelineRunRead])
def list_pipeline_runs(session: Session = Depends(get_db), user=Depends(get_current_user)) -> list[PipelineRunRead]:
    return [PipelineRunRead.model_validate(item) for item in PipelineRepository().list_for_org(session, user.organization_id)]


@router.post("/pipeline-runs", response_model=PipelineRunRead, status_code=status.HTTP_201_CREATED)
def create_pipeline_run(payload: PipelineRunCreate, session: Session = Depends(get_db), user=Depends(get_current_user)) -> PipelineRunRead:
    job = JobRepository().get(session, user.organization_id, payload.job_profile_id)
    candidate = CandidateRepository().get(session, user.organization_id, payload.candidate_profile_id)
    if not job or not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job or candidate not found")
    run = PipelineRepository().create(session, user.organization_id, job.id, candidate.id)
    return PipelineRunRead.model_validate(run)

