"""Shared scraper helpers and normalized job schema."""

from __future__ import annotations

import hashlib
import html
import re
from datetime import datetime, timezone
from typing import Any

import requests


DEFAULT_TIMEOUT_SECONDS = 25
HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    ),
}


def make_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(HEADERS)
    return session


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def clean_html(value: str | None) -> str:
    if not value:
        return ""
    text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", value)
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</p\s*>", "\n\n", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"[ \t]+", " ", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def location_to_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        for key in ("name", "location", "city", "displayName", "formattedAddress"):
            if value.get(key):
                return str(value[key]).strip()
        return ", ".join(str(v).strip() for v in value.values() if v)
    if isinstance(value, list):
        return "; ".join(location_to_text(item) for item in value if item)
    return str(value).strip()


def stable_job_id(platform: str, company: str, source_id: str | int | None, url: str) -> str:
    raw = f"{platform}|{company}|{source_id or ''}|{url}".lower()
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]
    return f"{platform}_{digest}"


def company_abbrev(company: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9 ]+", "", company).strip().lower()
    if not cleaned:
        return "company"
    parts = cleaned.split()
    if len(parts) == 1:
        return parts[0]
    return "".join(part[0] for part in parts if part)


def extract_salary(*values: Any) -> tuple[int | None, int | None]:
    text = " ".join(clean_html(str(value)) for value in values if value)
    if not text:
        return None, None

    matches: list[int] = []
    money_pattern = r"(?:\$|USD\s*)\s*(\d{2,3}(?:,\d{3})+|\d{2,3})(?:\s*(k|K))?"
    shorthand_pattern = r"\b(\d{2,3})\s*(k|K)\b"

    for match in re.finditer(money_pattern, text):
        number_text = match.group(1)
        suffix = match.group(2)
        amount = int(number_text.replace(",", ""))
        if suffix:
            amount *= 1000
        elif "," not in number_text and amount < 1000:
            amount *= 1000
        if 30000 <= amount <= 400000:
            matches.append(amount)

    for match in re.finditer(shorthand_pattern, text):
        amount = int(match.group(1)) * 1000
        if 30000 <= amount <= 400000:
            matches.append(amount)

    if not matches:
        return None, None
    return min(matches), max(matches)


def normalized_job(
    *,
    platform: str,
    company: str,
    title: str,
    location: str,
    description: str,
    apply_url: str,
    source_id: str | int | None = None,
    source_url: str | None = None,
    salary_min: int | None = None,
    salary_max: int | None = None,
    posted_at: str | None = None,
    raw: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "id": stable_job_id(platform, company, source_id, apply_url),
        "source_id": str(source_id or ""),
        "company": company,
        "company_abbrev": company_abbrev(company),
        "title": title.strip(),
        "location": location.strip(),
        "description": clean_html(description),
        "apply_url": apply_url,
        "source_url": source_url or apply_url,
        "ats_platform": platform,
        "salary_min": salary_min,
        "salary_max": salary_max,
        "posted_at": posted_at,
        "scraped_at": now_iso(),
        "status": "new",
        "score": 0,
        "match_reasons": [],
        "unfilled_questions": [],
        "raw": raw or {},
    }
