# Tailoring workflow



Scraping and opening applications are scripted; resume and cover letter tailoring are meant to be **agent-assisted** (Cursor or similar) so you keep judgment, honesty checks, and one-page layout control.



## Per-job flow



1. Run `python scrape.py` from the repo root.

2. Pick a job from `data/jobs.json` by `id`, company, and title.

3. Ask your agent to tailor documents using:

   - `master/resume.tex` as the master resume.

   - `master/cover_letter.tex` as the cover letter template.

   - Your Cursor rule (see `docs/CURSOR_RULES_TEMPLATE.md`).

4. Before writing the resume, the agent should provide:

   - ATS match score estimate.

   - Missing keywords.

   - Recommended improvements.

   - Potential recruiter concerns.

5. The agent writes:

   - `applications/{company_abbrev}/{company_abbrev}_r.tex`

   - `applications/{company_abbrev}/{company_abbrev}_cl.tex`

6. Compile PDFs:



```powershell

python compile_documents.py {company_abbrev}

```



7. Open the application (browser only — you fill and submit manually):



```powershell

python apply.py --job-id {job_id}

```



`apply.py` prints a **suggested compensation** from `config/profile.json` and opens the apply URL. Review every field and submit yourself.



See `applications/example/` for naming and structure.



## Naming rules



- Resume source: `{company_abbrev}_r.tex`

- Cover letter source: `{company_abbrev}_cl.tex`

- Resume PDF: `{company_abbrev}_r.pdf`

- Cover letter PDF: `{company_abbrev}_cl.pdf`



Use the `company_abbrev` on each job in `data/jobs.json`.



## Safety rules



- Never overwrite `master/resume.tex` for a single application.

- Keep tailored resumes to one page; use honest content only.

- Do not rely on automation to submit applications.

