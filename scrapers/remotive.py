"""Remotive public remote-jobs API scraper."""

from __future__ import annotations

from typing import Any

from .common import DEFAULT_TIMEOUT_SECONDS, extract_salary, make_session, normalized_job


def fetch_remotive_jobs(company_config: dict[str, Any], search_text: str | None = None) -> list[dict[str, Any]]:
    url = "https://remotive.com/api/remote-jobs"
    params = {"search": search_text} if search_text else {}

    response = make_session().get(url, params=params, timeout=DEFAULT_TIMEOUT_SECONDS)
    response.raise_for_status()
    payload = response.json()

    jobs: list[dict[str, Any]] = []
    for item in payload.get("jobs", []):
        title = item.get("title") or ""
        description = item.get("description") or ""
        salary_min, salary_max = extract_salary(item.get("salary"), description)
        company = item.get("company_name") or company_config.get("company", "Remotive")

        jobs.append(
            normalized_job(
                platform="remotive",
                company=company,
                title=title,
                location=item.get("candidate_required_location") or "",
                description=description,
                apply_url=item.get("url") or "",
                source_id=item.get("id"),
                salary_min=salary_min,
                salary_max=salary_max,
                posted_at=item.get("publication_date"),
                raw=item,
            )
        )

    return jobs
