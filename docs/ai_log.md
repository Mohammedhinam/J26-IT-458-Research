# AI use log

## Entry template (one per task)

```text
Date:
Tool: (Codex / Claude / other)
Task:
Prompt summary:
What was accepted / rejected:
How I verified it (row counts, output check, docs):
What I changed myself:
```

Record the owner's own edits separately from Codex edits. Do not claim that the owner has verified or understood work until the owner confirms it.

## 2026-10-07 — Step 1: repository setup

Date: 2026-10-07
Tool: Codex
Task: Create project folders and append approved ignore rules.
Prompt summary: Setup only on vinuthan; preserve teammates’ files; no modelling or NHANES audit.
What was accepted / rejected: Accepted root-only data/models exclusions and environment/model rules; rejected global CSV/JPG/PNG exclusions at owner request.
How I verified it (row counts, output check, docs): Confirmed vinuthan and clean clone; reviewed .gitignore diff; checked ignore rules and staged paths before commit.
What I changed myself: Codex created folders, placeholders and this log and appended owner-approved ignore rules. Owner selected exclusions; owner understanding remains to be filled in.

## 2026-10-07 — Step 2: diary and AI log templates

Date: 2026-10-07
Tool: Codex
Task: Add diary and complete the reusable AI log template.
Prompt summary: Follow attached AGENTS.md section 9; document actual repository setup only.
What was accepted / rejected: Accepted plain templates and factual setup entries; no invented results or owner-understanding claims.
How I verified it (row counts, output check, docs): Compared template fields with section 9; reviewed both Markdown files and staged diff; checked branch before commit.
What I changed myself: Codex wrote the diary and expanded its own AI log. Owner's personal edits and understanding are pending owner input.

## 2026-10-07 — Step 3: Python requirements

Date: 2026-10-07
Tool: Codex
Task: Record the initial tabular Python dependencies.
Prompt summary: Add pandas, numpy, scikit-learn, xgboost and shap; no torch; owner performs installation.
What was accepted / rejected: Accepted the five initial libraries from AGENTS.md; deferred optional pyreadstat until an actual need is identified. No version pins were specified or tested.
How I verified it (row counts, output check, docs): Compared requirements with the authorised list; checked exact file contents and whitespace; no dependency installation or runtime compatibility test performed.
What I changed myself: Codex created requirements.txt and supplied python -m pip install -r requirements.txt. Owner installation and personal edits are pending.

## 2026-10-07 — Step 4: Planner task plan

Date: 2026-10-07
Tool: Codex
Task: Create the October 7–22 MS Planner task table.
Prompt summary: Use the attached 15-day plan, add the PP1 deadline, and distinguish completed setup from pending work.
What was accepted / rejected: Recorded verified hashes for steps 1–3; identified this file's own commit by exact message with a hash lookup command. No fabricated self-referential hash, metrics, feedback or installation evidence.
How I verified it (row counts, output check, docs): Compared October 7–21 tasks with section 11 and October 22 with section 1; checked all six requested columns, date coverage, commit references and Markdown whitespace. This table was not imported into Microsoft Planner.
What I changed myself: Codex wrote docs/planner_tasks.md and appended task records to its AI log and diary. Owner understanding and future task evidence remain pending.
