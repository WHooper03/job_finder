"""Remote OK public API scraper."""

from __future__ import annotations

from typing import Any

from .common import DEFAULT_TIMEOUT_SECONDS, clean_html, make_session, normalized_job


def fetch_remoteok_jobs(company_config: dict[str, Any], search_text: str | None = None) -> list[dict[str, Any]]:
    session = make_session()
    response = session.get("https://remoteok.com/api", timeout=DEFAULT_TIMEOUT_SECONDS)
    response.raise_for_status()
    payload = response.json()

    jobs: list[dict[str, Any]] = []
    for item in payload:
        if not isinstance(item, dict) or not item.get("id"):
            continue

        title = item.get("position") or ""
        tags = " ".join(item.get("tags") or [])
        if search_text and search_text.lower() not in f"{title} {tags}".lower():
            continue

        company = item.get("company") or company_config.get("company", "Remote OK")
        description = clean_html(item.get("description") or "")
        jobs.append(
            normalized_job(
                platform="remoteok",
                company=company,
                title=title,
                location=item.get("location") or "",
                description=description,
                apply_url=item.get("apply_url") or item.get("url") or "",
                source_id=item.get("id") or item.get("slug"),
                salary_min=item.get("salary_min") or None,
                salary_max=item.get("salary_max") or None,
                posted_at=item.get("epoch") or item.get("date"),
                raw=item,
            )
        )

    return jobs
