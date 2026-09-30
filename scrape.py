"""Scrape ATS job boards and write normalized listings to data/jobs.json."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from scrapers import SCRAPERS


ROOT = Path(__file__).resolve().parent
CONFIG_DIR = ROOT / "config"
DATA_DIR = ROOT / "data"
JOBS_PATH = DATA_DIR / "jobs.json"


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def contains_any(text: str, needles: list[str]) -> bool:
    text_lower = text.lower()
    return any(needle.lower() in text_lower for needle in needles)


def normalized_search_text(*values: str) -> str:
    return f" {' '.join(value for value in values if value).lower()} "


def parse_posted_at(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        timestamp = float(value)
        if timestamp > 10_000_000_000:
            timestamp /= 1000
        return datetime.fromtimestamp(timestamp, tz=timezone.utc)

    text = str(value).strip()
    if not text:
        return None
    lowered = text.lower()
    now = datetime.now(timezone.utc)

    if "today" in lowered:
        return now
    if "yesterday" in lowered:
        return None

    relative = re.search(r"(\d+)\s*(minute|minutes|hour|hours|day|days)\s+ago", lowered)
    if relative:
        amount = int(relative.group(1))
        unit = relative.group(2)
        if unit.startswith("minute"):
            return now - timedelta(minutes=amount)
        if unit.startswith("hour"):
            return now - timedelta(hours=amount)
        if unit.startswith("day"):
            return now - timedelta(days=amount)

    cleaned = text.replace("Z", "+00:00")
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%d", "%m/%d/%Y"):
        try:
            parsed = datetime.strptime(cleaned, fmt)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except ValueError:
            continue

    try:
        parsed = datetime.fromisoformat(cleaned)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        return None


def recency_passes(job: dict[str, Any], params: dict[str, Any]) -> bool:
    posted_within_hours = params.get("posted_within_hours")
    if not posted_within_hours:
        return True
    posted = parse_posted_at(job.get("posted_at"))
    if posted is None:
        return False
    age = datetime.now(timezone.utc) - posted
    return timedelta(0) <= age <= timedelta(hours=int(posted_within_hours))


def salary_passes(job: dict[str, Any], params: dict[str, Any]) -> bool:
    minimum = params.get("minimum_salary_usd")
    if not minimum:
        return True
    salary_min = job.get("salary_min")
    salary_max = job.get("salary_max")
    if salary_min is None and salary_max is None:
        return bool(params.get("include_unlisted_salary", True))
    return (salary_max or salary_min or 0) >= int(minimum)


def seniority_passes(job: dict[str, Any], params: dict[str, Any]) -> bool:
    title = job.get("title", "").lower()
    seniority_text = normalized_search_text(
        job.get("description", ""),
        str((job.get("raw") or {}).get("level") or ""),
    )
    excludes = params.get("exclude_title_keywords", [])
    return not contains_any(title, excludes) and not contains_any(seniority_text, excludes)


def location_passes(job: dict[str, Any], params: dict[str, Any]) -> bool:
    location_text = normalized_search_text(job.get("location", ""))
    search_text = normalized_search_text(
        job.get("location", ""),
        job.get("title", ""),
        job.get("description", ""),
    )
    policy = params.get("location_policy", "remote_us_or_local")
    if policy not in {"remote_us_or_local", "remote_us_or_memphis"}:
        return contains_any(search_text, params.get("location_keywords", []))

    local_keywords = params.get("local_area_keywords") or params.get("memphis_keywords", [])
    local_match = contains_any(location_text, local_keywords)
    remote_match = job.get("ats_platform") in {
        "arbeitnow",
        "jobicy",
        "remotejobsfinder",
        "remoteok",
        "remotive",
    } or contains_any(
        search_text,
        params.get("remote_keywords", []),
    )
    us_match = contains_any(location_text, params.get("remote_us_keywords", []))
    return local_match or (remote_match and us_match)


def title_passes(job: dict[str, Any], params: dict[str, Any]) -> bool:
    title = job.get("title", "")
    if contains_any(title, params.get("title_keywords", [])):
        return True

    expanded_title_match = contains_any(title, params.get("expanded_title_keywords", []))
    description_match = contains_any(
        job.get("description", ""),
        params.get("expanded_title_requires_description_keywords", []),
    )
    return expanded_title_match and description_match


def exact_title_passes(job: dict[str, Any], params: dict[str, Any]) -> bool:
    return contains_any(job.get("title", ""), params.get("title_keywords", []))


def score_job(job: dict[str, Any], params: dict[str, Any]) -> tuple[int, list[str]]:
    score = 0
    reasons: list[str] = []
    title = job.get("title", "")
    location = job.get("location", "")
    description = job.get("description", "")

    if exact_title_passes(job, params):
        score += 40
        reasons.append("title match")
    elif title_passes(job, params):
        score += 28
        reasons.append("expanded title + technical description match")
    if location_passes(job, params):
        score += 25
        reasons.append("location match")
    if recency_passes(job, params):
        score += 10
        reasons.append("posted within target window")
    if salary_passes(job, params):
        score += 15
        reasons.append("salary pass")
    if "python" in description.lower() or "sql" in description.lower():
        score += 10
        reasons.append("Python/SQL keyword")
    if any(term in description.lower() for term in ("machine learning", "ml", "etl", "pipeline", "analytics")):
        score += 10
        reasons.append("technical fit keyword")
    if "remote" in f"{title} {location} {description}".lower():
        score += 5
        reasons.append("remote signal")
    if job.get("company_tier") == "preferred":
        score += 10
        reasons.append("preferred industry target")

    return score, reasons


def passes_filters(job: dict[str, Any], params: dict[str, Any]) -> bool:
    return (
        title_passes(job, params)
        and location_passes(job, params)
        and recency_passes(job, params)
        and salary_passes(job, params)
        and seniority_passes(job, params)
    )


def merge_existing_status(jobs: list[dict[str, Any]], existing: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {job["id"]: job for job in existing}
    for job in jobs:
        old = by_id.get(job["id"])
        if not old:
            continue
        for key in (
            "status",
            "notes",
            "unfilled_questions",
            "applied_at",
            "last_reviewed_at",
            "expected_compensation_usd",
            "documents",
        ):
            if key in old:
                job[key] = old[key]
    return jobs


def is_closed_job(job: dict[str, Any]) -> bool:
    return job.get("status") in {"applied", "review_pending", "skipped", "unavailable"}


def dedupe_jobs(jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for job in jobs:
        key = (job.get("apply_url") or job.get("id") or "").lower()
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(job)
    return deduped


def scrape_source(source: dict[str, Any], params: dict[str, Any]) -> list[dict[str, Any]]:
    platform = source["platform"].lower()
    scraper = SCRAPERS[platform]

    if platform in {"arbeitnow", "jobicy", "remotejobsfinder", "remoteok"}:
        jobs: list[dict[str, Any]] = scraper(source)
    elif platform in {"remotive", "workday"}:
        jobs = []
        for search_text in params.get("title_keywords", []):
            jobs.extend(scraper(source, search_text=search_text))
        jobs = dedupe_jobs(jobs)
    else:
        jobs = scraper(source)

    company_tier = source.get("company_tier")
    if company_tier:
        for job in jobs:
            job["company_tier"] = company_tier

    return jobs


def load_sources() -> list[dict[str, Any]]:
    sources_path = CONFIG_DIR / "sources.json"
    if sources_path.exists():
        sources = load_json(sources_path, [])
    else:
        sources = load_json(CONFIG_DIR / "companies.json", [])
    return sorted(
        sources,
        key=lambda source: 0 if source.get("source_type", "company_ats") == "open" else 1,
    )


def run_scrape(
    limit: int | None = None,
    write: bool = True,
    company_limit: int | None = None,
) -> list[dict[str, Any]]:
    params = load_json(CONFIG_DIR / "search_params.json", {})
    sources = load_sources()
    existing = load_json(JOBS_PATH, [])
    all_jobs: list[dict[str, Any]] = []

    active_sources = [source for source in sources if source.get("enabled", True)]
    if company_limit:
        active_sources = active_sources[:company_limit]

    for source in active_sources:
        if not source.get("enabled", True):
            continue
        source_name = source.get("name") or source.get("company") or source["platform"]
        source_type = source.get("source_type", "company_ats")
        print(f"[FETCH] {source_name} ({source_type}/{source['platform']})", flush=True)
        try:
            scraped = scrape_source(source, params)
        except Exception as exc:
            print(f"[WARN] {source_name}: {exc}", flush=True)
            continue

        filtered = []
        for job in scraped:
            if passes_filters(job, params):
                score, reasons = score_job(job, params)
                job["score"] = score
                job["match_reasons"] = reasons
                filtered.append(job)
        all_jobs.extend(filtered)
        print(f"[OK] {source_name}: {len(filtered)} matching jobs", flush=True)

    jobs = merge_existing_status(dedupe_jobs(all_jobs), existing)
    active_jobs = [job for job in jobs if not is_closed_job(job)]
    active_jobs.sort(key=lambda item: (item.get("score", 0), item.get("scraped_at", "")), reverse=True)
    if limit:
        active_jobs = active_jobs[:limit]

    if write:
        closed_existing = [job for job in existing if is_closed_job(job)]
        closed_ids = {job["id"] for job in closed_existing}
        save_json(JOBS_PATH, closed_existing + [job for job in active_jobs if job["id"] not in closed_ids])

    return active_jobs


def print_summary(jobs: list[dict[str, Any]]) -> None:
    if not jobs:
        print("No matching jobs found.")
        return

    print("\nMatching jobs:")
    for index, job in enumerate(jobs, start=1):
        salary = ""
        if job.get("salary_min") or job.get("salary_max"):
            salary = f" | ${job.get('salary_min') or '?'}-${job.get('salary_max') or '?'}"
        print(
            f"{index:>2}. {job['id']} | {job['score']:>3} | "
            f"{job['company']} | {job['title']} | {job.get('location', 'Unknown')}{salary}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape configured ATS job boards.")
    parser.add_argument("--limit", type=int, default=None, help="Limit saved results.")
    parser.add_argument(
        "--source-limit",
        "--company-limit",
        dest="company_limit",
        type=int,
        default=None,
        help="Only scrape the first N enabled sources.",
    )
    parser.add_argument("--no-write", action="store_true", help="Print results without writing data/jobs.json.")
    args = parser.parse_args()

    jobs = run_scrape(limit=args.limit, write=not args.no_write, company_limit=args.company_limit)
    print_summary(jobs)


if __name__ == "__main__":
    main()
