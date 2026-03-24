from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.entities import ApplicationStatus, ApplicationTarget, CandidateProfile, ExternalJob, MatchRun, ResumeApprovalStatus
from app.repositories.pipeline_repository import MatchRepository
from app.schemas.domain import DashboardSummary, MatchRunRead


class DashboardService:
    def __init__(self) -> None:
        self.match_repository = MatchRepository()

    def get_summary(self, session: Session, organization_id: int) -> DashboardSummary:
        latest_matches = self.match_repository.list_for_org(session, organization_id)[:5]
        avg_score = session.scalar(select(func.avg(MatchRun.score)).where(MatchRun.organization_id == organization_id))
        return DashboardSummary(
            imported_jobs=session.scalar(
                select(func.count()).select_from(ExternalJob).where(ExternalJob.organization_id == organization_id)
            )
            or 0,
            candidates=session.scalar(
                select(func.count()).select_from(CandidateProfile).where(CandidateProfile.organization_id == organization_id)
            )
            or 0,
            tailored_resumes=session.scalar(
                select(func.count()).select_from(MatchRun).where(MatchRun.organization_id == organization_id)
            )
            or 0,
            approved_resumes=session.scalar(
                select(func.count()).select_from(MatchRun).where(
                    MatchRun.organization_id == organization_id,
                    MatchRun.approval_status == ResumeApprovalStatus.approved,
                )
            )
            or 0,
            application_targets=session.scalar(
                select(func.count()).select_from(ApplicationTarget).where(ApplicationTarget.organization_id == organization_id)
            )
            or 0,
            submitted_applications=session.scalar(
                select(func.count()).select_from(ApplicationTarget).where(
                    ApplicationTarget.organization_id == organization_id,
                    ApplicationTarget.status == ApplicationStatus.submitted,
                )
            )
            or 0,
            avg_score=round(float(avg_score or 0.0), 2),
            latest_matches=[MatchRunRead.model_validate(run) for run in latest_matches],
        )
