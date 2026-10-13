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

## 2026-10-10 — First development-only baseline experiment

### What was done

Read the attached AGENTS.md, existing preprocessing code/rules/tests and supplied proposal pages 19–22. Reused the frozen 6,251 development participants: 1,553 Yes (24.844025%) and 4,698 No. Added selective XPT loading that scans SEQN bytes and decodes only development records, reusing the audited zero fix. Audit/preprocessing reports and split-manifest hashes remained unchanged. Compared a training-fold prior DummyClassifier with fixed L2 logistic regression in identical shuffled seed-42 five-fold stratified cross-validation. Every training fold fitted its own fresh preprocessing/classifier Pipeline; each participant received one out-of-fold prediction. Eight new synthetic tests and the 15 existing tests passed (23 total).

Actual pooled OOF results: Dummy AUROC 0.499486, trapezoidal PR-AUC 0.398258, average precision 0.248216, Brier 0.186718, sensitivity 0 and specificity 1. Logistic regression AUROC 0.736721, trapezoidal PR-AUC 0.512827, average precision 0.513089, Brier 0.157823, sensitivity 0.292981 and specificity 0.936143. At threshold 0.50, logistic regression had TN=4,398, FP=300, FN=1,098, TP=455. Each fitted fold produced 47 encoded columns from 12 inputs. Saved the aggregate experiment design, measurements and fold class balance in docs/tabular_baseline.md; no participant predictions, models or datasets were committed.

### Problems faced

The original loader reads every participant, so a narrow selective reader was needed to respect the held-out predictor boundary. It depends on the installed pandas XPORT metadata/private IBM decoder; a synthetic XPT test verifies selection and original-row zero repair, and unsupported layouts fail explicitly. No install, fit or convergence failure occurred. The first logistic AUROC is below the proposal's 0.80 feasibility target, and sensitivity at 0.50 is low. The dummy's slightly varying fold priors and PR-curve interpolation mean pooled ranking/area figures are not identical to simple chance/prevalence references; average precision is reported separately.

### Decisions made

Predefined threshold 0.50 before running; classify positive at probability >=0.50. Fixed logistic C=1.0, default L2, lbfgs, max_iter=1000, class_weight=None, seed 42. No hyperparameter search, post-hoc calibration or threshold optimisation in this first experiment. These are unweighted internal development results for self-reported previous gum treatment; no diagnosis, current-risk, external-validation or final-test claim. Confidence intervals, calibration slope/intercept, survey-weighted sensitivity and awareness-feature ablation remain pending.

### Next step

Review the first baseline, then predefine development-only regularisation/class-weight and calibration/threshold comparisons, including the proposal's awareness-feature ablation. Keep the 1,563 final held-out participants reserved until all choices are fixed.

What I understood (my own words):

## 2026-10-12 — Baseline Planner evidence update

### What was done

Updated the local Planner table and copy-paste notes using the completed October 10 baseline report and verified commit 5dccc4b. Marked the first preprocessing/baseline milestone Completed; retained the actual metrics, low sensitivity and below-target AUROC. Existing 23-test evidence is from October 10, not a new run today.

### Problems faced

The local Planner table still showed baseline validation pending after the measured experiment had been completed. No external board update is claimed.

### Decisions made

Keep completion dates and evidence-update dates separate. Mark further tuning/calibration as pending; preserve reports and all untracked files.

### Next step

Write a bounded development-only comparison plan with explicit pending status and verification checks.

What I understood (my own words):

## 2026-10-12 — Next development experiment plan

### What was done

Wrote docs/tabular_development_plan.md with a proposed six-configuration L2/class-weight comparison, frozen development membership, identical five-fold validation, fresh fold preprocessing, metric outputs and focused verification checks. Included separate future calibration, threshold-selection and awareness-feature ablation stages. The plan is ready for owner review; the experiment is Not started.

### Problems faced

The first baseline's low sensitivity at 0.50 motivates further comparisons, but improved metrics cannot be assumed. Choosing a candidate using the same OOF results can make its selected score optimistic.

### Decisions made

Proposed C=0.1/1/10 and class_weight=None/balanced, with pooled average precision as the provisional selection metric and documented tie-breaks. Keep the current 12-input baseline unchanged. Calibration must be evaluated on participants whose labels were not used to fit the calibrator. Preserve final held-out data and original results.

### Next step

Review the specification, then implement and run the bounded comparison with focused tests. No training or new metrics were produced today.

What I understood (my own words):

## 2026-10-13 — Vision archive/caption precheck and extraction plan

### What was done

Prepared a read-only gingivitis archive/caption audit and a safe extraction plan. The primary archive contains 1,096 image entries, split 732/182/182, matching the proposal; captions contain 2,196/546/546 rows with three variants per image. Saved provisional maximum-grade distributions and all review filenames. Focused synthetic tests: 16 passed, zero failed.

### Problems faced

113 images have inconsistent explicit caption grade sets (47 validation, 66 test); 81 also disagree on the maximum (34/47). No provisional image-level MGI 0 labels were found. Unique filenames do not prove unique content or participant independence. Image hashing/decoding, near-duplicate review, participant metadata and YOLO mapping remain unverified.

### Decisions made

Kept ambiguous records as needs_review without dropping, relabelling or changing published splits. Streamed CSVs to memory only. Proposed ignored raw/staging locations and local manifests; no image extraction, resizing, upload, package installation or training. Preserved existing work and historical evidence; no commit or push.

### Next step

Owner reviews the extraction/full-content audit plan and the label/grade-0 blockers before approving further dataset preparation. Training requires separate approval after audit and label/split validation.

What I understood (my own words):

## 2026-10-13 — Safe Vision extraction and dataset-integrity audit

### What was done

Compared primary/backup archive SHA-256: both 16669f74665ff0deca6ddd25feb0d233e52fdc2313265465bf91731af1e8956b. Checked safe paths, links, advertised extraction sizes and disk reserve. Successful full regular-file integrity read covered 6,556,351,198 bytes; extracted only to new ignored staging. Verified 2,195 regular-file paths/sizes and all 1,096 RGB JPEG decodes, dimensions, byte/pixel hashes and caption/annotation references. Kept local per-image manifests/review records in ignored staging and added aggregate integrity report plus proposed label-review options. Final focused tests: 35 passed, zero failed.

### Problems faced

First all-entry integrity read failed because bsdtar tried to decompress ten directory entries; no extraction occurred in that failed attempt. Explicit regular-member selection passed on retry without ignoring errors. An annotation blank line was initially misflagged as invalid; minimally fixed parser and refreshed annotation-only evidence without repeating image decoding/hashing. Preserved the initial audit snapshot; audit_verified is the current evidence.

Found 14 exact duplicate pairs (28 entries, 1,082 unique byte contents): six within training, seven train-test and one train-validation. Three pairs disagree on caption maxima. Caption variants conflict for 113 images, including 81 maximum disagreements; seven caption-versus-mapping-hypothesis discrepancies and sixteen non-12 tooth-box annotations remain unresolved. Final needs_review union: 161 images (34/53/74), with overlapping reasons. All published tooth-code count comparisons (codes 2–6) mismatch local counts. No supported image-level maximum-0 example; code-2 normal tooth boxes do not establish whole-image MGI 0. Participant identifiers are not supplied/documented locally; paper's independence claim does not establish clean splits in the presence of exact duplicates.

### Decisions made

Preserved all original archives, images, captions, annotations and published split memberships. No target repair, automatic missing-to-zero rule, final class mapping, record exclusion, resplit, training, package installation, commit or push. Raw/pixel hashes and exact dHash equality identify duplicates; transformed near duplicates are not comprehensively ruled out. Final-test images were accessed only for the approved integrity/label audit, with no fitting or model selection. Historical evidence and prior work preserved.

### Next step

Request owner/supervisor approval for label adjudication and a duplicate/group-handling plan, including absent-grade-0 feasibility and mapping verification. Do not train until these blockers are resolved, a proposal-aligned manifest is approved, and separate training approval is given.

What I understood (my own words):

## 2026-10-13 — Focused Vision label verification and duplicate-handling plan

### What was done

Read proposal pages 17–18/22, supplied AGENTS.md and existing Vision evidence. Reused extracted CSV/TXT and cached inventory; visually inspected three original training photos. Technical mapping 0/1 ROI and 2–6 MGI 0–4 is corroborated by spatial/caption examples, especially 00029. Computed separate raw tooth-box and diagnostic image-maximum frequencies from cached evidence. Reconciled historical needs_review union: 113 caption conflicts + 7 caption–TXT discrepancies + 28 duplicate entries + 13 other tooth-count issues = 161, with secondary overlaps accounted for.

### Problems faced

All three variants of the seven caption–TXT discrepancies were inspected. Four have empty tooth lists for their numeric maximum-grade phrases; three are substantive source disagreements. Current numeric parsing does not prove the phrase describes an actual tooth. One sampled provisionally unflagged photo also has tooth-level source differences despite equal maxima; historical inventory stays unchanged and is not an exhaustive adjudication queue. There are 309 raw normal-tooth boxes but no supported image maximum-0 examples. Clinical grade correctness and participant independence remain unverified. Live paper refresh hit CAPTCHA/403; used signed proposal and previously recorded source content.

### Decisions made

Prepared docs/vision_label_verification_duplicate_plan.md with decision table and approval checklist only. Proposed a versioned non-destructive group-aware analysis manifest, original-test reservation and label-blind duplicate representative rules. Known-duplicates-only scenario gives 718/182/182 unique contents; this is not an implemented split or final eligible sample. Supervisor must approve content-group versus participant-group limitations and absent-class-0 scope. Maximum remains the proposal target provisionally; no placeholder repair, new class mapping, label edit, data/code change, exclusion, resplit, training, installation, commit or push occurred. No new tests or full audits run; read-only ledger/count assertions passed. Historical code/reports/data and dirty work preserved.

### Next step

Wait for qualified reviewer/supervisor approval on mapping, caption adjudication/parser rules, MGI-0 feasibility and duplicate/group policy. Implementation and later training require separate authorization.

What I understood (my own words):

## 2026-10-13 — Read-only evidence review of 161 flagged Vision records

### What was done

Compared 483 original CSV captions, 161 original TXT files and 161 original RGB sources. Prepared an ignored local HTML case report, full-evidence reviewer CSV/JSON, exact referral lists, duplicate-group comparisons and 27 final RGB contact sheets. Visually screened all 27 source/overlay sheets; full-resolution originals remain linked for qualified review. Filename/variant checks passed. No source or approved target was changed.

### Problems faced

All 113 caption-conflict cases have twelve supported sites in captions 1/2 and only the six upper sites in caption 3; lower-jaw descriptions are omitted. Four maximum-grade discrepancy cases have empty tooth lists. Duplicate-companion review found eleven pairs with different complete positional tooth-grade maps and three pairs with ambiguous/incomplete box coverage. Seventeen records are individually source-consistent but none is cleared group-wide. A footer-layout clipping issue was corrected only in newly generated contact sheets. Positional sorting/parsing is a screening hypothesis, not verified tooth identity or clinical diagnosis.

### Decisions made

All 161 remain needs_review; resolved count zero. Forty-eight image records (34 distinct cached photo contents, not verified people) are listed for qualified dental/tooth-annotation adjudication: 28 duplicate entries + 13 other box-count issues + 3 substantive caption–TXT disputes + 4 unsupported maximum-grade phrase cases. The other 113 require incomplete-caption policy approval and dental escalation if needed. No automatic first-caption selection, majority voting, missing-to-zero assignment, new grade, exclusion, resplit or training. Final-test cases were audit-only, never development/model selection. Preserved original RGB colours, source files/manifests, splits and prior working-tree content.

### Next step

Owner approves qualified reviewer involvement and annotation-policy adjudication using the case report, source photos and provenance. Label changes, duplicate/group handling and any training still require separate explicit authorization.

What I understood (my own words):

## 2026-10-13 — Focused 113-caption reconciliation and Vision publication

### What was done

Reused the existing 113-record reviewer list and caption evidence. Caption 1/2 source text agrees at all twelve positions in each case (1,356 paired positions); Caption 3 equals the upper-jaw prefix and agrees at all six shared positions (678 positions). Recorded split counts and independent raw-clause checks in docs/vision_incomplete_caption_reconciliation.md. Owner subsequently requested publication of the existing Vision audit/review work as scoped commits. Publication verification: 35 synthetic Vision tests passed, zero failed; no real-data audit or extraction rerun.

### Problems faced

Historical 81 maximum differences and 32 same-maximum grade-set differences reflect lower-jaw omission in this subset. Double commas in 35 records did not prevent explicit-site parsing. An initial auxiliary numeric-only parser did not cover non-inflamed wording in eight records; adding literal source-wording handling to the in-memory check resolved that check limitation without modifying source evidence or grades.

### Decisions made

All 113 remain needs_review, with no approved grade. Zero source-position disagreements or remaining unparseable cases were identified under the stated checks, not a clinical validation claim. All 113 may be considered under a supervisor-approved incomplete-caption policy; uncertainty requires qualified review. Criteria must be predefined and must not be tuned against final-test outcomes. TXT is verification evidence only. Raw images, CSV/TXT and local reviewer artifacts remain ignored. Unrelated pending tabular work and original split/label evidence are preserved.

### Next step

Obtain supervisor/qualified reviewer approval for annotation policy, the separate 48 adjudication cases, duplicate/group handling and absent image-level MGI 0 before any training. No policy implementation or training is authorized by publication.

What I understood (my own words):
