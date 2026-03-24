from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, Enum as SqlEnum, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class UserRole(str, Enum):
    admin = "admin"
    recruiter = "recruiter"
    hiring_manager = "hiring_manager"


class MatchStatus(str, Enum):
    queued = "queued"
    completed = "completed"
    failed = "failed"


class ResumeApprovalStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class ApplicationStatus(str, Enum):
    draft = "draft"
    ready = "ready"
    submitted = "submitted"
    external_action_required = "external_action_required"
    failed = "failed"


class ApplyMode(str, Enum):
    direct_api = "direct_api"
    external_redirect = "external_redirect"


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    industry: Mapped[str] = mapped_column(String(120), default="Technology")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    users: Mapped[list["User"]] = relationship(back_populates="organization")
    candidate_profiles: Mapped[list["CandidateProfile"]] = relationship(back_populates="organization")
    job_sources: Mapped[list["JobSource"]] = relationship(back_populates="organization")
    external_jobs: Mapped[list["ExternalJob"]] = relationship(back_populates="organization")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    role: Mapped[UserRole] = mapped_column(SqlEnum(UserRole), default=UserRole.admin, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    organization: Mapped["Organization"] = relationship(back_populates="users")


class CandidateProfile(Base):
    __tablename__ = "candidate_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    years_experience: Mapped[int] = mapped_column(Integer, default=0)
    target_role: Mapped[str] = mapped_column(String(180), nullable=False)
    skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    resume_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    organization: Mapped["Organization"] = relationship(back_populates="candidate_profiles")
    match_runs: Mapped[list["MatchRun"]] = relationship(back_populates="candidate_profile")
    resume_versions: Mapped[list["ResumeVersion"]] = relationship(back_populates="candidate_profile")


class JobSource(Base):
    __tablename__ = "job_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    label: Mapped[str] = mapped_column(String(180), nullable=False)
    supports_ingestion: Mapped[bool] = mapped_column(Boolean, default=True)
    supports_direct_apply: Mapped[bool] = mapped_column(Boolean, default=False)
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    auth_config: Mapped[dict] = mapped_column(JSON, default=dict)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    organization: Mapped["Organization"] = relationship(back_populates="job_sources")
    external_jobs: Mapped[list["ExternalJob"]] = relationship(back_populates="source")


class ExternalJob(Base):
    __tablename__ = "external_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("job_sources.id"), nullable=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    source_label: Mapped[str] = mapped_column(String(180), nullable=False)
    external_job_id: Mapped[str] = mapped_column(String(120), nullable=False)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    company: Mapped[str] = mapped_column(String(180), nullable=False)
    location: Mapped[str] = mapped_column(String(180), default="Remote")
    employment_type: Mapped[str] = mapped_column(String(80), default="Unknown")
    description: Mapped[str] = mapped_column(Text, nullable=False)
    apply_url: Mapped[str] = mapped_column(Text, nullable=False)
    compensation: Mapped[str | None] = mapped_column(String(120), nullable=True)
    is_remote: Mapped[bool] = mapped_column(Boolean, default=False)
    posted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    required_skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    preferred_skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    raw_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    organization: Mapped["Organization"] = relationship(back_populates="external_jobs")
    source: Mapped["JobSource | None"] = relationship(back_populates="external_jobs")
    match_runs: Mapped[list["MatchRun"]] = relationship(back_populates="external_job")
    application_targets: Mapped[list["ApplicationTarget"]] = relationship(back_populates="external_job")


class MatchRun(Base):
    __tablename__ = "match_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    candidate_profile_id: Mapped[int] = mapped_column(ForeignKey("candidate_profiles.id"), nullable=False)
    external_job_id: Mapped[int] = mapped_column(ForeignKey("external_jobs.id"), nullable=False)
    status: Mapped[MatchStatus] = mapped_column(SqlEnum(MatchStatus), default=MatchStatus.completed, nullable=False)
    approval_status: Mapped[ResumeApprovalStatus] = mapped_column(
        SqlEnum(ResumeApprovalStatus),
        default=ResumeApprovalStatus.pending,
        nullable=False,
    )
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    stage_results: Mapped[dict] = mapped_column(JSON, default=dict)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    candidate_profile: Mapped["CandidateProfile"] = relationship(back_populates="match_runs")
    external_job: Mapped["ExternalJob"] = relationship(back_populates="match_runs")
    resume_version: Mapped["ResumeVersion | None"] = relationship(back_populates="match_run", uselist=False)
    application_target: Mapped["ApplicationTarget | None"] = relationship(back_populates="match_run", uselist=False)


class ResumeVersion(Base):
    __tablename__ = "resume_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    match_run_id: Mapped[int] = mapped_column(ForeignKey("match_runs.id"), unique=True, nullable=False)
    candidate_profile_id: Mapped[int] = mapped_column(ForeignKey("candidate_profiles.id"), nullable=False)
    tailored_resume: Mapped[str] = mapped_column(Text, nullable=False)
    cover_letter: Mapped[str] = mapped_column(Text, nullable=False)
    fit_summary: Mapped[str] = mapped_column(Text, nullable=False)
    change_summary: Mapped[str] = mapped_column(Text, nullable=False)
    approved: Mapped[bool] = mapped_column(Boolean, default=False)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    match_run: Mapped["MatchRun"] = relationship(back_populates="resume_version")
    candidate_profile: Mapped["CandidateProfile"] = relationship(back_populates="resume_versions")


class ApplicationTarget(Base):
    __tablename__ = "application_targets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    match_run_id: Mapped[int] = mapped_column(ForeignKey("match_runs.id"), unique=True, nullable=False)
    external_job_id: Mapped[int] = mapped_column(ForeignKey("external_jobs.id"), nullable=False)
    status: Mapped[ApplicationStatus] = mapped_column(SqlEnum(ApplicationStatus), default=ApplicationStatus.draft, nullable=False)
    apply_mode: Mapped[ApplyMode] = mapped_column(SqlEnum(ApplyMode), default=ApplyMode.external_redirect, nullable=False)
    external_apply_url: Mapped[str] = mapped_column(Text, nullable=False)
    payload_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    confirmation_code: Mapped[str | None] = mapped_column(String(255), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    match_run: Mapped["MatchRun"] = relationship(back_populates="application_target")
    external_job: Mapped["ExternalJob"] = relationship(back_populates="application_targets")
