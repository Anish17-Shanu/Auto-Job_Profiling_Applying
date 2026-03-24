from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.models.entities import CandidateProfile, JobProfile, Organization, User, UserRole


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

    has_job = session.scalar(select(JobProfile.id).where(JobProfile.organization_id == organization.id))
    if not has_job:
        session.add(
            JobProfile(
                organization_id=organization.id,
                title="Senior Product Analyst",
                company="Northstar Talent",
                location="Remote",
                employment_type="Full-time",
                description="Lead analytics initiatives and translate business questions into measurable product insights.",
                required_skills=["SQL", "Python", "A/B Testing", "Stakeholder Management", "Analytics"],
                preferred_skills=["dbt", "Looker", "Product Strategy"],
                salary_range="$110k-$140k",
            )
        )

    has_candidate = session.scalar(select(CandidateProfile.id).where(CandidateProfile.organization_id == organization.id))
    if not has_candidate:
        session.add(
            CandidateProfile(
                organization_id=organization.id,
                full_name="Avery Singh",
                email="avery.singh@example.com",
                years_experience=6,
                target_role="Product Analyst",
                skills=["SQL", "Python", "Looker", "Experimentation", "Communication"],
                summary="Product analyst focused on growth analytics, funnel optimization, and stakeholder-facing insight delivery.",
                resume_text="Built SQL pipelines, Python notebooks, executive dashboards, and experimentation workflows.",
            )
        )

    session.commit()

