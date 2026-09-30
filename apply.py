"""Open a job application in the browser for manual review and submission."""

from __future__ import annotations

import argparse
import json
import webbrowser
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from compensation import choose_expected_compensation, load_profile


ROOT = Path(__file__).resolve().parent
CONFIG_DIR = ROOT / "config"
DATA_DIR = ROOT / "data"
APPLICATIONS_DIR = ROOT / "applications"
JOBS_PATH = DATA_DIR / "jobs.json"


def load_jobs() -> list[dict[str, Any]]:
    if not JOBS_PATH.exists():
        raise SystemExit("No data/jobs.json found. Run `python scrape.py` first.")
    return json.loads(JOBS_PATH.read_text(encoding="utf-8"))


def save_jobs(jobs: list[dict[str, Any]]) -> None:
    JOBS_PATH.write_text(json.dumps(jobs, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def find_job(jobs: list[dict[str, Any]], job_id: str | None, company: str | None) -> dict[str, Any]:
    if job_id:
        matches = [job for job in jobs if job["id"] == job_id or job["id"].startswith(job_id)]
    elif company:
        company_lower = company.lower()
        matches = [job for job in jobs if company_lower in job.get("company", "").lower()]
    else:
        raise SystemExit("Provide either --job-id or --company.")

    if not matches:
        raise SystemExit("No matching job found.")
    if len(matches) > 1:
        print("Multiple matching jobs:")
        for job in matches:
            print(f"- {job['id']} | {job['company']} | {job['title']} | {job.get('location', '')}")
        raise SystemExit("Use --job-id to choose one exact job.")
    return matches[0]


def document_paths(
    job: dict[str, Any], resume_override: str | None, cover_letter_override: str | None
) -> tuple[Path, Path | None]:
    abbrev = job.get("company_abbrev") or "company"
    app_dir = APPLICATIONS_DIR / abbrev
    resume_pdf = Path(resume_override) if resume_override else app_dir / f"{abbrev}_r.pdf"
    cover_letter_pdf = Path(cover_letter_override) if cover_letter_override else app_dir / f"{abbrev}_cl.pdf"
    return resume_pdf, cover_letter_pdf


def verify_documents(resume_pdf: Path, cover_letter_pdf: Path | None) -> None:
    missing: list[str] = []
    if not resume_pdf.exists():
        missing.append(str(resume_pdf))
    if cover_letter_pdf and not cover_letter_pdf.exists():
        missing.append(str(cover_letter_pdf))
    if missing:
        raise SystemExit(
            "Missing tailored PDF(s):\n"
            + "\n".join(f"- {path}" for path in missing)
            + "\n\nGenerate and compile the tailored resume/cover letter before running apply.py."
        )


def update_job_status(
    jobs: list[dict[str, Any]],
    target: dict[str, Any],
    *,
    submitted: bool,
    expected_compensation_usd: int | None,
    resume_pdf: Path,
    cover_letter_pdf: Path | None,
) -> None:
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    for job in jobs:
        if job["id"] != target["id"]:
            continue
        job["status"] = "applied" if submitted else "review_pending"
        job["unfilled_questions"] = []
        job["last_reviewed_at"] = now
        if submitted:
            job["applied_at"] = now
        job["expected_compensation_usd"] = expected_compensation_usd
        job["documents"] = {
            "resume_pdf": str(resume_pdf),
            "cover_letter_pdf": str(cover_letter_pdf) if cover_letter_pdf else None,
        }
        break


def print_compensation_hint(job: dict[str, Any], profile: dict[str, Any]) -> int | None:
    expected = choose_expected_compensation(job, profile)
    salary_min = job.get("salary_min")
    salary_max = job.get("salary_max")
    if salary_min is not None or salary_max is not None:
        lo = f"${int(salary_min):,}" if salary_min is not None else "?"
        hi = f"${int(salary_max):,}" if salary_max is not None else "?"
        print(f"Posted range: {lo} – {hi}")
    if expected is not None:
        print(f"Suggested compensation to enter: ${expected:,} (from config/profile.json strategy)")
    else:
        print("No salary on posting and no default in profile — decide compensation manually.")
    return expected


def main() -> None:
    parser = argparse.ArgumentParser(description="Open the job application URL for manual completion.")
    parser.add_argument("--job-id", help="Exact or prefix match for a job id in data/jobs.json.")
    parser.add_argument("--company", help="Company-name match if only one scraped job exists for that company.")
    parser.add_argument("--resume", help="Override path to tailored resume PDF.")
    parser.add_argument("--cover-letter", help="Override path to tailored cover letter PDF.")
    parser.add_argument(
        "--no-open",
        action="store_true",
        help="Print URL and compensation hint without opening a browser tab.",
    )
    args = parser.parse_args()

    jobs = load_jobs()
    job = find_job(jobs, args.job_id, args.company)
    resume_pdf, cover_letter_pdf = document_paths(job, args.resume, args.cover_letter)
    verify_documents(resume_pdf, cover_letter_pdf)
    profile = load_profile(CONFIG_DIR / "profile.json")

    print(f"Applying to: {job['company']} | {job['title']}")
    print(f"URL: {job['apply_url']}")
    print(f"Resume: {resume_pdf}")
    if cover_letter_pdf:
        print(f"Cover letter: {cover_letter_pdf}")
    expected = print_compensation_hint(job, profile)

    if not args.no_open:
        webbrowser.open(job["apply_url"])
        print("Opened application in your default browser. Upload PDFs and fill fields manually.")

    try:
        submitted = input("Did you manually submit this application? [y/N]: ").strip().lower() == "y"
    except EOFError:
        submitted = False
    update_job_status(
        jobs,
        job,
        submitted=submitted,
        expected_compensation_usd=expected,
        resume_pdf=resume_pdf,
        cover_letter_pdf=cover_letter_pdf,
    )
    save_jobs(jobs)
    print("Updated data/jobs.json.")


if __name__ == "__main__":
    main()
