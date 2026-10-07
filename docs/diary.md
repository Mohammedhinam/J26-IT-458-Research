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
