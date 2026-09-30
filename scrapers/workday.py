"""Workday public career-site scraper."""

from __future__ import annotations

from typing import Any

from .common import DEFAULT_TIMEOUT_SECONDS, extract_salary, location_to_text, make_session, normalized_job


def _base(company_config: dict[str, Any]) -> str:
    tenant = company_config["tenant"]
    region = company_config.get("region", "wd1")
    return f"https://{tenant}.{region}.myworkdayjobs.com"


def _apply_url(company_config: dict[str, Any], external_path: str) -> str:
    base = _base(company_config)
    site = company_config["site"]
    if external_path.startswith("/"):
        return f"{base}/{site}{external_path}"
    return f"{base}/{site}/{external_path}"


def _detail(company_config: dict[str, Any], external_path: str) -> dict[str, Any]:
    if not external_path:
        return {}
    tenant = company_config["tenant"]
    site = company_config["site"]
    url = f"{_base(company_config)}/wday/cxs/{tenant}/{site}/job{external_path}"
    response = make_session().get(url, timeout=DEFAULT_TIMEOUT_SECONDS)
    if response.status_code >= 400:
        return {}
    return response.json()


def fetch_workday_jobs(company_config: dict[str, Any], search_text: str | None = None) -> list[dict[str, Any]]:
    tenant = company_config["tenant"]
    site = company_config["site"]
    company = company_config["company"]
    url = f"{_base(company_config)}/wday/cxs/{tenant}/{site}/jobs"
    session = make_session()

    jobs: list[dict[str, Any]] = []
    limit = int(company_config.get("limit", 20))
    max_pages = int(company_config.get("max_pages", 2))

    for page in range(max_pages):
        offset = page * limit
        payload = {
            "appliedFacets": {},
            "limit": limit,
            "offset": offset,
            "searchText": search_text or "",
        }
        response = session.post(url, json=payload, timeout=DEFAULT_TIMEOUT_SECONDS)
        response.raise_for_status()
        data = response.json()
        postings = data.get("jobPostings") or data.get("jobs") or []
        if not postings:
            break

        for item in postings:
            external_path = item.get("externalPath") or item.get("jobPostingId") or ""
            listing_title = item.get("title") or ""
            if search_text and search_text.lower() not in listing_title.lower():
                continue

            detail = _detail(company_config, external_path if str(external_path).startswith("/") else f"/{external_path}")
            posting_info = detail.get("jobPostingInfo") or detail
            title = posting_info.get("title") or listing_title

            description = posting_info.get("jobDescription") or posting_info.get("description") or ""
            location = location_to_text(
                posting_info.get("location")
                or posting_info.get("locationsText")
                or item.get("locationsText")
                or item.get("location")
            )
            apply_url = posting_info.get("externalUrl") or _apply_url(
                company_config,
                external_path if str(external_path).startswith("/") else f"/{external_path}",
            )
            salary_min, salary_max = extract_salary(description, posting_info.get("compensation"))

            jobs.append(
                normalized_job(
                    platform="workday",
                    company=company,
                    title=title,
                    location=location,
                    description=description,
                    apply_url=apply_url,
                    source_id=item.get("bulletFields") or external_path,
                    salary_min=salary_min,
                    salary_max=salary_max,
                    posted_at=posting_info.get("startDate") or item.get("postedOn"),
                    raw={"listing": item, "detail": detail},
                )
            )

        total = int(data.get("total", len(jobs)))
        if offset + limit >= total:
            break

    return jobs
