# Isolated PP1 exploratory scaffold — v1

2026-10-14; `vinuthan`. **Implementation/dry-run only. Real dental image packaging, model training and inference remain unauthorised.**

Every pilot result states: **Provisional labels; non-clinical; non-final; participant independence unverified.**

## Files and reuse

- `src/vision/exploratory_bundle.py`: fixed-DRAFT candidate selection; development-only cached hash projection; source/path/SHA dry-run; separately opt-in packaging and safe bundle validation/extraction.
- `src/vision/exploratory_pilot.py`: separate opt-in provisional adapter/runner; reuses existing model factory, preprocessing, `_fit`, metrics, frozen-backbone/BatchNorm and Grad-CAM. Adds scoped provenance, majority baseline, unsupported-class warnings and checkpoint integrity checks.
- `tests/test_exploratory_bundle.py`, `tests/test_exploratory_pilot.py`: generated RGB/metadata only; synthetic ownership fixtures are not real approvals.
- `docs/vision_pp1_exploratory_colab_v1.ipynb`: new runtime workflow; real-data run OFF by default.
- `docs/vision_pp1_exploratory_code_v1.zip`: six current source/test files and SHA manifest; **no images, labels, weights or datasets**.

Existing `model_pipeline.py`, `train_pipeline.py`, their approved-research gates, historical tests/reports and source DRAFT are unchanged. Exploratory numerical targets do not become approved labels. No fake qualified reviewer or participant IDs are supplied.

## Actual dry-run findings

New ignored directory: `data/vision/pp1_pilot_dry_run_v1_20261014/`.

`dry_run.json` and `source_plan.json` record **733 candidate source hashes MATCH**, **680 Training / 53 Validation**, **4,427,774,122 source bytes**, **0 RGB decodes**, **0 packaged images**, no Test payload reads or approvals. Cached audit projection reads only development path/hash/dimension fields; annotation fields and Test rows are not decoded. This selected-source SHA check is bundle preflight, not a new full dataset audit.

The builder pins the original DRAFT SHA and candidate identity/group/grade digest. All 181 holds stay outside the plan. Entire multi-image groups, protected-Test groups and both NP015 groups remain excluded; no original source membership or label changes. Known content isolation is checked; unknown participant independence is not claimed.

Current candidate grades MGI 0–4 are Training **0/12/84/223/361**, Validation **0/1/13/22/17**. No whole-image MGI 0 support; one Validation MGI 1 record. Undefined recall/AUROC stay null and five-class validity remains false. Source consistency is not qualified clinical validation.

## Local verification and weight blocker

Focused new suite: **58 passed, 0 failed/errors, 2 skipped**. The two skips are new PyTorch synthetic adapter/checkpoint reload and foreign-checkpoint provenance cases; local torch/torchvision are unavailable. These cases have **not** been verified in Colab yet. Historical 59 selected v1/v2 cases do not validate this new wrapper, nor represent scientific model performance.

Passed coverage includes scope/hash opt-in rejection, original research gate rejection, held/NP015/content isolation, malformed manifests/grades, source/path/link checks, package contents/tampering, synthetic extraction, tensor-equivalent RGB derivatives, five-grade mapping, missing-class metrics, Training-only majority, byte-integrity rejection before checkpoint deserialisation, and mandatory CAM notices. Real dental packages/models were not created.

Required documented source: `ResNet50_Weights.IMAGENET1K_V2`, file `resnet50-11ad3fa6.pth`, official URL `https://download.pytorch.org/models/resnet50-11ad3fa6.pth` ([TorchVision v0.26 source](https://github.com/pytorch/vision/blob/v0.26.0/torchvision/models/resnet.py)). Local expected cache `/Users/vinuthanvinuthan/.cache/torch/hub/checkpoints/resnet50-11ad3fa6.pth` is **missing**. No repository `models/` directory or supplied checkpoint was found in this check; Colab cache is not yet inspected. No weight download/load attempted. Runtime preflight reports status rather than silently downloading or using random weights.

## Next single executable step — code only

1. Upload the new `.ipynb` to a fresh Colab runtime; no Drive mount. Upload **only** the new code-only ZIP when prompted.
2. Execute source-SHA, environment and synthetic-verification cells. Compatible installed dependencies are reused; no pip cell exists.
3. Obtain actual new test results, runtime versions/JUnit/logs and downloaded `vision_pp1_scaffold_runtime_evidence_v1.zip`. Acceptance: all **60 selected new cases** pass with zero failures/errors/skips, unchanged source hashes. Do not claim this until executed.
4. **Leave `RUN_PILOT=False`.** No real data is requested by the authorised verification cells; absent pretrained weights do not block synthetic `weights=None` checks.

The later pilot cell exists but requires separate hash-bound owner run authorisation, an isolated development ZIP and approved documented cached/supplied weights. It refuses a Drive mount, CPU fallback, extra payloads and wrong source/bundle/config/weight/run identity. Changing a notebook boolean alone grants no valid authorisation.

## Separate future approval: packaging, then execution

Two unsigned templates are saved under the ignored dry-run directory. They contain **pending** status, blank authorizer/date/evidence and false acknowledgements; they are not approvals. Record a real owner decision before filling them. The records document opt-in, not cryptographic authentication or clinical sign-off.

**Packaging approval wording:**

> I authorise copying/resizing only the pinned 680 Training and 53 Validation candidates into the isolated development bundle `pp1_dev_bundle_v1_20261014`, plus the three eligible Validation originals 00733/00734/00766. Keep all holds and Test files excluded; preserve originals/labels/splits. This authorises packaging only, not training, inference, weights downloads or final manifest activation.

After that decision, populate `package_authorization.json` from its template with actual owner/date/evidence and the exact DRAFT, source-plan and code hashes. From the repository root, using the existing bundled Python (no installation):

```bash
task_pilot_python=/Users/vinuthanvinuthan/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3
task_pilot_staging="$PWD/data/vision/gingivitis/staging-16669f74665ff0deca6ddd25feb0d233e52fdc2313265465bf91731af1e8956b"
```

**Do not run this packaging command today:**

```bash
"$task_pilot_python" -B -m src.vision.exploratory_bundle \
  --draft "$task_pilot_staging/strict_clean_development_draft_v1_20261014/development_manifest_draft_v1.json" \
  --hash-inventory "$task_pilot_staging/audit_verified/integrity_results.json" \
  --source-root "$task_pilot_staging" \
  --output "$PWD/data/vision/pp1_dev_bundle_v1_20261014" \
  --package --opt-in \
  --authorization "$PWD/data/vision/pp1_pilot_dry_run_v1_20261014/package_authorization.json"
```

The builder rechecks source bytes, RGB/dimensions and tensor equivalence, writes only a fresh ignored location, then verifies and ZIPs the allowlisted package. No source files, annotations or Test records are included. Its final archive/manifest hashes are required for the next approval.

**Pilot approval wording, only after package/runtime/weight preflight:**

> I authorise exactly one isolated exploratory ResNet-50 head-only run `pp1-v1-run01` using the verified bundle/config/code and documented pretrained checkpoint hashes. Labels stay provisional; this is non-clinical/non-final and participant independence unverified. Retain five MGI definitions, disclose unsupported MGI 0/scarce MGI 1, preserve Test isolation and all holds. Allow only the three fixed development Grad-CAM examples after best-checkpoint restoration; no final research approval or model promotion.

Complete `run_authorization.json` with the actual archive/manifest SHA, current code digest, fixed configuration digest, full weight SHA and official URL, source DRAFT SHA, fixed run ID and real owner/evidence/date. Then use the later notebook cell; it requires opt-in and refuses reusing an existing run directory. Missing weights require separate approval to supply the exact official checkpoint; no automatic download. Packaging approval alone is insufficient to run.

Profile: ResNet-50/five logits, frozen backbone/BatchNorm, seed 42, batch 16, LR 0.001, Adam, at most 5 epochs, patience 2, no class weighting/augmentation/fine-tuning/search. Reuse Validation metrics and Training-only majority; preselected CAM at `layer4[-1]`. All results/checkpoints/CAM artifacts carry the exact provisional notice. Any grade-0 prediction is tagged unsupported, not a confirmed healthy mouth.

This separate engineering opt-in does not satisfy qualified labels/participant-independent validation or the approved-research API. Those scientific approvals remain pending. No supervision requirements, original research objectives or questionnaire definitions are rewritten.

Teaching: `select_candidates` keeps holds and groups out; scoped `authorise` distinguishes implementation, packaging and running; checkpoint SHA/provenance binds results to the actual provisional experiment. Viva: **Does approving this pilot approve its clinical labels?** No—engineering permission and clinical/research approval are separate, and the approved API still rejects the DRAFT.


## 2026-10-14 — PP1 exploratory scaffold Colab evidence and packaging preflight

Saved new Colab evidence has now been verified: **60 passed, 0 failed, 0 errors, 0 skipped**, Tesla T4 runtime; six current source hashes and code-bundle bytes match. The historical local two skips above are resolved for the unchanged v1 snapshot. See [verified evidence](vision_runtime_verification_results.md). No repeat test execution or dental training took place in this update.

**Do not execute the earlier v1 packaging command or approve its template yet.** New packaging preflight confirms 680/53 candidates, all 733 hashes, holds/NP015 and known group isolation, but detects GPSInfo/opaque metadata in all three planned CAM originals. The current verbatim JPEG copies preserve that metadata. A scoped metadata-safe export/attribution/payload-hash revision, new verified code binding and actual separate owner packaging authorisation are needed first. See [preflight and next approval](vision_development_packaging_preflight_v1.md). No source code, source image, label, split or signed approval was changed; RUN_PILOT remains off.

Targeted GPS clarification: all three selected CAM originals contain only GPSVersionID, no latitude/longitude or GPS time/date fields. No location leak or patient identity is asserted. The packaging review blocker concerns nonempty DateTime/opaque MakerNote metadata copied verbatim, with no export sanitisation policy or verification.


## 2026-10-15 — Metadata-safe exploratory export revision v2

Owner authorised only the scoped export revision/generated-image checks. Current guide: [metadata-safe export v2](vision_metadata_safe_export_v2.md), new code-only `vision_pp1_metadata_safe_code_v2.zip` and metadata-only `vision_pp1_metadata_safe_verification_v2.ipynb`. The revised bundle schema replaces CAM JPEG byte copies with lossless full-resolution RGB PNGs and separate source/export/pixel hashes, strict metadata/chunk checks and mandatory CC BY attribution. Historical v1 notebook/bundle/evidence remain unchanged; their 60-pass source snapshot is not the new revision.

Actual local affected selection: **73 passed, 0 failed, 0 errors, 0 skipped**. No completed Colab workflow rerun, model operations or real image exports. New notebook has not executed in Colab and stays RUN_PILOT=False. The three real permitted CAM headers have embedded ICC and EXIF ColorSpace=65535, orientation=1; the fail-closed colour guard rejects them before any packaging output. No GPS coordinate fields were found previously. A reviewed colour-preserving profile policy and separately recorded packaging-only permission are still required; do not use old unsigned/hash-bound templates or strip ICC silently.
