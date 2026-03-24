from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.models.entities import CandidateProfile, Organization, User, UserRole


def seed_demo_data(session: Session) -> None:
    organization = session.scalar(select(Organization).where(Organization.name == "AutoJob Demo Org"))
    if not organization:
        organization = Organization(name="AutoJob Demo Org", industry="HR Technology")
        session.add(organization)
        session.commit()
        session.refresh(organization)

    admin = session.scalar(select(User).where(User.email == settings.demo_admin_email))
    if not admin:
        session.add(
            User(
                organization_id=organization.id,
                full_name="Platform Admin",
                email=settings.demo_admin_email,
                role=UserRole.admin,
                password_hash=hash_password(settings.demo_admin_password),
            )
        )

    candidate = session.scalar(select(CandidateProfile).where(CandidateProfile.email == "avery.singh@example.com"))
    if not candidate:
        session.add(
            CandidateProfile(
                organization_id=organization.id,
                full_name="Avery Singh",
                email="avery.singh@example.com",
                years_experience=6,
                target_role="Product Analyst",
                skills=["SQL", "Python", "Looker", "Experimentation", "Stakeholder Management"],
                summary="Product analyst focused on growth analytics, experimentation, and stakeholder-facing insight delivery.",
                resume_text=(
                    "Experience: Built SQL pipelines, Python notebooks, dashboarding workflows, and decision support for product teams.\n"
                    "Achievements: Improved funnel conversion analysis, experimentation velocity, and stakeholder reporting quality."
                ),
            )
        )

    session.commit()
