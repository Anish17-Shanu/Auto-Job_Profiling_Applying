from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class OrganizationRead(BaseModel):
    id: int
    name: str
    industry: str

    model_config = {"from_attributes": True}


class UserRead(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: str
    organization: OrganizationRead

    model_config = {"from_attributes": True}


class JobProfileCreate(BaseModel):
    title: str
    company: str
    location: str = "Remote"
    employment_type: str = "Full-time"
    description: str
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    salary_range: str = "Confidential"


class JobProfileRead(JobProfileCreate):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class CandidateProfileCreate(BaseModel):
    full_name: str
    email: EmailStr
    years_experience: int = 0
    target_role: str
    skills: list[str] = Field(default_factory=list)
    summary: str
    resume_text: str


class CandidateProfileRead(CandidateProfileCreate):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class PipelineRunCreate(BaseModel):
    job_profile_id: int
    candidate_profile_id: int


class PipelineRunRead(BaseModel):
    id: int
    status: str
    score: float | None
    stage_results: dict
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    job_profile_id: int
    candidate_profile_id: int

    model_config = {"from_attributes": True}


class ApplicationDraftRead(BaseModel):
    id: int
    pipeline_run_id: int
    tailored_resume: str
    cover_letter: str
    recruiter_notes: str
    created_at: datetime

    model_config = {"from_attributes": True}


class DashboardSummary(BaseModel):
    jobs: int
    candidates: int
    queued_runs: int
    completed_runs: int
    avg_score: float
    latest_runs: list[PipelineRunRead]


class WorkerClaimResponse(BaseModel):
    id: int
    job: JobProfileRead
    candidate: CandidateProfileRead


class WorkerCompletionRequest(BaseModel):
    status: str
    score: float | None = None
    stage_results: dict = Field(default_factory=dict)
    error_message: str | None = None
    tailored_resume: str | None = None
    cover_letter: str | None = None
    recruiter_notes: str | None = None

