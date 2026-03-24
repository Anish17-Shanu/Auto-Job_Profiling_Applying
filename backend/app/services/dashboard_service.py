from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.entities import CandidateProfile, JobProfile, PipelineRun, PipelineStatus
from app.repositories.pipeline_repository import PipelineRepository
from app.schemas.domain import DashboardSummary, PipelineRunRead


class DashboardService:
    def __init__(self) -> None:
        self.pipeline_repository = PipelineRepository()

    def get_summary(self, session: Session, organization_id: int) -> DashboardSummary:
        latest_runs = self.pipeline_repository.list_for_org(session, organization_id)[:5]
        avg_score = session.scalar(
            select(func.avg(PipelineRun.score)).where(
                PipelineRun.organization_id == organization_id,
                PipelineRun.status == PipelineStatus.completed,
            )
        )
        return DashboardSummary(
            jobs=session.scalar(select(func.count()).select_from(JobProfile).where(JobProfile.organization_id == organization_id)) or 0,
            candidates=session.scalar(select(func.count()).select_from(CandidateProfile).where(CandidateProfile.organization_id == organization_id)) or 0,
            queued_runs=session.scalar(
                select(func.count()).select_from(PipelineRun).where(
                    PipelineRun.organization_id == organization_id,
                    PipelineRun.status == PipelineStatus.queued,
                )
            )
            or 0,
            completed_runs=session.scalar(
                select(func.count()).select_from(PipelineRun).where(
                    PipelineRun.organization_id == organization_id,
                    PipelineRun.status == PipelineStatus.completed,
                )
            )
            or 0,
            avg_score=round(float(avg_score or 0.0), 2),
            latest_runs=[PipelineRunRead.model_validate(run) for run in latest_runs],
        )

