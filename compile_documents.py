"""Compile tailored LaTeX documents and copy PDFs to Downloads."""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent
APPLICATIONS_DIR = ROOT / "applications"


def compile_tex(tex_path: Path) -> Path:
    if not tex_path.exists():
        raise SystemExit(f"Missing source file: {tex_path}")

    result = subprocess.run(
        ["pdflatex", "-interaction=nonstopmode", tex_path.name],
        cwd=tex_path.parent,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit(
            f"pdflatex failed for {tex_path.name}\n\nSTDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
        )

    pdf_path = tex_path.with_suffix(".pdf")
    if not pdf_path.exists():
        raise SystemExit(f"Expected PDF was not created: {pdf_path}")
    return pdf_path


def compile_application(abbrev: str, downloads_dir: Path) -> list[Path]:
    app_dir = APPLICATIONS_DIR / abbrev
    sources = [app_dir / f"{abbrev}_r.tex", app_dir / f"{abbrev}_cl.tex"]
    copied: list[Path] = []

    for source in sources:
        pdf = compile_tex(source)
        destination = downloads_dir / pdf.name
        downloads_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(pdf, destination)
        copied.append(destination)

    return copied


def main() -> None:
    parser = argparse.ArgumentParser(description="Compile tailored resume and cover letter PDFs.")
    parser.add_argument("company_abbrev", help="Company abbreviation, e.g. stripe for applications/stripe/stripe_r.tex.")
    parser.add_argument(
        "--downloads",
        type=Path,
        default=Path.home() / "Downloads",
        help="Destination folder for compiled PDFs.",
    )
    args = parser.parse_args()

    copied = compile_application(args.company_abbrev, args.downloads)
    print("Compiled and copied:")
    for path in copied:
        print(f"- {path}")


if __name__ == "__main__":
    main()
