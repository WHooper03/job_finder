# Cursor rules for resume tailoring

This repo does **not** ship personal Cursor rules. Add your own so agents follow consistent tailoring behavior.

## Setup

1. In your project (or parent workspace), create `.cursor/rules/resume-tailoring.mdc`.
2. Paste the template below and adjust paths to match your machine.
3. Optionally set `globs: **/*.tex` so the rule applies when editing LaTeX.

## Suggested rule content

```markdown
---
description: Resume/cover-letter tailoring conventions
globs: **/*.tex
alwaysApply: false
---

# Resume & Cover Letter Tailoring

- Treat `master/resume.tex` as the **master/base** resume. Do not overwrite it when tailoring a single job.
- Create per-job copies under `applications/{company_abbrev}/` (see `TAILORING_WORKFLOW.md`).

## Goals (priority order)
1. ATS keyword alignment with the posting.
2. Reads as written for this role.
3. **Complete honesty** — no fabricated skills, employers, or metrics.
4. One page for tailored resumes.

## Process
- Extract 20–30 high-value keywords from the posting.
- Before finalizing: ATS match estimate, missing keywords, improvements, recruiter concerns.
- Use ATS-friendly dates: `MM/YYYY -- Present`, include target job title in Summary, plain section labels.

## Hard constraints
- One page; trim least-relevant content before shrinking fonts.
- No graphics or multi-column layouts.
- Cover letters: tailor every application unless you explicitly skip one.
```

Point your agent at `TAILORING_WORKFLOW.md` for compile and apply commands.
