# Job Finder



Human-in-the-loop job search: scrape public ATS and job-board listings, tailor LaTeX resume/cover letter with an AI assistant, compile PDFs, and open application pages for **manual** completion.



There is **no browser autofill** — you upload documents and answer screening questions yourself.



## Setup



```powershell

git clone https://github.com/WHooper03/job_finder.git

cd job_finder

python -m pip install -r requirements.txt

copy config\profile.example.json config\profile.json

```



Edit `config\profile.json` with your details and compensation strategy. Optional: `copy config\.env.example config\.env` if you store ATS login credentials locally (never commit `.env`).



Replace placeholder content in `master\resume.tex` and `master\cover_letter.tex` with your real master documents.



### Cursor / AI tailoring



Add a project rule using `docs\CURSOR_RULES_TEMPLATE.md` so agents know to copy from `master/` into `applications/{company_abbrev}/` without fabricating experience. Full steps: `TAILORING_WORKFLOW.md`.



### LaTeX



Install a TeX distribution (MiKTeX or TeX Live) so `compile_documents.py` can run `pdflatex`.



## Configuration



| File | Purpose |

|------|---------|

| `config/search_params.json` | Title keywords, salary floor, seniority filters, **location policy** |

| `config/sources.json` | Which boards/APIs to scrape |

| `config/companies.json` | Greenhouse/Lever/Ashby/Workday board tokens |

| `config/profile.json` | Your info + `compensation_strategy` (gitignored; copy from example) |



### Location policy (`search_params.json`)



Default: `"location_policy": "remote_us_or_local"`.



- Keeps jobs that are **US remote** (remote keywords + US location hints) **or** match **`local_area_keywords`** in the job location string.

- Set `local_area_keywords` to your metro, e.g. `["austin", "austin, tx"]`, to include on-site/hybrid nearby roles.

- Legacy value `remote_us_or_memphis` still works; prefer `local_area_keywords` (alias: `memphis_keywords` in older configs).



Other policies: set `location_policy` to anything else and define `location_keywords` for custom substring matching.



### Compensation hints (`apply.py`)



When a job has `salary_min` / `salary_max` in `data/jobs.json`, `apply.py` prints a suggested number from `profile.json`:



- If the range includes your `current_salary_usd`, it suggests `if_current_salary_in_range_ask_usd` (capped inside the range).

- If the whole range is above that bridge amount, it picks a conservative point above the floor using the job `score` (usually below midpoint unless the match is strong).

- If no range is posted, set `salary_expectation_usd` or decide manually.



Tune `application_defaults.compensation_strategy` in `config/profile.json`.



## Scrape jobs



```powershell

python scrape.py

```



Writes matches to `data/jobs.json` (gitignored). Dry run:



```powershell

python scrape.py --no-write --source-limit 3 --limit 10

```



Open aggregators run before company-specific boards so smaller employers appear without listing every board token.



## Tailor, compile, apply



1. Agent creates `applications\{abbrev}\{abbrev}_r.tex` and `{abbrev}_cl.tex` (see example in `applications/example/`).

2. `python compile_documents.py {abbrev}`

3. `python apply.py --job-id {id}` — opens the apply URL, prints compensation hint, updates status after you confirm submit.



## Supported sources



- Jobicy, RemoteJobsFinder, Remote OK, Arbeitnow, Remotive (public APIs)

- Greenhouse, Lever, Ashby, Workday public job endpoints



Workday and some ATS sites may still require accounts, CAPTCHAs, or multi-step flows in the browser.



## License



Resume LaTeX layout derives from [sb2nov/resume](https://github.com/sb2nov/resume) (MIT). Tooling in this repo is MIT unless noted otherwise.

