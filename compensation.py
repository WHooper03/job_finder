"""Suggested compensation for application forms (manual entry)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
DEFAULT_PROFILE_PATH = ROOT / "config" / "profile.json"


def load_profile(profile_path: Path | None = None) -> dict[str, Any]:
    path = profile_path or DEFAULT_PROFILE_PATH
    if not path.exists():
        raise SystemExit(
            f"Missing {path}. Copy config/profile.example.json to config/profile.json and edit it."
        )
    return json.loads(path.read_text(encoding="utf-8"))


def choose_expected_compensation(job: dict[str, Any] | None, profile: dict[str, Any]) -> int | None:
    defaults = profile.get("application_defaults", {})
    strategy = defaults.get("compensation_strategy", {})
    current_salary = int(strategy.get("current_salary_usd", 75000))
    bridge_salary = int(strategy.get("if_current_salary_in_range_ask_usd", 80000))
    fallback = defaults.get("salary_expectation_usd")

    if not job:
        return fallback

    salary_min = job.get("salary_min")
    salary_max = job.get("salary_max")
    if salary_min is None and salary_max is None:
        return fallback

    if salary_min is None:
        salary_min = salary_max
    if salary_max is None:
        salary_max = salary_min
    salary_min = int(salary_min)
    salary_max = int(salary_max)

    if salary_min <= current_salary <= salary_max:
        return min(max(bridge_salary, salary_min), salary_max)

    if salary_min > bridge_salary:
        score = int(job.get("score") or 0)
        spread = max(salary_max - salary_min, 0)
        if score >= 85:
            percentile = 0.4
        elif score >= 70:
            percentile = 0.3
        else:
            percentile = 0.2
        target = salary_min + round(spread * percentile)
        return int(round(target / 1000) * 1000)

    return max(bridge_salary, current_salary)
