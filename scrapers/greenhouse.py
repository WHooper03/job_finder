"""Greenhouse job-board scraper."""

from __future__ import annotations

from typing import Any

from .common import DEFAULT_TIMEOUT_SECONDS, extract_salary, location_to_text, make_session, normalized_job


def fetch_greenhouse_jobs(company_config: dict[str, Any], search_text: str | None = None) -> list[dict[str, Any]]:
    board_token = company_config["board_token"]
    company = company_config["company"]
    url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs"
    params = {"content": "true"}

    response = make_session().get(url, params=params, timeout=DEFAULT_TIMEOUT_SECONDS)
    response.raise_for_status()
    payload = response.json()

    jobs: list[dict[str, Any]] = []
    for item in payload.get("jobs", []):
        title = item.get("title") or ""
        if search_text and search_text.lower() not in title.lower():
            continue

        description = item.get("content") or ""
        salary_min, salary_max = extract_salary(description, item.get("metadata"))
        apply_url = item.get("absolute_url") or item.get("internal_job_id") or ""
        location = location_to_text(item.get("location"))

        jobs.append(
            normalized_job(
                platform="greenhouse",
                company=company,
                title=title,
                location=location,
                description=description,
                apply_url=apply_url,
                source_id=item.get("id"),
                salary_min=salary_min,
                salary_max=salary_max,
                posted_at=item.get("first_published") or item.get("updated_at"),
                raw=item,
            )
        )

    return jobs
