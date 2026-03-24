from datetime import datetime

import httpx
from sqlalchemy.orm import Session

from app.ai.matching import compute_fit_score, identify_skill_gaps
from app.models.entities import ApplicationStatus, ApplyMode, MatchRun
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.job_repository import ExternalJobRepository, JobSourceRepository
from app.repositories.pipeline_repository import ApplicationRepository, MatchRepository
from app.schemas.domain import (
    ApplicationTargetRead,
    CandidateProfileRead,
    ExternalJobRead,
    JobSearchResponse,
    MatchRunRead,
)
from app.services.portal_service import PortalService


class WorkflowService:
    def __init__(self) -> None:
        self.portal_service = PortalService()
        self.source_repository = JobSourceRepository()
        self.job_repository = ExternalJobRepository()
        self.candidate_repository = CandidateRepository()
        self.match_repository = MatchRepository()
        self.application_repository = ApplicationRepository()

    def import_jobs(
        self,
        session: Session,
        organization_id: int,
        *,
        provider: str,
        board_token: str | None,
        company_slug: str | None,
        keywords: str | None,
        location: str | None,
        country: str | None,
        limit: int,
        auth_config: dict | None = None,
    ) -> list[ExternalJobRead]:
        imported = self.portal_service.import_jobs(
            provider,
            board_token=board_token,
            company_slug=company_slug,
            keywords=keywords,
            location=location,
            country=country,
            limit=limit,
            auth_config=auth_config,
        )
        source = self.source_repository.get_or_create(
            session,
            organization_id,
            provider=imported.provider,
            label=imported.label,
            config=imported.config,
            supports_direct_apply=imported.supports_direct_apply,
            auth_config=auth_config,
        )
        jobs = self.job_repository.upsert_many(session, organization_id, source, imported.jobs)
        self.source_repository.mark_synced(session, source)
        session.commit()
        return [ExternalJobRead.model_validate(job) for job in jobs]

    def search_jobs(
        self,
        session: Session,
        organization_id: int,
        *,
        query: str | None,
        provider: str | None,
        location: str | None,
        remote_only: bool,
        candidate_profile_id: int | None,
    ) -> JobSearchResponse:
        jobs = self.job_repository.list_for_org(session, organization_id)
        candidate = (
            self.candidate_repository.get(session, organization_id, candidate_profile_id) if candidate_profile_id else None
        )

        filtered = []
        for job in jobs:
            haystack = " ".join([job.title, job.company, job.location, job.description]).lower()
            if query and query.lower() not in haystack:
                continue
            if provider and job.provider != provider:
                continue
            if location and location.lower() not in job.location.lower():
                continue
            if remote_only and not job.is_remote:
                continue
            score = None
            if candidate:
                score = compute_fit_score(
                    required_skills=job.required_skills,
                    preferred_skills=job.preferred_skills,
                    candidate_skills=candidate.skills,
                    years_experience=candidate.years_experience,
                )
            payload = ExternalJobRead.model_validate(job).model_copy(update={"score": score})
            filtered.append(payload)

        filtered.sort(key=lambda item: (item.score is not None, item.score or 0, item.posted_at or datetime.min), reverse=True)
        return JobSearchResponse(items=filtered, total=len(filtered))

    def generate_matches(
        self,
        session: Session,
        organization_id: int,
        *,
        candidate_profile_id: int,
        external_job_ids: list[int],
    ) -> list[MatchRunRead]:
        candidate = self.candidate_repository.get(session, organization_id, candidate_profile_id)
        if not candidate:
            raise ValueError("Candidate profile not found.")
        jobs = self.job_repository.get_many(session, organization_id, external_job_ids)
        results: list[MatchRunRead] = []
        for job in jobs:
            score = compute_fit_score(job.required_skills, job.preferred_skills, candidate.skills, candidate.years_experience)
            skill_gaps = identify_skill_gaps(job.required_skills, candidate.skills)
            fit_summary = (
                f"{candidate.full_name} matches {len(job.required_skills) - len(skill_gaps)} of {max(len(job.required_skills), 1)} "
                f"required skills for {job.title} at {job.company}. Estimated fit score: {score}%."
            )
            change_summary = (
                f"Emphasized {', '.join(candidate.skills[:5]) or 'core transferable experience'} and highlighted "
                f"{', '.join(job.required_skills[:4]) or 'role requirements'} to align with the job description."
            )
            tailored_resume = (
                f"{candidate.full_name}\n"
                f"Targeting: {job.title} at {job.company}\n\n"
                f"Summary\n{candidate.summary}\n\n"
                f"Why this role fits\n"
                f"- {fit_summary}\n"
                f"- Key matched skills: {', '.join([skill for skill in candidate.skills if skill.lower() in {s.lower() for s in job.required_skills}][:6]) or 'Transferable analytical and delivery skills'}\n"
                f"- Experience: {candidate.years_experience} years\n\n"
                f"Core Skills\n- " + "\n- ".join(candidate.skills) + "\n\n"
                f"Base Resume\n{candidate.resume_text}"
            )
            cover_letter = (
                f"Dear Hiring Team,\n\n"
                f"I am excited to apply for the {job.title} role at {job.company}. "
                f"My background in {', '.join(candidate.skills[:4])} and {candidate.years_experience} years of experience "
                f"align with your needs in {job.location}.\n\n"
                f"I would bring immediate value in {', '.join(job.required_skills[:3]) or 'core role execution'} and "
                f"would welcome the chance to contribute.\n\n"
                f"Sincerely,\n{candidate.full_name}"
            )
            stage_results = {
                "matching": {"fit_score": score, "skill_gaps": skill_gaps},
                "tailoring": {"fit_summary": fit_summary, "change_summary": change_summary},
            }
            run = self.match_repository.create_completed(
                session,
                organization_id=organization_id,
                candidate_profile_id=candidate.id,
                external_job_id=job.id,
                score=score,
                stage_results=stage_results,
            )
            self.match_repository.upsert_resume_version(
                session,
                run,
                candidate_profile_id=candidate.id,
                tailored_resume=tailored_resume,
                cover_letter=cover_letter,
                fit_summary=fit_summary,
                change_summary=change_summary,
            )
            session.commit()
            results.append(MatchRunRead.model_validate(self.match_repository.get(session, run.id)))
        return results

    def queue_applications(self, session: Session, organization_id: int, match_run_ids: list[int]) -> list[ApplicationTargetRead]:
        queued: list[ApplicationTargetRead] = []
        for match_run_id in match_run_ids:
            run = self.match_repository.get(session, match_run_id)
            if not run or run.organization_id != organization_id or not run.resume_version:
                continue
            if not run.resume_version.approved:
                continue
            apply_mode = ApplyMode.external_redirect
            status = ApplicationStatus.ready
            if run.external_job.provider == "greenhouse" and run.external_job.source and run.external_job.source.auth_config.get("api_key"):
                apply_mode = ApplyMode.direct_api
            target = self.application_repository.upsert_target(
                session,
                organization_id=organization_id,
                match_run_id=run.id,
                external_job_id=run.external_job_id,
                apply_mode=apply_mode,
                external_apply_url=run.external_job.apply_url,
                payload_snapshot={
                    "candidate_email": run.candidate_profile.email,
                    "tailored_resume": run.resume_version.tailored_resume,
                    "cover_letter": run.resume_version.cover_letter,
                },
                status=status,
            )
            session.commit()
            queued.append(ApplicationTargetRead.model_validate(target))
        return queued

    def submit_applications(self, session: Session, organization_id: int, application_ids: list[int]) -> list[ApplicationTargetRead]:
        results: list[ApplicationTargetRead] = []
        targets = self.application_repository.get_many(session, organization_id, application_ids)
        for target in targets:
            try:
                if target.apply_mode == ApplyMode.direct_api:
                    self._submit_greenhouse(target.match_run, target)
                    self.application_repository.mark_submitted(session, target, confirmation_code="greenhouse-api-submitted")
                else:
                    self.application_repository.mark_external_action_required(session, target)
                session.commit()
            except Exception as exc:
                self.application_repository.mark_failed(session, target, str(exc))
                session.commit()
            results.append(ApplicationTargetRead.model_validate(target))
        return results

    def _submit_greenhouse(self, run: MatchRun, target) -> None:
        source = run.external_job.source
        if not source:
            raise ValueError("Missing source configuration for Greenhouse application.")
        api_key = source.auth_config.get("api_key")
        board_token = source.config.get("board_token")
        if not api_key or not board_token:
            raise ValueError("Greenhouse direct apply requires both board token and API key.")
        candidate = run.candidate_profile
        resume = run.resume_version
        if not candidate or not resume:
            raise ValueError("Candidate and approved tailored resume are required before apply.")
        url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs/{run.external_job.external_job_id}"
        payload = {
            "first_name": candidate.full_name.split(" ")[0],
            "last_name": " ".join(candidate.full_name.split(" ")[1:]) or "Candidate",
            "email": candidate.email,
            "resume_text": resume.tailored_resume,
            "cover_letter_text": resume.cover_letter,
        }
        with httpx.Client(timeout=20) as client:
            response = client.post(url, auth=(api_key, ""), json=payload)
            response.raise_for_status()
