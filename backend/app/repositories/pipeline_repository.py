from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.entities import (
    ApplicationStatus,
    ApplicationTarget,
    ApplyMode,
    MatchRun,
    MatchStatus,
    ResumeApprovalStatus,
    ResumeVersion,
)


class MatchRepository:
    def list_for_org(self, session: Session, organization_id: int) -> list[MatchRun]:
        stmt = (
            select(MatchRun)
            .where(MatchRun.organization_id == organization_id)
            .options(joinedload(MatchRun.external_job), joinedload(MatchRun.resume_version))
            .order_by(MatchRun.created_at.desc())
        )
        return list(session.scalars(stmt).unique())

    def create_completed(
        self,
        session: Session,
        organization_id: int,
        candidate_profile_id: int,
        external_job_id: int,
        score: float,
        stage_results: dict,
    ) -> MatchRun:
        run = MatchRun(
            organization_id=organization_id,
            candidate_profile_id=candidate_profile_id,
            external_job_id=external_job_id,
            status=MatchStatus.completed,
            score=score,
            stage_results=stage_results,
            completed_at=datetime.utcnow(),
        )
        session.add(run)
        session.flush()
        return run

    def get(self, session: Session, match_run_id: int) -> MatchRun | None:
        stmt = (
            select(MatchRun)
            .where(MatchRun.id == match_run_id)
            .options(
                joinedload(MatchRun.external_job),
                joinedload(MatchRun.resume_version),
                joinedload(MatchRun.application_target),
            )
        )
        return session.scalar(stmt)

    def set_approval(self, session: Session, run: MatchRun, approved: bool) -> MatchRun:
        run.approval_status = ResumeApprovalStatus.approved if approved else ResumeApprovalStatus.rejected
        if run.resume_version:
            run.resume_version.approved = approved
            run.resume_version.approved_at = datetime.utcnow() if approved else None
        session.commit()
        session.refresh(run)
        return run

    def upsert_resume_version(
        self,
        session: Session,
        run: MatchRun,
        candidate_profile_id: int,
        tailored_resume: str,
        cover_letter: str,
        fit_summary: str,
        change_summary: str,
    ) -> ResumeVersion:
        existing = session.scalar(select(ResumeVersion).where(ResumeVersion.match_run_id == run.id))
        if existing:
            existing.tailored_resume = tailored_resume
            existing.cover_letter = cover_letter
            existing.fit_summary = fit_summary
            existing.change_summary = change_summary
            resume = existing
        else:
            resume = ResumeVersion(
                match_run_id=run.id,
                candidate_profile_id=candidate_profile_id,
                tailored_resume=tailored_resume,
                cover_letter=cover_letter,
                fit_summary=fit_summary,
                change_summary=change_summary,
            )
            session.add(resume)
        session.flush()
        return resume


class ApplicationRepository:
    def list_for_org(self, session: Session, organization_id: int) -> list[ApplicationTarget]:
        stmt = (
            select(ApplicationTarget)
            .where(ApplicationTarget.organization_id == organization_id)
            .options(joinedload(ApplicationTarget.external_job))
            .order_by(ApplicationTarget.created_at.desc())
        )
        return list(session.scalars(stmt).unique())

    def upsert_target(
        self,
        session: Session,
        *,
        organization_id: int,
        match_run_id: int,
        external_job_id: int,
        apply_mode: ApplyMode,
        external_apply_url: str,
        payload_snapshot: dict,
        status: ApplicationStatus,
    ) -> ApplicationTarget:
        existing = session.scalar(select(ApplicationTarget).where(ApplicationTarget.match_run_id == match_run_id))
        if existing:
            existing.apply_mode = apply_mode
            existing.external_apply_url = external_apply_url
            existing.payload_snapshot = payload_snapshot
            existing.status = status
            target = existing
        else:
            target = ApplicationTarget(
                organization_id=organization_id,
                match_run_id=match_run_id,
                external_job_id=external_job_id,
                apply_mode=apply_mode,
                external_apply_url=external_apply_url,
                payload_snapshot=payload_snapshot,
                status=status,
            )
            session.add(target)
        session.flush()
        return target

    def get_many(self, session: Session, organization_id: int, application_ids: list[int]) -> list[ApplicationTarget]:
        if not application_ids:
            return []
        stmt = (
            select(ApplicationTarget)
            .where(ApplicationTarget.organization_id == organization_id, ApplicationTarget.id.in_(application_ids))
            .options(joinedload(ApplicationTarget.external_job), joinedload(ApplicationTarget.match_run).joinedload(MatchRun.resume_version))
        )
        return list(session.scalars(stmt).unique())

    def mark_submitted(self, session: Session, target: ApplicationTarget, confirmation_code: str | None = None) -> ApplicationTarget:
        target.status = ApplicationStatus.submitted
        target.confirmation_code = confirmation_code
        target.error_message = None
        target.submitted_at = datetime.utcnow()
        session.flush()
        return target

    def mark_external_action_required(self, session: Session, target: ApplicationTarget) -> ApplicationTarget:
        target.status = ApplicationStatus.external_action_required
        target.submitted_at = datetime.utcnow()
        session.flush()
        return target

    def mark_failed(self, session: Session, target: ApplicationTarget, message: str) -> ApplicationTarget:
        target.status = ApplicationStatus.failed
        target.error_message = message
        target.submitted_at = datetime.utcnow()
        session.flush()
        return target
