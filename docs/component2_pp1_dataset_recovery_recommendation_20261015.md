# Component 2 PP1: dataset recovery and completion recommendation

2026-10-15 · branch `vinuthan`. Advice/plan only;no dataset access,new training,approval activation,commit or push. Reuses the actual three B1 pilots and existing cached QA/grouping evidence;the old Oct14 no-training statements remain historical.

## Where the project stands

The Vision model/Grad-CAM/trainer and guarded B1 colour/privacy packaging work. Three owner-authorized exploratory runs completed on680provisionalTraining/53Validation. Latestv3correct27/53,accuracy0.509434,macroF1.325872;Grade2recall1/13andmacroAUROC.627264remainweak. This is an executable exploratory prototype,not validated five-grade or clinical performance. NHANES audit/preprocessing,Logistic/XGBoost comparisons and development calibration are documented;baselineAUROC.736721andXGBoostA.739398are internal results,not achievement of0.80. SHAP,controlledWhat-if,finalprotocol/evaluation and user-facingintegration remain pending according to current records. No fused output or current-disease/causal/forecasting claim.

## Correct source accounting: 181held development images,not183

| Disjoint category | Training | Validation | Total |
|---|---:|---:|---:|
| Upper-partial-caption policy candidates |2|119|121|
| Other qualified annotation referrals |45|9|54|
| Additional multi-image companions outside QA |4|0|4|
| NP015 unresolved identity sources outside above |1|1|2|
| **Held development union** |**52**|**129**|**181**|

The current pilot uses680+53=733of914development sources. The182original final-Testimages are separate and remain protected. The274all-splitpolicycandidates comprise121development+153Test;do not add274to181or moveTesttoTraining. Full339QA=274policy+65otherreferrals;these are overlapping views of the existing holds,not additional failures. Original held images were preserved,not deleted. Sources: [strict draft](vision_development_strict_clean_draft_v1.md),[qualified review package](vision_qualified_review_package_v1.md),[content reconciliation](vision_content_reconciliation_plan_v2.md).

## Solved versus unresolved

| Issue | Present status | Practical treatment |
|---|---|---|
| ICCv2/source compatibility,privacy,B1unclipped model input,package integrity | Qualified engineering pathway and actual733-imagepackage succeeded;OptionAfailed/frozen | Reuse B1;do not repeat colour work or claim clinical colour fidelity |
| Exact/near-duplicate detection and54ownerdecisions | Completed;14exactpairs,sixhuman-sameedges,reconciled1076contentgroups | Preserve decisions;protect8cross-splitgroups and uncertainNP015;qualified group/split approval and participant independence remain unresolved |
| Incomplete Caption3 | Optional verification mode identified274technical candidates | Review proposed policy and development121cases;require record-level label/provenance approval,not automatic acceptance |
| Other caption/group issues |54developmentreferrals+4companions+2NP015held | Qualified individual/joint adjudication,source clarification or retain hold;no majority/model-based auto-label |
| Missing whole-imageMGI0 | No supported whole-imagezeroexamples;309source-annotatedzero toothboxes are a different task unit | Seek genuine comparable qualified whole-imageMGI0 evidence;do not label wholeimages healthy from a healthy tooth |
| ScarceMGI1 and Grade2regression |12Training/1Validationgrade1;v3Grade2correct1/13 | Preserve per-grade reporting;no guaranteed architecture,weighting or epoch fix established |

## What research sources add

The dataset's original paper describes MGI annotations per tooth and three image captions,not an automatically validated whole-image maximum classifier. This explains why tooth-level grade0support does not imply a whole-image grade0example under our signed maximum rule. It does not excuse conflicting records or authorize a new target. [Original dataset paper, §§3.3–3.4,4.3–4.4](https://pmc.ncbi.nlm.nih.gov/articles/PMC11462013/).

External lead: [MIO v1 source record](https://zenodo.org/records/21140854) describes765photographs with Healthy/Gingivitis/Periodontitis categories,not an MGI0–4label schema. Its rendered licence field did not expose a definite licence value in this review;there is a newer-version link,but its resolution failed. This is a lead only,not a cleared training source. Comparable whole-image grading,licence/consent,participant/content independence,source/camera confounding and owner/supervisor approval need verification before any use. No data downloaded. A [2024MGIgradingstudy](https://www.nature.com/articles/s41598-024-70311-y) explicitly says its underlying images are not publicly available owing to patient privacy;the publication is not a ready-to-download solution. This focused search did not establish an immediately usable,qualified external whole-imageMGI0cohort;it does not prove none exists.

## Recommended priority change for PP1

A seed43replication remains an optional bounded stability proposal,not a solution to held labels,missingMGI0or participant independence. For the user's broader completion goal,prioritize **development-data rehabilitation and completing the two demo functions** before another tuning loop.

1. Reuse the existing qualified-review package to prepare a concise development-only decision request:52heldTraining first,and the121partial-policyqueue(2Trainingoverlapwiththose52;119Validation). Qualified reviewer/source authors clarify clinical consensus/annotation provenance;supervisor approvesmethodologicalgroup/split/policychoices. No need to repeat54pairreview. Published annotation authors may clarify/export their consensus labels and participant/source records;do not send messages without owner authorization. Some duplicates may contribute one independent representative rather than all aliases;protectedTest/NP015cannot simply return toTraining.
2. After actual decisions,write a NEW versioned eligible-development draft,retain everyoldID/split/holdreason,check independence and grade support,then seek fresh separately hash-bound packaging/training permission. A policy decision alone is not per-image clinical approval. Do not change existing733manifest or let a changed53-casevalidationcohort retroactively replace historicalscores.
3. Recovering the121policycases would mainly help Validation coverage,not add121Trainingexamples:only2areoriginalTraining. Even recoveryofall52heldTrainingwouldnotguarantee MGI0support or better accuracy. Exact recoverable counts/grades are not yet known. Do not reinterpret missing/ambiguous labels as zero or moveValidation/Testcases intoTraining to inflate training size.
4. In parallel,complete the independent NHANESSHAP/controlledWhat-if and demo/API work from existing development evidence;use the current Vision result only as explicitlyprovisionalMGI1–4exploratory demonstration with unsupportedMGI0anduncertainty disclosed. Preserve original five-grade research definitions and qualified research-training gate. Freeze a final protocol before final held-out evaluation;avoid promising a clinical classifier by the PP1deadline.

**ONE next practical action:**use the existing cached package to create a compact development-only recovery/decision sheet for the52heldTrainingrecords,with links to the already prepared121partial-policycases. It must classify review requirements and retain everyhold;it does not clear labels,activate a policy or train. No original image/TXT/CSV audit needs repeating. This focuses human effort on actual blockers while independent demo work can proceed.

Viva:Why not add all181back now? Some labels are unresolved and some sources share protectedcontent/unknownidentity. More images with uncertain labels or overlap can make reported scores misleading;qualified,source-accounted recovery is needed. A working pilot and a validated research model are different milestones.
