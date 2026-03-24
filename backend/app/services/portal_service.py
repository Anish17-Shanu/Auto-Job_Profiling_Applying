import html
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import httpx

from app.schemas.domain import PortalProviderDescriptor


COMMON_SKILLS = {
    "python",
    "sql",
    "fastapi",
    "react",
    "typescript",
    "javascript",
    "node",
    "docker",
    "kubernetes",
    "aws",
    "azure",
    "gcp",
    "machine learning",
    "data analysis",
    "product analytics",
    "excel",
    "power bi",
    "tableau",
    "communication",
    "stakeholder management",
    "a/b testing",
    "experimentation",
    "api",
    "postgresql",
    "java",
    "spring",
    "go",
    "rust",
}


@dataclass
class ImportedSource:
    provider: str
    label: str
    config: dict[str, Any]
    supports_direct_apply: bool
    jobs: list[dict[str, Any]]


def strip_html(value: str | None) -> str:
    if not value:
        return ""
    text = re.sub(r"<[^>]+>", " ", html.unescape(value))
    return re.sub(r"\s+", " ", text).strip()


def detect_skills(text: str) -> list[str]:
    normalized = text.lower()
    return sorted([skill.title() for skill in COMMON_SKILLS if skill in normalized])


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


class PortalService:
    def list_supported_providers(self) -> list[PortalProviderDescriptor]:
        return [
            PortalProviderDescriptor(
                provider="greenhouse",
                label="Greenhouse Boards API",
                credential_requirement="None for ingestion; per-board API key required for direct apply",
                ingestion_support="Public JSON job board import by board token",
                apply_support="Direct API apply is supported when a board-level API key is provided",
                notes="Best free/public portal to start with because listings are openly readable.",
            ),
            PortalProviderDescriptor(
                provider="lever",
                label="Lever Postings API",
                credential_requirement="None for public ingestion",
                ingestion_support="Public postings import by company slug",
                apply_support="Application generally redirects to the portal-hosted apply page",
                notes="Great for free ingestion, but bulk auto-submit usually requires an assisted flow.",
            ),
            PortalProviderDescriptor(
                provider="remotive",
                label="Remotive Remote Jobs",
                credential_requirement="None",
                ingestion_support="Keyword-based public remote jobs feed import",
                apply_support="Redirect-based apply flow to employer listing",
                notes="Useful free remote-job source for broad discovery.",
            ),
            PortalProviderDescriptor(
                provider="adzuna",
                label="Adzuna Jobs API",
                credential_requirement="Adzuna app_id and app_key",
                ingestion_support="Authenticated job search by keywords, location, and country",
                apply_support="Redirect-based apply flow to the source ad",
                notes="Good authenticated aggregator source with broad coverage.",
            ),
            PortalProviderDescriptor(
                provider="usajobs",
                label="USAJOBS Search API",
                credential_requirement="USAJOBS API key and request email/User-Agent",
                ingestion_support="Authenticated federal job search",
                apply_support="Redirect-based apply flow to USAJOBS announcement/apply page",
                notes="Useful for federal roles; official search requires specific request headers.",
            ),
        ]

    def import_jobs(
        self,
        provider: str,
        *,
        board_token: str | None,
        company_slug: str | None,
        keywords: str | None,
        location: str | None,
        country: str | None,
        limit: int,
        auth_config: dict[str, Any] | None = None,
    ) -> ImportedSource:
        if provider == "greenhouse":
            return self._import_greenhouse(board_token=board_token, limit=limit)
        if provider == "lever":
            return self._import_lever(company_slug=company_slug, limit=limit)
        if provider == "remotive":
            return self._import_remotive(keywords=keywords, location=location, limit=limit)
        if provider == "adzuna":
            return self._import_adzuna(keywords=keywords, location=location, country=country, limit=limit, auth_config=auth_config or {})
        if provider == "usajobs":
            return self._import_usajobs(keywords=keywords, location=location, limit=limit, auth_config=auth_config or {})
        raise ValueError(f"Unsupported provider: {provider}")

    def _import_greenhouse(self, *, board_token: str | None, limit: int) -> ImportedSource:
        if not board_token:
            raise ValueError("Greenhouse imports require a board token.")
        url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true"
        with httpx.Client(timeout=20) as client:
            response = client.get(url)
            response.raise_for_status()
            payload = response.json()
        jobs = []
        for item in payload.get("jobs", [])[:limit]:
            description = strip_html(item.get("content"))
            jobs.append(
                {
                    "provider": "greenhouse",
                    "source_label": f"Greenhouse:{board_token}",
                    "external_job_id": str(item["id"]),
                    "title": item.get("title", "Untitled role"),
                    "company": board_token.replace("-", " ").title(),
                    "location": item.get("location", {}).get("name", "Unknown"),
                    "employment_type": "Unknown",
                    "description": description,
                    "apply_url": item.get("absolute_url") or "",
                    "compensation": None,
                    "is_remote": "remote" in description.lower() or "remote" in item.get("location", {}).get("name", "").lower(),
                    "posted_at": parse_datetime(item.get("updated_at")),
                    "required_skills": detect_skills(description),
                    "preferred_skills": [],
                    "raw_payload": item,
                }
            )
        return ImportedSource(
            provider="greenhouse",
            label=f"Greenhouse:{board_token}",
            config={"board_token": board_token},
            supports_direct_apply=True,
            jobs=jobs,
        )

    def _import_lever(self, *, company_slug: str | None, limit: int) -> ImportedSource:
        if not company_slug:
            raise ValueError("Lever imports require a company slug.")
        urls = [
            f"https://api.lever.co/v0/postings/{company_slug}?mode=json",
            f"https://api.eu.lever.co/v0/postings/{company_slug}?mode=json",
        ]
        payload: list[dict[str, Any]] | None = None
        for url in urls:
            with httpx.Client(timeout=20) as client:
                response = client.get(url)
            if response.status_code == 200:
                payload = response.json()
                break
        if payload is None:
            raise ValueError("Lever import failed for the supplied company slug.")
        jobs = []
        for item in payload[:limit]:
            description = strip_html(item.get("descriptionPlain") or item.get("description"))
            categories = item.get("categories") or {}
            jobs.append(
                {
                    "provider": "lever",
                    "source_label": f"Lever:{company_slug}",
                    "external_job_id": item.get("id") or item.get("hostedUrl") or item.get("text"),
                    "title": item.get("text", "Untitled role"),
                    "company": company_slug.replace("-", " ").title(),
                    "location": categories.get("location") or "Unknown",
                    "employment_type": categories.get("commitment") or "Unknown",
                    "description": description,
                    "apply_url": item.get("hostedUrl") or item.get("applyUrl") or "",
                    "compensation": None,
                    "is_remote": "remote" in description.lower() or "remote" in (categories.get("location") or "").lower(),
                    "posted_at": parse_datetime(item.get("createdAt")),
                    "required_skills": detect_skills(description),
                    "preferred_skills": [],
                    "raw_payload": item,
                }
            )
        return ImportedSource(
            provider="lever",
            label=f"Lever:{company_slug}",
            config={"company_slug": company_slug},
            supports_direct_apply=False,
            jobs=jobs,
        )

    def _import_remotive(self, *, keywords: str | None, location: str | None, limit: int) -> ImportedSource:
        query = keywords or ""
        with httpx.Client(timeout=20) as client:
            response = client.get("https://remotive.com/api/remote-jobs", params={"search": query})
            response.raise_for_status()
            payload = response.json()
        jobs = []
        for item in payload.get("jobs", [])[:limit]:
            description = strip_html(item.get("description"))
            candidate_location = item.get("candidate_required_location") or "Remote"
            if location and location.lower() not in candidate_location.lower():
                continue
            jobs.append(
                {
                    "provider": "remotive",
                    "source_label": f"Remotive:{query or 'all'}",
                    "external_job_id": str(item["id"]),
                    "title": item.get("title", "Untitled role"),
                    "company": item.get("company_name", "Unknown"),
                    "location": candidate_location,
                    "employment_type": item.get("job_type", "Unknown"),
                    "description": description,
                    "apply_url": item.get("url") or item.get("job_url") or "",
                    "compensation": item.get("salary"),
                    "is_remote": True,
                    "posted_at": parse_datetime(item.get("publication_date")),
                    "required_skills": detect_skills(description),
                    "preferred_skills": [],
                    "raw_payload": item,
                }
            )
        return ImportedSource(
            provider="remotive",
            label=f"Remotive:{query or 'all'}",
            config={"keywords": query, "location": location},
            supports_direct_apply=False,
            jobs=jobs,
        )

    def _import_adzuna(
        self,
        *,
        keywords: str | None,
        location: str | None,
        country: str | None,
        limit: int,
        auth_config: dict[str, Any],
    ) -> ImportedSource:
        app_id = auth_config.get("app_id")
        app_key = auth_config.get("app_key")
        if not app_id or not app_key:
            raise ValueError("Adzuna imports require app_id and app_key.")
        market = (country or "us").lower()
        with httpx.Client(timeout=20) as client:
            response = client.get(
                f"https://api.adzuna.com/v1/api/jobs/{market}/search/1",
                params={
                    "app_id": app_id,
                    "app_key": app_key,
                    "results_per_page": limit,
                    "what": keywords or "",
                    "where": location or "",
                    "content-type": "application/json",
                },
            )
            response.raise_for_status()
            payload = response.json()
        jobs = []
        for item in payload.get("results", []):
            description = strip_html(item.get("description"))
            jobs.append(
                {
                    "provider": "adzuna",
                    "source_label": f"Adzuna:{market}",
                    "external_job_id": str(item.get("id") or item.get("redirect_url")),
                    "title": item.get("title", "Untitled role"),
                    "company": (item.get("company") or {}).get("display_name", "Unknown"),
                    "location": (item.get("location") or {}).get("display_name", "Unknown"),
                    "employment_type": item.get("contract_type") or item.get("contract_time") or "Unknown",
                    "description": description,
                    "apply_url": item.get("redirect_url") or item.get("adref") or "",
                    "compensation": format_salary(item.get("salary_min"), item.get("salary_max")),
                    "is_remote": "remote" in description.lower() or "remote" in ((item.get("location") or {}).get("display_name", "").lower()),
                    "posted_at": parse_datetime(item.get("created")),
                    "required_skills": detect_skills(description),
                    "preferred_skills": [],
                    "raw_payload": item,
                }
            )
        return ImportedSource(
            provider="adzuna",
            label=f"Adzuna:{market}",
            config={"keywords": keywords, "location": location, "country": market},
            supports_direct_apply=False,
            jobs=jobs,
        )

    def _import_usajobs(
        self,
        *,
        keywords: str | None,
        location: str | None,
        limit: int,
        auth_config: dict[str, Any],
    ) -> ImportedSource:
        api_key = auth_config.get("api_key")
        user_agent = auth_config.get("user_agent")
        if not api_key or not user_agent:
            raise ValueError("USAJOBS imports require api_key and user_agent email.")
        with httpx.Client(timeout=20) as client:
            response = client.get(
                "https://data.usajobs.gov/api/search",
                params={
                    "Keyword": keywords or "",
                    "LocationName": location or "",
                    "ResultsPerPage": limit,
                },
                headers={
                    "Host": "data.usajobs.gov",
                    "User-Agent": user_agent,
                    "Authorization-Key": api_key,
                },
            )
            response.raise_for_status()
            payload = response.json()
        items = (
            payload.get("SearchResult", {})
            .get("SearchResultItems", [])
        )
        jobs = []
        for item in items:
            descriptor = item.get("MatchedObjectDescriptor", {})
            description = strip_html(descriptor.get("UserArea", {}).get("Details", {}).get("JobSummary"))
            position_id = descriptor.get("PositionID") or descriptor.get("PositionID")
            jobs.append(
                {
                    "provider": "usajobs",
                    "source_label": "USAJOBS",
                    "external_job_id": str(position_id or descriptor.get("PositionURI")),
                    "title": descriptor.get("PositionTitle", "Untitled role"),
                    "company": descriptor.get("OrganizationName", "USAJOBS"),
                    "location": ", ".join(
                        [loc.get("LocationName", "") for loc in descriptor.get("PositionLocation", []) if loc.get("LocationName")]
                    )
                    or "Unknown",
                    "employment_type": descriptor.get("PositionSchedule", [{}])[0].get("Name", "Unknown"),
                    "description": description,
                    "apply_url": descriptor.get("PositionURI") or "",
                    "compensation": format_salary(descriptor.get("PositionRemuneration", [{}])[0].get("MinimumRange"), descriptor.get("PositionRemuneration", [{}])[0].get("MaximumRange")),
                    "is_remote": "remote" in description.lower(),
                    "posted_at": parse_datetime(descriptor.get("PublicationStartDate")),
                    "required_skills": detect_skills(description),
                    "preferred_skills": [],
                    "raw_payload": item,
                }
            )
        return ImportedSource(
            provider="usajobs",
            label="USAJOBS",
            config={"keywords": keywords, "location": location},
            supports_direct_apply=False,
            jobs=jobs,
        )


def format_salary(min_salary: Any, max_salary: Any) -> str | None:
    if min_salary is None and max_salary is None:
        return None
    if min_salary is None:
        return f"Up to {max_salary}"
    if max_salary is None:
        return f"From {min_salary}"
    return f"{min_salary} - {max_salary}"
