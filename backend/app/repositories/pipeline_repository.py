from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.entities import ApplicationDraft, PipelineRun, PipelineStatus


class PipelineRepository:
    def list_for_org(self, session: Session, organization_id: int) -> list[PipelineRun]:
        stmt = (
            select(PipelineRun)
            .where(PipelineRun.organization_id == organization_id)
            .options(joinedload(PipelineRun.job_profile), joinedload(PipelineRun.candidate_profile))
            .order_by(PipelineRun.created_at.desc())
        )
        return list(session.scalars(stmt).unique())

    def create(self, session: Session, organization_id: int, job_profile_id: int, candidate_profile_id: int) -> PipelineRun:
        run = PipelineRun(
            organization_id=organization_id,
            job_profile_id=job_profile_id,
            candidate_profile_id=candidate_profile_id,
            status=PipelineStatus.queued,
            stage_results={},
        )
        session.add(run)
        session.commit()
        session.refresh(run)
        return run

    def claim_next(self, session: Session) -> PipelineRun | None:
        run = session.scalar(
            select(PipelineRun)
            .where(PipelineRun.status == PipelineStatus.queued)
            .order_by(PipelineRun.created_at.asc())
            .options(joinedload(PipelineRun.job_profile), joinedload(PipelineRun.candidate_profile))
        )
        if not run:
            return None
        run.status = PipelineStatus.running
        run.started_at = datetime.utcnow()
        session.commit()
        session.refresh(run)
        return run

    def get(self, session: Session, run_id: int) -> PipelineRun | None:
        stmt = (
            select(PipelineRun)
            .where(PipelineRun.id == run_id)
            .options(joinedload(PipelineRun.job_profile), joinedload(PipelineRun.candidate_profile), joinedload(PipelineRun.application_draft))
        )
        return session.scalar(stmt)

    def complete(self, session: Session, run: PipelineRun, status: PipelineStatus, score: float | None, stage_results: dict, error_message: str | None) -> PipelineRun:
        run.status = status
        run.score = score
        run.stage_results = stage_results
        run.error_message = error_message
        run.completed_at = datetime.utcnow()
        session.commit()
        session.refresh(run)
        return run

    def upsert_draft(self, session: Session, run_id: int, tailored_resume: str, cover_letter: str, recruiter_notes: str) -> ApplicationDraft:
        existing = session.scalar(select(ApplicationDraft).where(ApplicationDraft.pipeline_run_id == run_id))
        if existing:
            existing.tailored_resume = tailored_resume
            existing.cover_letter = cover_letter
            existing.recruiter_notes = recruiter_notes
            draft = existing
        else:
            draft = ApplicationDraft(
                pipeline_run_id=run_id,
                tailored_resume=tailored_resume,
                cover_letter=cover_letter,
                recruiter_notes=recruiter_notes,
            )
            session.add(draft)
        session.commit()
        session.refresh(draft)
        return draft

    def get_draft(self, session: Session, run_id: int) -> ApplicationDraft | None:
        return session.scalar(select(ApplicationDraft).where(ApplicationDraft.pipeline_run_id == run_id))

