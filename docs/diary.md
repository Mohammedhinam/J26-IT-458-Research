# Project diary — Component 2

## Daily entry template

- Date:
- What was done:
- Decisions made:
- Problems faced:
- Next step:
- What I understood (my own words):

## 2026-10-07 — Repository setup

### What was done

Codex read the attached AGENTS.md fully. The owner confirmed the project summary, authorised cloning Mohammedhinam/J26-IT-458-Research into this workspace, and confirmed vinuthan as the only permitted branch. Codex cloned it, created docs/, src/tabular/, src/vision/, tests/ and local ignored data/, appended approved exclusions to .gitignore, and started the AI log. Step 1 was committed and pushed as e2e61e5. Step 2 adds this diary and the full AI log template.
### Decisions made

Keep Component 2 code organised, leave teammates' files intact, exclude local datasets and models, and retain a clear record the owner can review and defend. Global CSV/JPG/PNG exclusions were rejected by the owner so shared files and evidence remain visible to Git.
### Problems faced

Before cloning, Git detected an unrelated parent repository on master with an LMS remote; work stopped without changing it. The correct research repository is now cloned on vinuthan. No data, audit script, modelling, metrics or package installation ran today.
### Next step

Record Python requirements, prepare the October 7–22 Planner table, and let the owner install dependencies. NHANES audit is scheduled for October 8, subject to confirming the join plan before use.
- What I understood (my own words): (DRAFT - owner to review and edit)
  1. The photo and questionnaire branches use different people, so we keep them separate and never combine their scores.
  2. OHQ850 means self-reported previous gum treatment; it is the label the questionnaire model will learn, never an input predictor.
  3. Today we set up folders, ignore rules, requirements, logs and the Planner plan, then installed packages in .venv and checked that imports work.
  4. No model was built or trained yet, and no NHANES audit script was run today.

### Task record

- Step 1: Folders, approved ignore rules and minimal AI log created; e2e61e5 pushed to vinuthan and working tree verified clean.
- Step 2: Diary and full AI log template created; both reviewed against the attached AGENTS.md section 9.
- Step 3: Added the five initial Python dependencies; omitted optional pyreadstat and torch. Installation command supplied to the owner; packages were not installed and compatibility was not tested. Step 2 was pushed as 031e8c6.
- Step 4: Created the October 7–22 Planner table with completed setup and pending future tasks. Added October 22 from the stated PP1 deadline. Step 3 was pushed as 52867dd. The Planner file references its own commit by message because embedding its own hash is impossible; the completion message supplies that hash. No Planner import, venv creation, installation, audit or modelling performed.
- Revised step 2: Updated diary headings to What was done / Problems faced / Decisions made / Next step and left the owner-understanding line blank. Preserved the original step 1 AI record and full section 9 template.
- Revised step 3: Recorded exact .venv creation, activation and installation commands in requirements.txt comments; owner will execute them. Packages remain unchanged and no environment was created.
- Revised step 4: Expanded Planner table with priorities, start/due/status, requested buckets, checklists, daily recurring tasks and copy-paste notes using real GitHub commit URLs. Future work and owner installation remain Not started.
- Task A completed: Created local ignored .venv with Python 3.13.5 and installed pandas 3.0.6, numpy 2.5.3, scikit-learn 1.9.1, xgboost 3.4.1 and shap 0.52.0. First install timed out downloading llvmlite; retry with longer timeout and resume succeeded. Import test printed ok; pip check found no broken requirements; Git status remained clean and .venv was ignored. No requirements change and no torch installation. Earlier installation-pending notes above describe the earlier setup stages.
- Task B completed: Codex drafted four reflection lines from the attached AGENTS.md and verified setup work, explicitly marked for owner review and editing; this does not claim owner understanding.

## 2026-10-08 — Audit preparation only

### What was done

Read the required attached AGENTS.md sections, checked repository/data/environment state, located candidate XPT files in Downloads, and reviewed CDC codebooks. Prepared an audit checklist. No audit script was written or run.

### Problems faced

The repository data/ folder is empty; pytest is absent from .venv. An untracked mermaid-diagram.png belongs to existing workspace work and was left untouched.

### Decisions made

Owner deferred execution to the next session due to limited time. Record actual documentation work only; no invented dataset counts or completed audit status.

### Next step

Confirm the local data copies and pytest installation, then implement and run the requested audit.

What I understood (my own words):

- Prepared next-session handover with source locations, missing pytest and next actions. Both October 8 tasks are documentation only; audit execution remains Not started.

## 2026-10-10 — NHANES audit execution and validation

### What was done

Read the attached AGENTS.md sections 5, 6.2 and 12 and the existing audit/checklist. Confirmed the research remote and vinuthan branch. Copied the four named XPT files from Downloads into ignored data/ without overwriting existing different files or changing originals; source/copy SHA-256 hashes matched. The extra P_DEMO (1).xpt matched P_DEMO.xpt and was not copied. Ran the existing audit, fixed confirmed reader/code-classification issues and added focused synthetic-data tests. All 6 tests passed; the revised audit completed successfully.

Saved the generated results to docs/nhanes_audit.md. File sizes were P_DEMO 15,560 rows/29 columns, P_OHQ 14,986/39, P_SMQ 11,137/16 and P_DIQ 14,986/28; none had duplicate or missing SEQN. OHQ850 had 1,941 Yes (24.83%), 5,876 No (75.17%), 36 don't-know and 7,133 missing responses. All four reference counts MATCH. All three joins retained 7,817 unique respondents, all aged at least 30; age range was 30–80 (80 means 80+).

All 13 predictors were present. INDFMPIR had 1,186 missing responses and SMQ040 had 4,373; other predictors had no NaNs. The missing SMQ040 rows comprised 4,369 SMQ020=No and 4 SMQ020=refused/don't know, matching the documented skip pattern. OHQ870 included three responses of 9 and two don't-know responses of 99; they were flagged/recorded and retained. Full source-file zero repairs were 142 INDFMPIR cells and 2,620 OHQ870 cells; the report records them separately from cohort statistics. No cleaned modelling sample or training results were produced.

### Problems faced

Pandas 3.0.6 decoded exact IBM zero bytes as 5.397605346934028e-79. Source-byte checks confirmed the issue in INDFMPIR and OHQ870. Also, the original script incorrectly included 8/9 as OHQ870 special codes and 7/9 as RIAGENDR special codes. CDC lists OHQ870 responses through 9, while the project rule allows only 0–7; the discrepancy is reported rather than hidden.

### Decisions made

Restore only the exact zero artifact in the two affected predictors after verifying every corresponding source cell is all-zero bytes. Keep missing and other numeric values unchanged. Enforce one-to-one joins so duplicate keys cannot inflate the cohort. Keep the requested valid-OHQ850 audit view, reporting age eligibility and cleaning-day anomalies without further exclusions. Historical October 8 handover notes describe their original preparation date.

### Next step

Review the three OHQ870=9 records against the project's 0–7 rule and the CDC released range of 0–9 before preprocessing. Then plan field-specific missing/special-code handling and smoking derivation. Modelling remains unstarted.

What I understood (my own words):

## 2026-10-10 — Tabular cleaning and preprocessing

### What was done

Reviewed attached AGENTS.md and the supplied proposal RP-IT23311022 (2).pdf, pages 19–20 and 22. Added field-specific cleaning rules, smoking derivation and a reusable sklearn preprocessing transformer. Reused the audited loader and zero-decoding correction without rerunning the audit report generator. Nine new preprocessing tests and six existing audit tests passed. Ran preprocessing on the local files; recorded real results, with no classifier training or held-out evaluation.

Verified results: 7,817 audit-valid rows minus three OHQ870=9 exclusions and zero age exclusions gives 7,814 main-analysis participants (1,941 Yes / 5,873 No). The seed-42 split has 6,251 development and 1,563 reserved held-out participants with zero overlap. Twelve conceptual inputs produce 47 encoded columns; the 6,251×47 development matrix is finite. Smoking categories are 4,366 fewer-than-100 lifetime, 2,040 former, 1,404 current and 4 unknown. Development numeric medians are age 56, income ratio approximately 2.265 and cleaning days 3. The split manifest and three-row sensitivity review are ignored local data, not committed. Saved aggregate output to docs/tabular_preprocessing.md; updated the repository Planner table and copy-paste notes, with external board access still blocked. Implementation commit: 9dc73ec.

### Problems faced

The CDC released OHQ870 range includes 9 while the proposal's main-analysis rule is integer 0–7. The owner explicitly authorised excluding the three flagged records and retaining them separately for sensitivity review. Direct Microsoft Planner access is blocked by a locked Mac/browser-access error; repository Planner notes will be updated separately.

### Decisions made

Keep 7,817 valid source labels as preserved audit evidence. Convert only each field's refused/don't-know codes to missing; preserve OHQ030=7, DIQ010=3 and INDFMPIR=0. Known fewer-than-100 lifetime respondents retain a derived smoking category, with skipped SMQ040 tracked separately rather than imputed. Unknown or inconsistent smoking responses are marked unknown and tracked. Use a seed-42 stratified participant split before fitting medians/scaling/encoding. Codebook-defined categories and fixed numeric missing flags ensure stable outputs. No identifiers, outcomes, survey design fields or review metadata enter predictors.

### Next step

Propose a regularised logistic regression versus training-rate baseline using development-only validation and fresh preprocessing within each fold. Keep the final held-out set reserved. Copy the prepared Planner update to the board when browser access is available.

What I understood (my own words):
