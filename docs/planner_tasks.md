# MS Planner tasks — Component 2

Source: attached AGENTS.md section 11 (October 7–21) and section 1 (October 22 PP1 deadline). Owner for every task: Vinuthan T (IT23311022). Dates are in 2026. This file is ready to copy into Planner; no Planner tasks have been created externally.

Buckets and priorities below follow the requested organisation; priority assignments are planning choices, not research results. Set the three daily tasks to repeat every day through October 22. Original setup notes describe October 7; the audit/preprocessing status below was updated on October 10. Planned dates are retained so schedule delays remain visible.

| Task | Bucket | Priority | Start | Due | Status | Deliverable | Evidence | Checklist (2–3 items) |
|---|---|---|---|---|---|---|---|---|
| Project folders and approved ignore rules | Setup | High | 2026-10-07 | 2026-10-07 | Completed | Code/docs/tests folders and ignored local data/ | [e2e61e5](https://github.com/Mohammedhinam/J26-IT-458-Research/commit/e2e61e5e1ac574bd4220a7bd1490b189c590306e) | Check folder paths; verify ignore rules; review commit |
| Diary and AI log templates | Evidence and Docs | High | 2026-10-07 | 2026-10-07 | Completed | Section 9 AI template, diary headings and blank owner-understanding line | [580ed9c](https://github.com/Mohammedhinam/J26-IT-458-Research/commit/580ed9c93b6577622f231367e7cd3cca9ac45d98) | Preserve step 1 log; review headings; owner fills understanding |
| Python requirements and environment commands | Setup | High | 2026-10-07 | 2026-10-07 | Completed | Five packages and exact venv/install commands | [9e723e0](https://github.com/Mohammedhinam/J26-IT-458-Research/commit/9e723e074dc096860ef3860f4455bd9c9bc653f8) | Check package list; read commands; owner installs separately |
| Planner task plan | Evidence and Docs | High | 2026-10-07 | 2026-10-07 | Completed | October 7–22 table, recurrence and copy-paste notes | [799cedf](https://github.com/Mohammedhinam/J26-IT-458-Research/commit/799cedf85d56d22c041191c7b9367ac14c797c00) (original plan); latest format is the commit containing this file, hash lookup below | Review dates/buckets; check evidence links; copy into Planner |
| Create virtual environment and install packages (owner) | Setup | High | 2026-10-07 | 2026-10-07 | Not started | Local .venv and installed dependencies | Pending owner confirmation; commands provided, not executed | Create .venv; activate it; install requirements |
| NHANES audit | Tabular | High | 2026-10-08 | 2026-10-08 | Completed (Oct 10) | Verified 7,817 valid labels, row-preserving joins and aggregate audit report | [b6abe80](https://github.com/Mohammedhinam/J26-IT-458-Research/commit/b6abe80f74e97108c23ba19794c72e846c3a4c49); 6 audit tests passed | Confirm join plan; check SEQN/counts; save exclusion log |
| Preprocessing and logistic regression baseline | Tabular | High | 2026-10-09 | 2026-10-09 | In progress | Preprocessing complete Oct 10; classifier training and baseline validation Not started | [9dc73ec](https://github.com/Mohammedhinam/J26-IT-458-Research/commit/9dc73ec70c10939334e8f27b1b15fd8126c7ea26); docs/tabular_preprocessing.md | Freeze stratified split (done); fit preprocessing on development only (done); validate baseline in development data (pending) |
| NHANES cleaning and preprocessing verification | Tabular | High | 2026-10-10 | 2026-10-10 | Completed | 7,814 cleaned participants; frozen 6,251/1,563 split; 12 inputs and 47 encoded columns | [9dc73ec](https://github.com/Mohammedhinam/J26-IT-458-Research/commit/9dc73ec70c10939334e8f27b1b15fd8126c7ea26); 15 total tests passed | Preserve audit and track 3 exclusions; verify split/no leakage; check finite development matrix |
| XGBoost and comparison table | Tabular | High | 2026-10-10 | 2026-10-10 | Not started | Measured XGBoost/logistic/training-rate comparison | Pending: actual outputs, checks and commit links | Train on development data; compare metrics; inspect calibration |
| SHAP and constrained what-if functions | Explainability and Simulator | High | 2026-10-11 | 2026-10-11 | Not started | SHAP output and basic Python simulator | Pending: actual outputs, checks and commit links | Verify SHAP reconstruction; restrict smoking/cleaning changes; test reset/validation |
| Caption labels and image dataset audit | Vision | High | 2026-10-12 | 2026-10-12 | Not started | MGI labels, review list, split audit and resized images on Drive | Pending: actual outputs, checks and commit links | Review ambiguous captions; check duplicates/overlap; report grade counts |
| Buffer and supervisor meeting | Tabular | High | 2026-10-13 | 2026-10-13 | Not started | Tabular results and meeting notes | Pending: actual outputs, checks and commit links | Prepare measured results; discuss limitations; record feedback |
| ResNet-50 baseline in Colab | Vision | High | 2026-10-14 | 2026-10-14 | Not started | ResNet-50 and majority-class baseline | Pending: actual outputs, checks and commit links | Use audited labels/splits; record training setup; evaluate baseline |
| EfficientNet-B0 comparison | Vision | High | 2026-10-15 | 2026-10-15 | Not started | Comparison using the same labels/splits | Pending: actual outputs, checks and commit links | Keep evaluation setup fixed; record measured metrics; compare baselines |
| Grad-CAM three-panel output | Explainability and Simulator | High | 2026-10-16 | 2026-10-16 | Not started | Original, heatmap and overlay | Pending: actual outputs, checks and commit links | Use same predicted class; check image alignment; describe model attention |
| FastAPI image and questionnaire endpoints | Tabular | High | 2026-10-17 | 2026-10-17 | Not started | Independent endpoint outputs and Postman tests | Pending: actual outputs, checks and commit links | Respect authorised file paths; test requests/responses; keep branch outputs separate |
| What-if endpoint and feedback from 3 people | Explainability and Simulator | High | 2026-10-18 | 2026-10-18 | Not started | Validated endpoint and actual feedback notes | Pending: actual outputs, checks and commit links | Validate permitted inputs; test reset/scenarios; record real feedback |
| Tests, risk register, README and architecture diagram | Evidence and Docs | High | 2026-10-19 | 2026-10-19 | Not started | Test evidence, risk register, approved docs and owner-drawn diagram | Pending: actual outputs, checks and commit links | Run meaningful tests; obtain shared README approval; owner draws architecture |
| Evidence pack, logs catch-up and demo script | PP1 Prep | High | 2026-10-20 | 2026-10-20 | Not started | Traceable evidence pack and demo script | Pending: actual outputs, checks and commit links | Collect verified artifacts; catch up logs; review demo script |
| Demo rehearsal and Q&A practice | PP1 Prep | High | 2026-10-21 | 2026-10-21 | Not started | Rehearsal record and owner explanations | Pending: actual outputs, checks and commit links | Rehearse both functions; practise viva answers; record issues |
| PP1 demonstration | PP1 Prep | High | 2026-10-22 | 2026-10-22 | Not started | Photo → MGI + Grad-CAM; questionnaire → prior-gum-treatment probability + SHAP + basic what-if | Pending: actual outputs, checks and commit links | Check both functions; explain limitations; retain real presentation evidence |
| Daily diary entry (today) | Evidence and Docs | Medium | 2026-10-07 | 2026-10-07 | Completed | Today’s factual diary entry | [580ed9c](https://github.com/Mohammedhinam/J26-IT-458-Research/commit/580ed9c93b6577622f231367e7cd3cca9ac45d98) | Record work/problems; record decisions/next step; leave owner words blank |
| Daily diary entry (repeat daily, Oct 8–22) | Evidence and Docs | Medium | 2026-10-08 | 2026-10-22 | Not started | Daily factual diary entry | Pending: daily dated records and real commit links | Record work/problems; record decisions/next step; leave owner words blank |
| Daily AI log entry (today) | Evidence and Docs | Medium | 2026-10-07 | 2026-10-07 | Completed | AI use recorded for today’s tasks | [9e723e0](https://github.com/Mohammedhinam/J26-IT-458-Research/commit/9e723e074dc096860ef3860f4455bd9c9bc653f8) | Record prompt and acceptance; record verification; distinguish owner/Codex edits |
| Daily AI log entry (repeat daily, Oct 8–22) | Evidence and Docs | Medium | 2026-10-08 | 2026-10-22 | Not started | AI use recorded for each day’s tasks | Pending: daily dated records and real commit links | Record prompt and acceptance; record verification; distinguish owner/Codex edits |
| Small-commit check (today) | Evidence and Docs | Medium | 2026-10-07 | 2026-10-07 | Completed | Separate logical commits on vinuthan | [9e723e0](https://github.com/Mohammedhinam/J26-IT-458-Research/commit/9e723e074dc096860ef3860f4455bd9c9bc653f8) | Check branch before commit; inspect staged paths; verify push/status |
| Small-commit check (repeat daily, Oct 8–22) | Evidence and Docs | Medium | 2026-10-08 | 2026-10-22 | Not started | Separate logical commits on vinuthan | Pending: daily dated records and real commit links | Check branch before commit; inspect staged paths; verify push/status |

## Evidence and limitations

The original Planner plan was committed as 799cedf. The revised format is committed with this file under `docs: add planner task plan`. Its own hash cannot be embedded in its contents without changing that hash. Find the latest actual hash after committing with:

```bash
git log -1 --format=%H --fixed-strings --grep='docs: add planner task plan' vinuthan
```

Commit URLs below use the verified origin remote. Original setup: e2e61e5; original logs: 031e8c6; original requirements: 52867dd; original plan: 799cedf. Revised logs and environment instructions have their own real links above.

At the original October 7 plan-writing stage, modelling, audit execution, package installation and feedback were pending. Current verified audit/preprocessing progress is recorded above and below. OHQ850 means self-reported previous gum treatment; MGI means visible gingival inflammation. Keep outputs independent. No diagnosis, future progression or treatment-effect claim. What-if is model sensitivity only.

If behind, cut the EfficientNet comparison first (keep ResNet-50), then the what-if endpoint (keep the Python function), then extra ceremonies. Retain both key PP1 functions. Future integration paths and shared-file edits require the owner's applicable authorisation; this plan does not override current file boundaries.

## Copy-paste for Planner today (Oct 7)

### Project folders and approved ignore rules

Title: Project folders and approved ignore rules

Notes: Completed on October 7, 2026. Owner: Vinuthan T. Bucket: Setup. Deliverable: Code/docs/tests folders and ignored local data/.

GitHub commit URL: [e2e61e5e1ac574bd4220a7bd1490b189c590306e](https://github.com/Mohammedhinam/J26-IT-458-Research/commit/e2e61e5e1ac574bd4220a7bd1490b189c590306e)

Checklist:

- [ ] Check folder paths
- [ ] Verify ignore rules
- [ ] Review commit

### Diary and AI log templates

Title: Diary and AI log templates

Notes: Completed on October 7, 2026. Owner: Vinuthan T. Bucket: Evidence and Docs. Deliverable: Section 9 AI template, diary headings and blank owner-understanding line.

GitHub commit URL: [580ed9c93b6577622f231367e7cd3cca9ac45d98](https://github.com/Mohammedhinam/J26-IT-458-Research/commit/580ed9c93b6577622f231367e7cd3cca9ac45d98)

Checklist:

- [ ] Preserve step 1 log
- [ ] Review headings
- [ ] Owner fills understanding

### Python requirements and environment commands

Title: Python requirements and environment commands

Notes: Completed on October 7, 2026. Owner: Vinuthan T. Bucket: Setup. Deliverable: Five packages and exact venv/install commands. Owner installation remains Not started.

GitHub commit URL: [9e723e074dc096860ef3860f4455bd9c9bc653f8](https://github.com/Mohammedhinam/J26-IT-458-Research/commit/9e723e074dc096860ef3860f4455bd9c9bc653f8)

Checklist:

- [ ] Check package list
- [ ] Read commands
- [ ] Owner installs separately

### Planner task plan

Title: Planner task plan

Notes: Completed on October 7, 2026. Owner: Vinuthan T. Bucket: Evidence and Docs. Deliverable: October 7–22 table, recurrence and copy-paste notes. Original table evidence is linked below; this revision adds the requested Planner format. Resolve its latest commit with the lookup command above.

GitHub commit URL: [799cedf85d56d22c041191c7b9367ac14c797c00](https://github.com/Mohammedhinam/J26-IT-458-Research/commit/799cedf85d56d22c041191c7b9367ac14c797c00)

Checklist:

- [ ] Review dates/buckets
- [ ] Check evidence links
- [ ] Copy into Planner

### Daily diary entry

Title: Daily diary entry

Notes: Today’s task Completed. Diary updated; owner-understanding field remains blank. Set daily recurrence for October 8–22; future occurrences are Not started.

GitHub commit URL: [580ed9c93b6577622f231367e7cd3cca9ac45d98](https://github.com/Mohammedhinam/J26-IT-458-Research/commit/580ed9c93b6577622f231367e7cd3cca9ac45d98)

Checklist:

- [ ] Review today’s entry
- [ ] Record own understanding

### Daily AI log entry

Title: Daily AI log entry

Notes: Today’s task Completed. AI records retained and appended for each task. Set daily recurrence for October 8–22; future occurrences are Not started.

GitHub commit URL: [9e723e074dc096860ef3860f4455bd9c9bc653f8](https://github.com/Mohammedhinam/J26-IT-458-Research/commit/9e723e074dc096860ef3860f4455bd9c9bc653f8)

Checklist:

- [ ] Review prompt/acceptance
- [ ] Review verification and edits

### Small-commit check

Title: Small-commit check

Notes: Today’s task Completed. Branch checked before commits; push and status verified. Set daily recurrence for October 8–22; future occurrences are Not started.

GitHub commit URL: [9e723e074dc096860ef3860f4455bd9c9bc653f8](https://github.com/Mohammedhinam/J26-IT-458-Research/commit/9e723e074dc096860ef3860f4455bd9c9bc653f8)

Checklist:

- [ ] Review staged files
- [ ] Check vinuthan
- [ ] Verify clean status

## Copy-paste for Planner — October 10 update

Task: NHANES cleaning and preprocessing verification

Bucket: Tabular. Priority: High. Start/Due: 2026-10-10. Status: Completed.

Notes: Preserved the audit evidence of 7,817 valid labels. Excluded three OHQ870=9 records from the main analysis and kept their details locally for sensitivity review. Main cohort is 7,814 (1,941 Yes / 5,873 No). Derived smoking status with questionnaire skip logic, preserved valid 7/3/0 values, and handled field-specific special codes. Froze a seed-42 stratified split of 6,251 development and 1,563 reserved held-out participants, with zero overlap. Fitted preprocessing on development data only: 12 conceptual inputs become 47 encoded columns; development output is finite. Fifteen tests passed. No classifier training or final held-out evaluation performed.

Checklist:

- [x] Document cleaning, special-code and smoking-skip rules
- [x] Freeze split and verify development-only fitting
- [x] Save aggregate results and pass focused tests

Evidence: [9dc73ec](https://github.com/Mohammedhinam/J26-IT-458-Research/commit/9dc73ec70c10939334e8f27b1b15fd8126c7ea26), docs/tabular_preprocessing.md and tests/test_preprocess_nhanes.py.

Existing combined task “Preprocessing and logistic regression baseline”: set In progress. Preprocessing is completed; baseline training/validation is Not started. Final held-out evaluation remains deferred.

External board update: not performed in this session. Browser access reported the Mac locked and a browser request-header-policy error. This file contains the prepared update; it does not prove an external Planner task was changed.
