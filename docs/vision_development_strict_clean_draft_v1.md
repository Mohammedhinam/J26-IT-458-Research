# Development-only strict-clean manifest DRAFT v1

2026-10-14; branch `vinuthan`. **Non-activating, unapproved; zero training-authorised records.**

Authority: AGENTS.md §§3, 6.1, 7, 13; signed Component 2 proposal §§3.2–3.5 (PDF pp.17–22). Preserve RGB → image-maximum MGI 0–4 → Grad-CAM and the independent questionnaire branch. Reuse existing QA and reconciliation v2; no new dataset audit or label derivation.

## Exact draft accounting

| Development source split | Source records | Technical candidates | Held/excluded | Qualified-approved / authorised |
|---|---:|---:|---:|---:|
| Training | 732 | **680** | 52 | **0 / 0** |
| Validation | 182 | **53** | 129 | **0 / 0** |
| Total | **914** | **733** | **181** | **0 / 0** |

| Candidate image-maximum grade | Training | Validation | Development total |
|---|---:|---:|---:|
| MGI 0 | **0** | **0** | **0** |
| MGI 1 | **12** | **1** | **13** |
| MGI 2 | 84 | 13 | 97 |
| MGI 3 | 223 | 22 | 245 |
| MGI 4 | 361 | 17 | 378 |

These are technically consistent **candidate** labels, not accepted clinical ground truth or a frozen analytic cohort. The five original definitions and model outputs remain unchanged. Missing grade 0 cannot be learned/validated as a supported primary class; one grade-1 validation candidate cannot support reliable class-level conclusions.

## Conservative proposed rules

1. Require cached strict QA: three complete matching captions, no original/current review issue, supported image maximum and complete agreeing TXT grade histograms. TXT corroborates annotations; it is not an inference input or clinical truth.
2. Hold all unresolved caption cases. **Do not activate the optional upper-partial policy.** Technical policy candidates remain unapproved.
3. Hold entire proposed multi-image groups pending joint annotation/group decisions. Do not select a convenient labelled alias or activate proposed representatives/reservations. This protects known cross-split overlap without reading Test grades.
4. Hold both complete NP015 groups: Training `00591`, Validation `00736`. Retain uncertainty; no automatic merge or participant-independence claim.
5. Keep original IDs/splits, all exclusions, reason flags and group references. Every record retains absent qualified approval and unknown participant identity.

Disjoint exclusion accounting:

| Primary hold category | Training | Validation | Total |
|---|---:|---:|---:|
| Existing cached QA-review records | 47 | 128 | 175 |
| Additional multi-image companions outside that QA set | 4 | 0 | 4 |
| NP015 records outside the above sets | 1 | 1 | 2 |
| Total | **52** | **129** | **181** |

Four extra companions are Training `00272,00571,00584,00728`. Multi-image-group holds cover 26 development sources (25 Training, 1 Validation), of which 22 already occur in QA holds; they are not 26 additional exclusions. Protected-Test group flags and other source/QA flags overlap too. All reasons are retained per record; never sum overlapping reason counts into a cohort size.

## Artifact and safety semantics

New ignored directory:
`data/vision/gingivitis/staging-16669f74665ff0deca6ddd25feb0d233e52fdc2313265465bf91731af1e8956b/strict_clean_development_draft_v1_20261014/`

- `development_manifest_draft_v1.json`: all **914 development records**, including 181 holds and all reasons; proposed groups, original status/split/provisional values, candidate grades and label provenance references.
- `verification.json`: five focused draft checks, actual counts and manifest checksum.
- `build_recipe.py` / `check_recipe.py`: saved preparation/check recipes; rebuilding requires a new version/location, never overwriting the existing draft. They run no training and are not changes to the existing Vision implementation.

Candidate grade is in **`candidate_mgi_grade`**. Approved `mgi_grade`, `participant_id` and activated `analysis_split` are **null**; `qualified_label_approved`, `training_eligible`, `activated`, `training_ready` and approval flags are false. Candidate `proposed_analysis_split` only references unchanged original membership. No record has received a new label or approval.

Shared QA cache is filtered using its split metadata prefix: **Test objects are discarded before JSON deserialisation**, so their label/caption/histogram fields are not accessed. Reconciliation contributes only existing group membership and unresolved-link metadata, including an opaque protected-Test group list. No Test source record is included; no Test label counts, payloads, outcomes or inference inform this draft or the experiment plan.

All 733 candidate content groups are distinct, Training/Validation group sets are disjoint, and none intersects protected-Test or NP015 groups. This verifies **known content isolation only**: globally unknown participant identity remains a blocker.

## Remaining approvals and fastest next step

Required before actual training:

- Qualified approval of retained image-maximum labels, with real reviewer/date/evidence and caption/adjudication provenance; source consistency alone cannot fill those fields.
- Supervisor approval of conservative exclusions, group/split handling and exploratory supported-grade limitations; uncertain/source-adjudication cases can remain held rather than be automatically resolved.
- Genuine participant-identity/independence evidence required by the unchanged trainer. Content IDs cannot substitute. If unavailable, obtain a separately approved proposal-aligned resolution; this task changes no gate.
- New externally authenticated manifest approval and checksum freeze; separately signed exact experiment configuration, missing-grade acknowledgement and documented cached pretrained weights/runtime.

The candidate Validation subset is only 53 of the original 182 development-validation sources: exclusions may create selection bias, and scarce grades make metrics unstable. Neither five-class validity nor population/clinical generalisation follows from a prototype.

See the separate [exploratory ResNet-50 plan](vision_exploratory_resnet50_plan_v1.md). Once eligibility is authorised, reuse the existing trainer for one bounded head-only pilot and Training-rate majority baseline, then produce validation metrics and original/heatmap/overlay Grad-CAM for predetermined authorised development examples. No Test inference; no final-model claim.

## Verification and teaching

**5 focused draft checks passed; 0 failures/errors/skips.** Checked saved coverage/counts, synthetic Test-label non-deserialisation, known group/NP015 isolation, existing trainer rejection before image access and source/dirty-work preservation. Historical 59 selected Colab model/trainer cases were not rerun or combined with these checks as a repository-wide test count.

Important blocks: `candidate_mgi_grade` stores evidence without approval; whole-group holds prevent aliases crossing boundaries; `approved_partitions(draft, None)` rejects before images open. Viva: **Why can't we train on all 733 now?** They are technical candidates, while authenticated labels, participant independence, split and protocol approvals are still absent.

Original code, datasets, historical reports/manifests and review decisions are unchanged. Diary/AI log appended factually. No original source modification, package installation, model training, Test inference, commit or push.
