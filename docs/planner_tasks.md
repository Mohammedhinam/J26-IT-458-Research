# MS Planner tasks — Component 2

Source: attached AGENTS.md section 11 (October 7–21 plan) and section 1 (PP1 deadline: October 22, 2026). Owner: Vinuthan T (IT23311022). Bucket names are suggested Planner groups. This is a Markdown planning table; it has not been imported into Microsoft Planner.

All due dates are in 2026. Completed indicates verified setup work only. Future evidence is explicitly pending; no model results exist from today's work.

| Task | Owner | Bucket | Due | Deliverable | Evidence |
|---|---|---|---|---|---|
| Completed: project folders and approved .gitignore | Vinuthan T | Setup | 2026-10-07 | docs/, src/tabular/, src/vision/, tests/; local ignored data/; .gitkeep placeholders and approved exclusions | e2e61e5; pushed to vinuthan; ignore checks passed |
| Completed: diary and AI log templates | Vinuthan T | Documentation | 2026-10-07 | docs/diary.md and docs/ai_log.md with October 7 entries | 031e8c6; pushed to vinuthan; template fields reviewed |
| Completed: initial Python requirements | Vinuthan T | Setup | 2026-10-07 | requirements.txt with five authorised packages; install command supplied | 52867dd; pushed to vinuthan; package list checked; installation not run |
| Completed: Planner task plan | Vinuthan T | Documentation | 2026-10-07 | This October 7–22 table | Commit containing this row: docs: add planner task plan; resolve its hash with the command below |
| Pending: create venv and install dependencies (owner) | Vinuthan T | Setup | 2026-10-07 | Local Python environment; python -m pip install -r requirements.txt | Pending: owner confirms environment and install output; never commit environment |
| Pending: NHANES audit | Vinuthan T | Questionnaire | 2026-10-08 | Confirm join plan; audit joins, filters, real final N and exclusion log | Pending: actual counts, SEQN checks and audit output; do not treat 11,137 as final N |
| Pending: preprocessing and logistic regression baseline | Vinuthan T | Questionnaire | 2026-10-09 | Development-only preprocessing and logistic regression baseline | Pending: frozen split, leakage checks and measured baseline metrics |
| Pending: XGBoost and comparison table | Vinuthan T | Questionnaire | 2026-10-10 | XGBoost compared with logistic regression and training-rate baseline | Pending: actual comparison results and calibration evidence |
| Pending: SHAP and what-if Python functions | Vinuthan T | Explainability | 2026-10-11 | SHAP explanations; constrained smoking/cleaning what-if | Pending: contribution reconstruction, scenario validation and limitations wording |
| Pending: image labels and dataset audit | Vinuthan T | Vision | 2026-10-12 | Caption-derived MGI labels, review list, overlap audit and resized images on Drive | Pending: real per-grade/split counts and duplicate checks; data stays outside Git |
| Pending: buffer and supervisor meeting | Vinuthan T | Review | 2026-10-13 | Tabular results shown to supervisor | Pending: meeting notes and feedback |
| Pending: ResNet-50 baseline in Colab | Vinuthan T | Vision | 2026-10-14 | ResNet-50 and majority baseline using audited labels/splits | Pending: actual training record and measured baseline metrics |
| Pending: EfficientNet-B0 comparison | Vinuthan T | Vision | 2026-10-15 | EfficientNet-B0 using the same evaluation setup | Pending: measured comparison table; provisional targets are not achieved results |
| Pending: Grad-CAM three-panel output | Vinuthan T | Explainability | 2026-10-16 | Original, heatmap and overlay for the same predicted class | Pending: output review; explain attention without clinical-boundary claims |
| Pending: FastAPI image/questionnaire endpoints | Vinuthan T | Integration | 2026-10-17 | Independent endpoint outputs and Postman tests | Pending: actual requests/responses and test evidence; no fused score |
| Pending: what-if endpoint and feedback | Vinuthan T | Integration | 2026-10-18 | Constrained endpoint and brief feedback from 3 people | Pending: validation evidence and real feedback notes; no treatment-effect claim |
| Pending: tests, risk register, README and architecture | Vinuthan T | Validation | 2026-10-19 | Test cases, risk register, documentation and diagram drawn manually by owner | Pending: executed test results and owner-drawn diagram; obtain approval before changing shared README |
| Pending: evidence pack and demo script | Vinuthan T | PP1 preparation | 2026-10-20 | Evidence pack, logs caught up and demo script | Pending: traceable artifacts and reviewed script |
| Pending: rehearsal and Q&A | Vinuthan T | PP1 preparation | 2026-10-21 | Demo rehearsal and owner explanations | Pending: rehearsal checklist and Q&A notes |
| Pending: PP1 demonstration | Vinuthan T | PP1 | 2026-10-22 | Photo to MGI + Grad-CAM; questionnaire to previous-gum-treatment probability + SHAP + basic what-if | Pending: actual demonstration and submission evidence; deadline from section 1 |

## Evidence for this file's own commit

A file cannot embed the hash of the commit that contains those exact bytes: adding the hash changes the commit. The other completed rows contain actual hashes. Resolve this row's commit hash from repository history:

```bash
git log -1 --format=%h --fixed-strings --grep='docs: add planner task plan' vinuthan
```

The actual hash is also reported in the completion message. This preserves the requested four-commit sequence without a separate evidence-update commit.

## Scope and fallback rules

The vision and questionnaire branches remain independent. MGI is visible gingival inflammation, not a periodontitis diagnosis. OHQ850 is self-reported previous gum treatment, never current disease risk or a predictor. What-if demonstrates model sensitivity, not future progression or treatment effects.

If behind, follow section 11: cut the EfficientNet comparison first (keep ResNet-50), then the what-if endpoint (keep its Python function), then extra ceremonies. Retain both key demonstration functions. Future integration work must respect the owner's file/path permissions; listing work here does not authorise changes to teammates' files.
