from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class OrganizationRead(BaseModel):
    id: int
    name: str
    industry: str

    model_config = ConfigDict(from_attributes=True)


class UserRead(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: str
    organization: OrganizationRead

    model_config = ConfigDict(from_attributes=True)


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

    model_config = ConfigDict(from_attributes=True)


class PortalProviderDescriptor(BaseModel):
    provider: str
    label: str
    credential_requirement: str
    ingestion_support: str
    apply_support: str
    notes: str


class JobSourceImportRequest(BaseModel):
    provider: str
    board_token: str | None = None
    company_slug: str | None = None
    keywords: str | None = None
    location: str | None = None
    country: str | None = None
    api_key: str | None = None
    user_agent: str | None = None
    app_id: str | None = None
    app_key: str | None = None
    limit: int = 25


class JobSourceAuthUpdateRequest(BaseModel):
    api_key: str | None = None
    user_agent: str | None = None
    app_id: str | None = None
    app_key: str | None = None


class JobSourceRead(BaseModel):
    id: int
    provider: str
    label: str
    supports_direct_apply: bool
    supports_ingestion: bool
    config: dict[str, Any]
    has_auth_config: bool = False
    last_synced_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExternalJobRead(BaseModel):
    id: int
    source_id: int | None
    provider: str
    source_label: str
    external_job_id: str
    title: str
    company: str
    location: str
    employment_type: str
    description: str
    apply_url: str
    compensation: str | None
    is_remote: bool
    posted_at: datetime | None
    required_skills: list[str]
    preferred_skills: list[str]
    score: float | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobSearchResponse(BaseModel):
    items: list[ExternalJobRead]
    total: int


class MatchGenerationRequest(BaseModel):
    candidate_profile_id: int
    external_job_ids: list[int] = Field(default_factory=list)


class ResumeVersionRead(BaseModel):
    id: int
    match_run_id: int
    candidate_profile_id: int
    tailored_resume: str
    cover_letter: str
    fit_summary: str
    change_summary: str
    approved: bool
    approved_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MatchRunRead(BaseModel):
    id: int
    candidate_profile_id: int
    external_job_id: int
    status: str
    score: float | None
    stage_results: dict[str, Any]
    error_message: str | None
    approval_status: str
    created_at: datetime
    completed_at: datetime | None
    external_job: ExternalJobRead
    resume_version: ResumeVersionRead | None = None

    model_config = ConfigDict(from_attributes=True)


class ResumeApprovalRequest(BaseModel):
    approved: bool


class ApplicationQueueRequest(BaseModel):
    match_run_ids: list[int] = Field(default_factory=list)


class ApplicationSubmitRequest(BaseModel):
    application_target_ids: list[int] = Field(default_factory=list)


class ApplicationTargetRead(BaseModel):
    id: int
    match_run_id: int
    external_job_id: int
    status: str
    apply_mode: str
    external_apply_url: str
    payload_snapshot: dict[str, Any]
    confirmation_code: str | None
    error_message: str | None
    submitted_at: datetime | None
    created_at: datetime
    external_job: ExternalJobRead

    model_config = ConfigDict(from_attributes=True)


class DashboardSummary(BaseModel):
    imported_jobs: int
    candidates: int
    tailored_resumes: int
    approved_resumes: int
    application_targets: int
    submitted_applications: int
    avg_score: float
    latest_matches: list[MatchRunRead]


class WorkerClaimResponse(BaseModel):
    id: int
    candidate: CandidateProfileRead
    external_job: ExternalJobRead


class WorkerCompletionRequest(BaseModel):
    status: str
    score: float | None = None
    stage_results: dict[str, Any] = Field(default_factory=dict)
    error_message: str | None = None
    tailored_resume: str | None = None
    cover_letter: str | None = None
    fit_summary: str | None = None
    change_summary: str | None = None
