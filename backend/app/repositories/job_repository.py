from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import ExternalJob, JobSource


class JobSourceRepository:
    def list_for_org(self, session: Session, organization_id: int) -> list[JobSource]:
        stmt = select(JobSource).where(JobSource.organization_id == organization_id).order_by(JobSource.created_at.desc())
        return list(session.scalars(stmt))

    def get_or_create(
        self,
        session: Session,
        organization_id: int,
        *,
        provider: str,
        label: str,
        config: dict,
        supports_direct_apply: bool,
        auth_config: dict | None = None,
    ) -> JobSource:
        stmt = select(JobSource).where(
            JobSource.organization_id == organization_id,
            JobSource.provider == provider,
            JobSource.label == label,
        )
        source = session.scalar(stmt)
        if source:
            source.config = config
            source.supports_direct_apply = supports_direct_apply
            source.supports_ingestion = True
            if auth_config is not None:
                source.auth_config = auth_config
        else:
            source = JobSource(
                organization_id=organization_id,
                provider=provider,
                label=label,
                supports_ingestion=True,
                supports_direct_apply=supports_direct_apply,
                config=config,
                auth_config=auth_config or {},
            )
            session.add(source)
        session.flush()
        return source

    def mark_synced(self, session: Session, source: JobSource) -> None:
        source.last_synced_at = datetime.utcnow()
        session.flush()

    def get(self, session: Session, organization_id: int, source_id: int) -> JobSource | None:
        stmt = select(JobSource).where(JobSource.organization_id == organization_id, JobSource.id == source_id)
        return session.scalar(stmt)

    def update_auth_config(self, session: Session, source: JobSource, auth_config: dict) -> JobSource:
        source.auth_config = auth_config
        session.commit()
        session.refresh(source)
        return source


class ExternalJobRepository:
    def upsert_many(self, session: Session, organization_id: int, source: JobSource | None, jobs: list[dict]) -> list[ExternalJob]:
        persisted: list[ExternalJob] = []
        for payload in jobs:
            stmt = select(ExternalJob).where(
                ExternalJob.organization_id == organization_id,
                ExternalJob.provider == payload["provider"],
                ExternalJob.external_job_id == payload["external_job_id"],
            )
            existing = session.scalar(stmt)
            if existing:
                existing.source_id = source.id if source else existing.source_id
                existing.source_label = payload["source_label"]
                existing.title = payload["title"]
                existing.company = payload["company"]
                existing.location = payload["location"]
                existing.employment_type = payload["employment_type"]
                existing.description = payload["description"]
                existing.apply_url = payload["apply_url"]
                existing.compensation = payload.get("compensation")
                existing.is_remote = payload.get("is_remote", False)
                existing.posted_at = payload.get("posted_at")
                existing.required_skills = payload.get("required_skills", [])
                existing.preferred_skills = payload.get("preferred_skills", [])
                existing.raw_payload = payload.get("raw_payload", {})
                job = existing
            else:
                job = ExternalJob(
                    organization_id=organization_id,
                    source_id=source.id if source else None,
                    **payload,
                )
                session.add(job)
            session.flush()
            persisted.append(job)
        session.commit()
        for job in persisted:
            session.refresh(job)
        return persisted

    def list_for_org(self, session: Session, organization_id: int) -> list[ExternalJob]:
        stmt = select(ExternalJob).where(ExternalJob.organization_id == organization_id).order_by(ExternalJob.updated_at.desc())
        return list(session.scalars(stmt))

    def get_many(self, session: Session, organization_id: int, job_ids: list[int]) -> list[ExternalJob]:
        if not job_ids:
            return []
        stmt = select(ExternalJob).where(ExternalJob.organization_id == organization_id, ExternalJob.id.in_(job_ids))
        return list(session.scalars(stmt))
