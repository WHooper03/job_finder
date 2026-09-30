"""Jobicy public remote-jobs API scraper."""

from __future__ import annotations

from typing import Any

from .common import DEFAULT_TIMEOUT_SECONDS, extract_salary, make_session, normalized_job


def fetch_jobicy_jobs(company_config: dict[str, Any], search_text: str | None = None) -> list[dict[str, Any]]:
    url = "https://jobicy.com/api/v2/remote-jobs"
    params: dict[str, Any] = {"count": company_config.get("count", 100)}
    if search_text:
        params["tag"] = search_text.replace(" ", "-").lower()

    response = make_session().get(url, params=params, timeout=DEFAULT_TIMEOUT_SECONDS)
    response.raise_for_status()
    payload = response.json()

    jobs: list[dict[str, Any]] = []
    for item in payload.get("jobs", []):
        description = item.get("jobDescription") or item.get("jobExcerpt") or ""
        salary_min, salary_max = extract_salary(description)
        company = item.get("companyName") or company_config.get("company", "Jobicy")

        jobs.append(
            normalized_job(
                platform="jobicy",
                company=company,
                title=item.get("jobTitle") or "",
                location=item.get("jobGeo") or "",
                description=description,
                apply_url=item.get("url") or "",
                source_id=item.get("id"),
                salary_min=salary_min,
                salary_max=salary_max,
                posted_at=item.get("pubDate"),
                raw=item,
            )
        )

    return jobs
