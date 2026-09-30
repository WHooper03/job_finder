"""Arbeitnow public job-board API scraper."""

from __future__ import annotations

from typing import Any

from .common import DEFAULT_TIMEOUT_SECONDS, extract_salary, make_session, normalized_job


def fetch_arbeitnow_jobs(company_config: dict[str, Any], search_text: str | None = None) -> list[dict[str, Any]]:
    session = make_session()
    pages = int(company_config.get("pages", 3))
    jobs: list[dict[str, Any]] = []

    for page in range(1, pages + 1):
        response = session.get(
            "https://www.arbeitnow.com/api/job-board-api",
            params={"page": page},
            timeout=DEFAULT_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json()

        for item in payload.get("data", []):
            title = item.get("title") or ""
            if search_text and search_text.lower() not in title.lower():
                continue

            description = item.get("description") or ""
            salary_min, salary_max = extract_salary(description)
            company = item.get("company_name") or company_config.get("company", "Arbeitnow")

            jobs.append(
                normalized_job(
                    platform="arbeitnow",
                    company=company,
                    title=title,
                    location=item.get("location") or ("Remote" if item.get("remote") else ""),
                    description=description,
                    apply_url=item.get("url") or "",
                    source_id=item.get("slug"),
                    salary_min=salary_min,
                    salary_max=salary_max,
                    posted_at=item.get("created_at"),
                    raw=item,
                )
            )

        if not payload.get("data"):
            break

    return jobs
