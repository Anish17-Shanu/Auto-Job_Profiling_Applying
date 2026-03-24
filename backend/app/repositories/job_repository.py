from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import JobProfile
from app.schemas.domain import JobProfileCreate


class JobRepository:
    def list_for_org(self, session: Session, organization_id: int) -> list[JobProfile]:
        stmt = select(JobProfile).where(JobProfile.organization_id == organization_id).order_by(JobProfile.created_at.desc())
        return list(session.scalars(stmt))

    def create(self, session: Session, organization_id: int, payload: JobProfileCreate) -> JobProfile:
        job = JobProfile(organization_id=organization_id, **payload.model_dump())
        session.add(job)
        session.commit()
        session.refresh(job)
        return job

    def get(self, session: Session, organization_id: int, job_id: int) -> JobProfile | None:
        stmt = select(JobProfile).where(JobProfile.organization_id == organization_id, JobProfile.id == job_id)
        return session.scalar(stmt)

