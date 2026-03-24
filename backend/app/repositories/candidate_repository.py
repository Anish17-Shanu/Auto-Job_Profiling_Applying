from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import CandidateProfile
from app.schemas.domain import CandidateProfileCreate


class CandidateRepository:
    def list_for_org(self, session: Session, organization_id: int) -> list[CandidateProfile]:
        stmt = (
            select(CandidateProfile)
            .where(CandidateProfile.organization_id == organization_id)
            .order_by(CandidateProfile.created_at.desc())
        )
        return list(session.scalars(stmt))

    def create(self, session: Session, organization_id: int, payload: CandidateProfileCreate) -> CandidateProfile:
        candidate = CandidateProfile(organization_id=organization_id, **payload.model_dump())
        session.add(candidate)
        session.commit()
        session.refresh(candidate)
        return candidate

    def get(self, session: Session, organization_id: int, candidate_id: int) -> CandidateProfile | None:
        stmt = select(CandidateProfile).where(
            CandidateProfile.organization_id == organization_id,
            CandidateProfile.id == candidate_id,
        )
        return session.scalar(stmt)

