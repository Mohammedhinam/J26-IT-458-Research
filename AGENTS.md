# AGENTS.md — Component 2 (Periodontal Screening), RP-J26-IT-458

Read this file fully before writing any code. It is the single source of truth for this repository.
The final signed proposal report is the authority. If this file and any earlier assumption disagree, this file wins.

## 1. Who and what

- Owner: Vinuthan T (IT23311022), 3rd-year BSc IT, SLIIT. Stack background: MERN, some Python.
- Project: AI-Integrated Dental Health Assessment (team of 4). This repo is **Component 2 only**.
- Component title: Dual-Branch Explainable AI & Interactive Risk Simulator for Periodontal Disease Screening.
- Deadline: **PP1 on 22 Oct 2026**. Scope for PP1 is roughly 60% of the full plan. Today is early October 2026.
- Language: the owner talks in Tamil/English mix. Keep code comments and explanations simple and in plain English.

## 2. Hard rules about how to work (read twice)

The owner is assessed on understanding, not only on output. The course rule is: *if the student cannot explain, verify and defend it, it must not be presented as their work.*

1. **Explain before or right after every non-trivial step.** For each script, give a short plain explanation of what each block does and why, in language a 3rd-year student can repeat in a viva.
2. **Small commits.** One logical change per commit, meaningful message (e.g. `Add NHANES merge script with row-count log`). Never one huge dump.
3. **Never commit data or model weights.** `data/`, `models/`, `*.xpt`, `*.jpg`, `*.png`, `venv/`, `__pycache__/` must be in `.gitignore` before the first commit. Run `git status` and show it before committing.
4. **Verify outputs, do not assume.** Print row counts at every filtering step and compare with the known reference numbers in section 5.
5. **Log AI use.** After each task, append an entry to `docs/ai_log.md` using the template in section 9, and an entry to `docs/diary.md`.
6. **Do not invent results.** No fake metrics, no placeholder numbers presented as real. If something is not run yet, say so.
7. Ask the owner before any decision that changes scope, labels, or the predictor list.

## 3. What we are building (final scope)

Two **independent** branches. They are never merged into one score.

**Branch A — Vision.** Input: intraoral photo. Output: image-level Modified Gingival Index (MGI) grade 0–4, class probabilities, and Grad-CAM views (original, heatmap, overlay).
- Models: EfficientNet-B0 (candidate) vs ResNet-50 (baseline), plus a majority-class baseline.
- Dataset: Mendeley "A Dental Intraoral Image Dataset of Gingivitis for Image Captioning" (Duy et al., 2024), 1,096 images, published split 732 train / 182 val / 182 test, licence CC BY 4.0. https://data.mendeley.com/datasets/3253gj88rr/1

**Branch B — Questionnaire.** Input: questionnaire answers. Output: probability of **self-reported previous gum treatment** (target OHQ850), SHAP contributions, plus a constrained what-if re-inference.
- Models: XGBoost (candidate) vs regularised logistic regression, plus a training-rate baseline.
- Dataset: NHANES 2017–March 2020 pre-pandemic files `P_DEMO`, `P_OHQ`, `P_SMQ`, `P_DIQ`, linked by `SEQN`.

## 4. Things that must NOT be built or claimed

- **No fusion** of the two branches. Mendeley people and NHANES people are different individuals. Do not pair, join, concatenate or average image and questionnaire data or scores.
- **No 6–12 month forecasting / progression prediction.** Data are cross-sectional. The what-if feature is model sensitivity only, never a prediction of future health or treatment effect.
- **No periodontitis diagnosis claim.** MGI measures visible gingival inflammation, not attachment loss or bone loss. Do not map MGI to periodontitis stages.
- **OHQ850 is not "current disease risk".** It means previous gum-disease treatment (self-reported). Name it that way in code, variable names, UI strings and API fields.
- **OHQ850 must never be a predictor.** It is the outcome only.
- Do not use the YOLO `.txt` files as classification labels unless the class mapping has been audited (see section 6).
- Do not use SMOTE by default. Use class weights first.

## 5. Reference numbers to reproduce and check against

- NHANES `P_OHQ`: 14,986 rows. OHQ850 valid responses: 1,941 Yes + 5,876 No = **7,817**. (OHQ850 is only asked of age 30+.) Other codes (e.g. 9 = don't know) and blanks are not valid labels.
- An earlier merge of all four files with inner joins gave 11,137 rows. **Do not treat 11,137 as the modelling sample.** It is an intermediate count driven by which respondents appear in `P_SMQ`. The real final N must be produced by the audit and reported with every exclusion step.
- Mendeley: 1,096 images, 732/182/182.

## 6. Data rules

### 6.1 Image labels
- Each image has captions in the captions CSV (FileName, #, BS1). There are three caption variants per image describing per-tooth grades, e.g. "gingivitis 2 at position 13, 12".
- Target = **maximum grade mentioned** for the image, classes 0–4. Extract with regex, validate range 0–4.
- Some captions say "non-inflamed" or similar instead of "gingivitis 0". Treat as grade 0 **only after** looking at examples. Captions that are unclear or conflict go to a `needs_review` list, not auto-assigned. Do not assume missing label = grade 0.
- The YOLO label files use class IDs 0–6. The published description says 0 and 1 are region-of-interest classes and 2–6 correspond to MGI 0–4. **Audit this** with a few label files against their images before relying on it. The captions are the primary label source for now.
- Check for duplicate images (hash), duplicate filenames, and repeated participants across splits. Keep the published splits if there is no overlap; otherwise create and freeze a new grouped split and log why.
- Report per-grade counts per split. Expect imbalance.

### 6.2 NHANES cohort
- Eligible: age >= 30 (`RIDAGEYR`) and valid OHQ850 (1 = Yes, 2 = No). Map to 1/0. Drop refused / don't know / missing outcome. Never impute the outcome.
- Join plan to confirm with the owner: start from `P_OHQ` rows that are age >= 30 with valid OHQ850, then **left-join** DEMO, SMQ, DIQ on `SEQN`. An all-inner join silently drops respondents who were skipped by design in smoking or diabetes modules. Log row counts before and after every join, and unique-`SEQN` checks.
- Predictors (13 raw fields, becoming 12 inputs after smoking derivation):
  `RIDAGEYR, RIAGENDR, DMDEDUC2, DMDMARTZ, INDFMPIR, OHQ030, OHQ845, OHQ860, OHQ870, OHQ835, SMQ020, SMQ040, DIQ010`
- Smoking: combine `SMQ020` + `SMQ040` into one 3-level variable (fewer than 100 lifetime cigarettes / former / current). Respondents with SMQ020 = No skip SMQ040 by design; do not invent a value.
- **Excluded:** `OHQ850` (outcome), `OHQ555Q` (not an adult-behaviour predictor for this model).
- **Verify every variable's meaning and codes against the CDC codebook pages before use**; do not trust names from memory:
  - https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_OHQ.htm
  - https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_DEMO.htm
  - https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_SMQ.htm
  - https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_DIQ.htm
- Known quirks: `RIDAGEYR` 80 means 80 or older. `OHQ870` should be 0–7 days; values outside that (e.g. 9) are flagged, excluded from the main analysis and reviewed separately. `INDFMPIR` is a US-specific ratio; add a missing-value flag.
- Keep survey-design fields (`SEQN, WTINTPRP, SDMVSTRA, SDMVPSU`) for linkage and sensitivity analysis. They are never predictors.
- Split: stratified 80/20 participant-level split with a fixed seed. Imputation, encoding, scaling, feature selection and class weighting are fitted on the development set only. Median imputation + missing indicators for numeric, an explicit "unknown" category for categorical.
- Also compare two feature sets: all inputs vs without `OHQ835` and `OHQ860` (closely tied to treatment awareness).

## 7. Metrics and targets (provisional feasibility targets, not guarantees)

- Vision: macro-F1 (target >= 0.70), per-grade recall, confusion matrix, quadratic weighted kappa, ordinal MAE, macro AUROC, multiclass Brier. Compare EfficientNet-B0 vs ResNet-50 vs majority baseline using the same labels and splits.
- Tabular: AUROC (target >= 0.80), PR-AUC, sensitivity/specificity at a threshold chosen on development data, Brier score, calibration slope/intercept. Compare XGBoost vs logistic regression vs training-rate baseline.
- Do not compare against other papers' numbers as targets (different tasks, e.g. MIoU vs F1). Use them as context only.
- Never tune on the final test set. Report 95% intervals (bootstrap) where possible.

## 8. Explainability and what-if

- Grad-CAM for the image branch; show original / heatmap / overlay for the same predicted class. Use the last convolutional block of the chosen model. Describe heatmaps as model attention, not clinical boundaries.
- TreeSHAP for XGBoost. Record the unit (log-odds vs probability). Check that base value + contributions reproduce the model output within a tolerance. Do not describe SHAP values as percentage changes of a calibrated probability.
- What-if: only `smoking status` and `OHQ870` (interdental-cleaning days) may be changed. Age, sex, previous treatment, and other history fields are fixed. Validate combinations, include a reset, flag poorly supported scenarios. Always show wording that this is model behaviour, not proof that a behaviour improves health.

## 9. Repository layout and logs

```
component-2-periodontal/   (or repo root)
  data/            # NOT committed
  models/          # NOT committed
  notebooks/
  src/
    tabular/       # NHANES merge, preprocessing, models
    vision/        # label extraction, training, Grad-CAM
    explain/
  api/             # FastAPI (later)
  docs/
    diary.md
    ai_log.md
  requirements.txt
  README.md
  AGENTS.md
```

`docs/ai_log.md` entry template (one per task):
```
Date:
Tool: (Codex / Claude / other)
Task:
Prompt summary:
What was accepted / rejected:
How I verified it (row counts, output check, docs):
What I changed myself:
```

`docs/diary.md`: what was done today, why this design/method, what failed, what is next.

## 10. Environment

- Python 3.10+, virtual environment `venv`. Start with: `pandas numpy scikit-learn xgboost shap`.
- Vision work runs in Google Colab (GPU). Add `torch torchvision pillow opencv-python grad-cam` there. Resize images to 224x224 before uploading to Drive to save time (original set is about 6.5 GB).
- Later: `fastapi uvicorn`. Test endpoints with Postman.
- Files in `data/`: `P_DEMO.xpt, P_OHQ.xpt, P_SMQ.xpt, P_DIQ.xpt`, Mendeley folder with `Training/Validation/Test` each containing `Images/`, `Labels/`, and a captions CSV.

## 11. Plan to PP1 (22 Oct) — two key functions to demonstrate

PP1 needs two working, explainable, testable functions: (1) vision pipeline: photo -> MGI grade + Grad-CAM, (2) questionnaire pipeline: inputs -> probability + SHAP + basic what-if.

| Date | Work |
|---|---|
| Oct 7 | Setup, `.gitignore`, venv, folders, diary + AI log started |
| Oct 8 | NHANES audit: merge, filters, real final N, exclusion log |
| Oct 9 | Preprocessing + logistic regression baseline |
| Oct 10 | XGBoost, comparison table |
| Oct 11 | SHAP + what-if (Python functions) |
| Oct 12 | Image labels from captions, dataset audit, resized images to Drive |
| Oct 13 | Buffer, supervisor meeting (show tabular results) |
| Oct 14 | ResNet-50 baseline (Colab) |
| Oct 15 | EfficientNet-B0, same setup |
| Oct 16 | Grad-CAM three-panel output |
| Oct 17 | FastAPI image + questionnaire endpoints, Postman tests |
| Oct 18 | What-if endpoint, brief feedback from 3 people |
| Oct 19 | Test cases, risk register, README, architecture diagram (drawn manually by the owner, not AI) |
| Oct 20 | Evidence pack, logs catch-up, demo script |
| Oct 21 | Demo rehearsal and Q&A practice |

If behind, cut in this order: EfficientNet comparison (keep ResNet-50), what-if endpoint (keep as Python function), extra ceremonies. Never cut the two key functions.

## 12. First task for Codex

1. Create the folder structure, `.gitignore`, `requirements.txt` (pandas, numpy, scikit-learn, xgboost, shap), `docs/diary.md`, `docs/ai_log.md`. Show `git status`, then commit.
2. Write `src/tabular/audit_nhanes.py`: load the four `.xpt` files, verify variable names exist, apply the cohort rules in 6.2, print and save an exclusion log (counts at each step, unique SEQN checks, OHQ850 value counts) to `docs/nhanes_audit.md`. Do not train anything yet.
3. Explain the script block by block, then wait for the owner to confirm before committing.

---

## 13. Teaching mode (MANDATORY — owner must be able to defend every line)

The owner uses an agent for speed but must explain and defend all work at PP1 and viva. This is not "vibe coding": nothing is accepted that the owner cannot explain.

Before each step, tell the owner (simple words, Tamil/English mix is fine):
1. **What** you are about to do.
2. **Why** it is needed for the project (link it to the research goal or a rule in this file).
3. **Which tool/library/function** you will use and **why that one** over the alternative (e.g. why `merge on SEQN`, why stratified split, why `class_weight` instead of SMOTE).

While writing code:
- Keep scripts short and readable. One clear job per function. Plain variable names.
- Add a short comment above each important block saying what it does and why (not what the syntax is).
- Do not use clever one-liners or advanced tricks the owner may not know. If one is unavoidable, explain it.

After each step:
- Run the code, show the real output, and explain what the numbers mean.
- Point out the 2–3 "important lines" the owner must understand to defend this step, and give one likely viva question with a short answer.
- State any assumption you made and anything you are unsure about. Never hide a doubt.
- Add one entry to docs/ai_log.md and one line to docs/diary.md (owner fills "what I understood" in his own words).

If the owner asks "why?", answer fully before continuing. If the owner says "I don't understand", re-explain with a simpler example, then continue only when he confirms.

Never write code the owner has not had a chance to read first. Never claim a result you did not run.

Current project handoff: [docs/component2_project_handoff.md](docs/component2_project_handoff.md). Read it for verified current status and owner workflow preferences; it is context, not approval to change labels, splits or research scope.
