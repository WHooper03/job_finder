"""Lever job-board scraper."""

from __future__ import annotations

from typing import Any

from .common import DEFAULT_TIMEOUT_SECONDS, clean_html, extract_salary, location_to_text, make_session, normalized_job


def _description(item: dict[str, Any]) -> str:
    if item.get("descriptionPlain"):
        return item["descriptionPlain"]
    parts = [item.get("description", "")]
    for list_name in ("lists", "additional"):
        for section in item.get(list_name, []) or []:
            parts.append(section.get("text", ""))
            for content in section.get("content", []) or []:
                parts.append(content.get("text", ""))
    return clean_html("\n\n".join(part for part in parts if part))


def fetch_lever_jobs(company_config: dict[str, Any], search_text: str | None = None) -> list[dict[str, Any]]:
    site = company_config["site"]
    company = company_config["company"]
    url = f"https://api.lever.co/v0/postings/{site}"
    params = {"mode": "json"}

    response = make_session().get(url, params=params, timeout=DEFAULT_TIMEOUT_SECONDS)
    response.raise_for_status()
    payload = response.json()

    jobs: list[dict[str, Any]] = []
    for item in payload:
        title = item.get("text") or ""
        if search_text and search_text.lower() not in title.lower():
            continue

        categories = item.get("categories") or {}
        location = location_to_text(categories.get("location") or item.get("workplaceType"))
        description = _description(item)
        salary_min, salary_max = extract_salary(description, item.get("salaryRange"))
        apply_url = item.get("hostedUrl") or item.get("applyUrl") or ""

        jobs.append(
            normalized_job(
                platform="lever",
                company=company,
                title=title,
                location=location,
                description=description,
                apply_url=apply_url,
                source_id=item.get("id"),
                salary_min=salary_min,
                salary_max=salary_max,
                posted_at=item.get("createdAt") or item.get("updatedAt"),
                raw=item,
            )
        )

    return jobs
