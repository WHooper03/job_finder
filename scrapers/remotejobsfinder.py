"""RemoteJobsFinder public jobs API scraper."""

from __future__ import annotations

from typing import Any

from .common import DEFAULT_TIMEOUT_SECONDS, extract_salary, make_session, normalized_job


API_URL = "https://rjf-gateway-prod.globalwork.ai/api/v1/public/jobs"


def _location_text(job: dict[str, Any]) -> str:
    locations = job.get("locations") or []
    parts: list[str] = []
    for location in locations:
        country = location.get("country")
        state = location.get("state")
        city = location.get("city")
        region = location.get("continentRegion")
        pieces = [piece for piece in (city, state, country, region) if piece]
        if pieces:
            parts.append(", ".join(pieces))
    if parts:
        return "; ".join(parts)
    if job.get("location"):
        return str(job["location"])
    return str(job.get("type") or "")


def _salary_range(job: dict[str, Any]) -> tuple[int | None, int | None]:
    compensation = job.get("compensation") or {}
    base_salary = compensation.get("baseSalary") or {}
    if isinstance(base_salary, (int, float)):
        amount = int(base_salary)
        return amount, amount
    if not isinstance(base_salary, dict):
        return extract_salary(job.get("description"))

    salary_min = base_salary.get("min") or base_salary.get("from")
    salary_max = base_salary.get("max") or base_salary.get("to")
    if salary_min or salary_max:
        return salary_min, salary_max
    return extract_salary(job.get("description"))


def _description(job: dict[str, Any]) -> str:
    parts = [
        job.get("description") or "",
        " ".join(job.get("skills") or []),
        " ".join(job.get("commitments") or []),
        str(job.get("level") or ""),
    ]
    return "\n".join(part for part in parts if part)


def fetch_remotejobsfinder_jobs(company_config: dict[str, Any], search_text: str | None = None) -> list[dict[str, Any]]:
    session = make_session()
    searches = [search_text] if search_text else company_config.get("searches") or ["data scientist"]
    limit = int(company_config.get("limit", 30))
    max_pages = int(company_config.get("max_pages", 3))
    jobs: list[dict[str, Any]] = []

    for search in searches:
        for page in range(max_pages):
            params: dict[str, Any] = {
                "limit": limit,
                "skip": page * limit,
                "search": search,
                "jobType": "remote",
            }
            response = session.get(API_URL, params=params, timeout=DEFAULT_TIMEOUT_SECONDS)
            response.raise_for_status()
            payload = response.json()
            items = payload.get("data") or []
            if not items:
                break

            for item in items:
                salary_min, salary_max = _salary_range(item)
                jobs.append(
                    normalized_job(
                        platform="remotejobsfinder",
                        company=item.get("companyName") or company_config.get("company", "RemoteJobsFinder"),
                        title=item.get("title") or "",
                        location=_location_text(item),
                        description=_description(item),
                        apply_url=item.get("jobUrl") or "",
                        source_id=item.get("uuid"),
                        salary_min=salary_min,
                        salary_max=salary_max,
                        posted_at=item.get("createdAt"),
                        raw=item,
                    )
                )

            total = int((payload.get("meta") or {}).get("totalRecords") or 0)
            if total and (page + 1) * limit >= total:
                break

    return jobs
