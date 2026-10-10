# AI use log

## Entry template (one per task)

```text
Date:
Tool: (name only if useful)
Task:
Prompt summary:
What was accepted / rejected:
How I verified it (row counts, output check, docs):
What I changed myself:
```

Record the owner's own edits separately. Do not claim that the owner has verified or understood work until the owner confirms it.

## 2026-10-07 — Step 1: repository setup

Date: 2026-10-07
Tool: AI
Task: Create project folders and append approved ignore rules.
Prompt summary: Setup only on vinuthan; preserve teammates’ files; no modelling or NHANES audit.
What was accepted / rejected: Accepted root-only data/models exclusions and environment/model rules; rejected global CSV/JPG/PNG exclusions at owner request.
How I verified it (row counts, output check, docs): Confirmed vinuthan and clean clone; reviewed .gitignore diff; checked ignore rules and staged paths before commit.
What I changed myself: Created folders and placeholders and appended owner-approved ignore rules. Owner selected exclusions; owner understanding remains to be filled in.

## 2026-10-07 — Step 2: diary and AI log templates

Date: 2026-10-07
Tool: AI
Task: Add diary and complete the reusable AI log template.
Prompt summary: Follow attached AGENTS.md section 9; document actual repository setup only.
What was accepted / rejected: Accepted plain templates and factual setup entries; no invented results or owner-understanding claims.
How I verified it (row counts, output check, docs): Compared template fields with section 9; reviewed both Markdown files and staged diff; checked branch before commit.
What I changed myself: Wrote the diary and expanded this log. Owner's personal edits and understanding are pending owner input.

## 2026-10-07 — Step 3: Python requirements

Date: 2026-10-07
Tool: AI
Task: Record the initial tabular Python dependencies.
Prompt summary: Add pandas, numpy, scikit-learn, xgboost and shap; no torch; owner performs installation.
What was accepted / rejected: Accepted the five initial libraries from AGENTS.md; deferred optional pyreadstat until an actual need is identified. No version pins were specified or tested.
How I verified it (row counts, output check, docs): Compared requirements with the authorised list; checked exact file contents and whitespace; no dependency installation or runtime compatibility test performed.
What I changed myself: Created requirements.txt and supplied python -m pip install -r requirements.txt. Owner installation and personal edits are pending.

## 2026-10-07 — Step 4: Planner task plan

Date: 2026-10-07
Tool: AI
Task: Create the October 7–22 MS Planner task table.
Prompt summary: Use the attached 15-day plan, add the PP1 deadline, and distinguish completed setup from pending work.
What was accepted / rejected: Recorded verified hashes for steps 1–3; identified this file's own commit by exact message with a hash lookup command. No fabricated self-referential hash, metrics, feedback or installation evidence.
How I verified it (row counts, output check, docs): Compared October 7–21 tasks with section 11 and October 22 with section 1; checked all six requested columns, date coverage, commit references and Markdown whitespace. This table was not imported into Microsoft Planner.
What I changed myself: Wrote docs/planner_tasks.md and appended task records to the log and diary. Owner understanding and future task evidence remain pending.

Date: 2026-10-07 | Tool: AI | Task: Revise step 2 diary format | Prompt summary: Use exact requested headings and leave owner understanding blank | Accepted/rejected: Accepted headings; no owner-understanding text invented; preserved step 1 entry and section 9 template | How verified: Reviewed diary headings, blank line and retained log entries; git diff --check | What I changed: Revised the diary; no teammate files changed.

Date: 2026-10-07 | Tool: AI | Task: Complete step 3 environment instructions | Prompt summary: Exact venv/install commands, five libraries, no torch | Accepted/rejected: Accepted commands as comments; deferred pyreadstat; no installation | How verified: Confirmed five package lines and command comments; git diff --check; runtime compatibility untested | What I changed: Documented commands in requirements.txt.

Date: 2026-10-07 | Tool: AI | Task: Revise step 4 Planner table and copy-paste section | Prompt summary: Nine columns, six buckets, checklists, recurrence and real GitHub links | Accepted/rejected: Accepted requested format; later tasks Not started; owner installation not claimed | How verified: Checked dates/columns/buckets/checklist lengths and resolved evidence hashes using git log and rev-parse; remote checked; no external Planner import | What I changed: Revised the Planner file and appended diary/log records.

Date: 2026-10-07 | Tool: AI | Task: A — install and verify local environment | Prompt summary: Create ignored .venv, install requirements, test imports and report actual versions; no torch | Accepted/rejected: Used available Python 3.13.5 instead of default 3.9.6 to meet Python 3.10+ rule; no requirements edits | How verified: Import test printed ok; pip check passed; versions read from installed metadata; torch absent; git status clean; .venv ignored and no root data/models/environment tracked | What I changed: Created local .venv only; initial llvmlite download timed out, retry with timeout/resume succeeded.

Date: 2026-10-07 | Tool: AI | Task: B — diary reflection draft | Prompt summary: Four simple lines based only on AGENTS.md and today’s setup | Accepted/rejected: Draft explicitly marked (DRAFT - owner to review and edit); owner has not confirmed understanding | How verified: Checked four lines cover independent branches, OHQ850 label not predictor, actual setup and no model/audit; reviewed staged diff | What I changed: Drafted the reflection and recorded environment verification in the diary; owner must review and edit.

Date: 2026-10-08 | Tool: AI | Task: Prepare NHANES audit checklist | Prompt summary: Defer audit; complete two small documentation tasks | Accepted/rejected: Accepted checklist preparation; no audit-completion claim | How verified: Read attached AGENTS.md sections 5, 6.2 and 12, checked CDC codebooks and branch; reviewed Markdown | What I changed: Created docs/nhanes_audit_checklist.md; no script or dataset processing.

Date: 2026-10-08 | Tool: AI | Task: Record audit handover and blockers | Prompt summary: Second small documentation commit; audit postponed | Accepted/rejected: Accepted factual handover; audit/tests remain Not started | How verified: Matched notes to observed empty data/, located file names and missing pytest; checked staged paths | What I changed: Created docs/nhanes_next_session.md; no data copies, installations, scripts or results.

Date: 2026-10-09 | Tool: AI | Task: Add pytest to project dependencies | Prompt summary: Install pytest into ignored .venv, add it to requirements, and show its version | Accepted/rejected: Installed pytest 9.1.1; no test suite or audit run | How verified: `.venv/bin/python -m pytest --version` printed `pytest 9.1.1`; `.venv/` remains ignored | What I changed: Added pytest to requirements.txt and recorded the actual version check.

Date: 2026-10-09 | Tool: AI | Task: Write NHANES audit script without running it | Prompt summary: Read AGENTS.md sections 5, 6.2 and 12; write the four-file audit and report generator, then syntax-check only | Accepted/rejected: Followed the valid-OHQ850 left-join request; no data processing, modelling, split, filtering, or audit run | How verified: `python -m py_compile` only; reviewed required inputs, predictors, report sections, and output path | What I changed: Added src/tabular/audit_nhanes.py and this factual log entry; docs/nhanes_audit.md is generated only when the script is run.

Date: 2026-10-10 | Tool: AI | Task: Verify audit decoding and join safeguards | Prompt summary: Execute existing audit, fix confirmed bugs only, add focused tests | Accepted/rejected: Accepted byte-verified zero decoding correction for INDFMPIR/OHQ870, field-specific special codes, and one-to-one joins; no imputation, predictor changes or training | How verified: Initial audit exposed exact 2**-260 zero artifact; verified all affected source cells are zero bytes; CDC codebooks checked; `.venv/bin/python -m pytest -q tests/test_audit_nhanes.py` passed 6 tests; revised audit executed successfully | What I changed: Corrected audit script and added synthetic-data tests; no original XPT files modified.
