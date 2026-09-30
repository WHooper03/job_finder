"""Ashby job-board scraper."""

from __future__ import annotations

from typing import Any

from .common import DEFAULT_TIMEOUT_SECONDS, extract_salary, location_to_text, make_session, normalized_job


def fetch_ashby_jobs(company_config: dict[str, Any], search_text: str | None = None) -> list[dict[str, Any]]:
    board = company_config["board"]
    company = company_config["company"]
    url = f"https://api.ashbyhq.com/posting-api/job-board/{board}/published-jobs"

    session = make_session()
    response = session.get(url, timeout=DEFAULT_TIMEOUT_SECONDS)
    if response.status_code in {404, 405}:
        response = session.post(url, json={}, timeout=DEFAULT_TIMEOUT_SECONDS)
    response.raise_for_status()
    payload = response.json()

    if isinstance(payload, list):
        items = payload
    else:
        items = payload.get("jobs") or payload.get("jobPostings") or []
    jobs: list[dict[str, Any]] = []
    for item in items:
        title = item.get("title") or item.get("name") or ""
        if search_text and search_text.lower() not in title.lower():
            continue

        description = item.get("descriptionHtml") or item.get("description") or item.get("department") or ""
        location = location_to_text(
            item.get("locationName")
            or item.get("location")
            or item.get("locations")
            or item.get("workplaceType")
        )
        apply_url = (
            item.get("jobUrl")
            or item.get("applyUrl")
            or item.get("externalLink")
            or f"https://jobs.ashbyhq.com/{board}/{item.get('id', '')}"
        )
        salary_min, salary_max = extract_salary(description, item.get("compensation"))

        jobs.append(
            normalized_job(
                platform="ashby",
                company=company,
                title=title,
                location=location,
                description=description,
                apply_url=apply_url,
                source_id=item.get("id"),
                salary_min=salary_min,
                salary_max=salary_max,
                posted_at=item.get("publishedAt") or item.get("publishedDate") or item.get("createdAt"),
                raw=item,
            )
        )

    return jobs
