# Option A v4 — generated-image export integration

2026-10-15; branch **vinuthan**. Authorized scope: versioned export-path integration and generated-image verification only. **131 selected tests passed; 0 failed, 0 errors, 0 skipped (2.03 s)** on the existing Mac CPU runtime. No real dental image/header was opened, decoded, exported or packaged; no Test payload, upload, model execution, install, download, commit or push. This is neither a full repository test run nor a new Colab result.

## Explicit version boundary

New `src/vision/exploratory_bundle_v4.py` provides the separately opt-in `package_development(draft_path, inventory_path, source_root, output_dir, authorization, opt_in=False)` and `validate_bundle(root, expected_manifest_sha256)` APIs. Version: `pp1-exploratory-bundle-v4-option-a`; permission scope: `package_development_option_a_v4`. Importing the module does not start packaging. No actual owner permission record was created.

The v3 public API still uses `ROUNDTRIP_LIMIT=2`. Its PNG encoder and structural/file validators were minimally factored into private shared functions; each public API fixes its own version and colour validator. There is no automatic version dispatch, fallback, exception-based retry or per-image relaxation. v3 rejects v4 bundles. The historical pilot/extraction reader consequently remains incompatible with v4: a separately scoped consumer update/verification is required before a future real pilot. Model, trainer and research-training approval gate are unchanged.

| Frozen v4 gate — all required | Enforcement |
|---|---|
| Mean ΔE76 +0.01 ≤0.50 | Existing Decimal comparison with effective limit 0.49 |
| P99.9 enclosing upper bound +0.01 ≤1.00 | Effective limit 0.99; never midpoint/lower edge |
| Maximum ΔE76 +0.01 ≤2.00 | Effective limit 1.99 |
| Out-of-gamut count ≤floor(N/1000) | Integer count; epsilon remains 1e-6 |
| Out-of-gamut fraction ≤0.001 | Exact `1000*C <= N`; mathematically equivalent to count gate |
| Maximum normalized excursion ≤2/255 | Existing isolated evaluator, unchanged limit |
| Integrity, privacy, geometry, supported profile, authorization and development isolation | Actual pinned selection, file/hash/header/conversion/output checks, not supplied passing booleans |

Frozen evaluator ID remains `pp1-option-a-isolated-v1-20261015`. Policy specification SHA-256: `b90937f2a7255a58ac65b3efb77ce58f03ec3865a9e0b096d48f6e27f639cc6a`. The unchanged pure evaluator still grants no authorization; v4 calls it only after its own checks.

## Actual checks and evidence trust

Before source access, v4 requires explicit opt-in and the new owner scope, rebuilds the plan from the pinned DRAFT/evidence, verifies the exact candidate identity, counts/grades, **181 holds**, protected/uncertain groups and fixed CAM membership. Current code, frozen policy, DRAFT, source plan, version and a fresh output ID must match the separate authorization. The pinned contract remains **680 Training +53 Validation**, three eligible CAM copies, no NP015, known overlapping content or Test. These are enforced future-input requirements, **not a new live verification of 733 dental files today**.

A tiny generated sRGB→D50 Lab reference qualifies the installed LittleCMS path before image access. Mac reference maximum discrepancy: **0.000010747529010839687 ΔE**, below its independent 0.01 numerical qualification allowance. Runtime: Python 3.12.14, Pillow 12.3.0, NumPy 2.3.5, pytest 9.1.1, LittleCMS 2.19. No dependency installed.

Future authorized export runs existing original-file SHA/header checks, then measures the actual supported source ICC→sRGB conversion at full resolution with tiled QA. Every composite condition must pass before writing that source's first derivative. Reverse RGB statistics remain diagnostics. Fresh RGB lossless PNG encoding retains only the fixed non-identifying sRGB declaration; actual geometry, decoded pixels, PNG chunks/CRC and payload hashes are verified. Full CAM copies must match the checked full-resolution managed pixels. Original source hashes are checked before QA, after QA and after export. Private metadata values/profile bytes are not written into receipts.

Per-source receipts bind source/managed pixel hashes, actual exported payload hashes, QA digest, geometry, original/final source hashes and checked cohort/hold/group/runtime/authorization references. The post-export verifier reruns the same composite gate, validates receipt bindings and actual PNG payloads/metadata, and rejects extra/missing files. A later failure stops the attempt; no row is silently dropped and no completed ZIP is produced. Partial derivatives, if any, are retained as an incomplete attempt, never promoted to an approved package.

**Trust boundary:** references are created internally after checks; a caller cannot provide `checks=True` instead of running them. Offline verification requires an independently trusted manifest SHA and matching code. It checks recorded source QA plus actual payloads; without originals it cannot independently remeasure source colour, prove an owner identity or detect a forged entire provenance chain whose replacement hash is also trusted. SHA binding is integrity protection, not institutional attestation. CC BY 4.0 dataset attribution/DOI/licence and the explicit bounded-loss transformation notice are retained.

## Focused generated verification

| Selected file | Passed | Failed/errors/skipped |
|---|---:|---:|
| `tests/test_exploratory_bundle_v4.py` — new integration checks | 40 | 0/0/0 |
| `tests/test_exploratory_bundle.py` — affected shared/legacy checks | 70 | 0/0/0 |
| `tests/test_icc_colour_export.py` — affected legacy ICC/PNG checks | 21 | 0/0/0 |
| **Total selected** | **131** | **0/0/0** |

The first 122-case run passed; nine additional focused source/receipt/guard checks produced the final 131-case result. Tests use generated images, synthetic-only permissions and a four-selected-record miniature cohort with 181 synthetic held records. They do not pretend to verify real candidate labels or actual source counts. Independent generated fixtures/oracles from earlier qualification are reused; their complete 40/71-case suites and prior Colab runs were not repeated.

Checks include each independently failing forward/severity criterion and both equivalent extent conditions, pre-write/post-write agreement, a generated shadow fixture whose reverse error exceeds 2 (v3 rejects; qualified v4 accepts), actual incorrect-transform measurement, severe clipping, malformed ICC, ambiguous orientation, source hash/geometry mismatch, held/NP015/protected/duplicate/Test rejection, false approval/boolean claims, old scope/stale code/policy/version/plan permissions, missing opt-in, altered receipts/groups/QA/pixels/metadata/manifest, extra Test files, runtime-reference failure and incomplete-attempt behaviour. Source fixture bytes stay unchanged; labels remain provisional.

Ignored local evidence: `data/vision/option_a_export_v4_20261015/tests.log`, `junit.xml`, `artifacts.json`, `package_collection.log` and preservation/verification JSON. The test run's 40 new checks are distinct from the earlier helper's 40 tests.

## Code-only Colab handoff — not executed

- Notebook: `docs/vision_option_a_export_verification_v4.ipynb`.
- ZIP: `docs/vision_option_a_export_code_v4.zip` — **58,504 bytes**, SHA-256 `1c512d1fc29c9c1b3eae55750a89a47e8ce5ad09a4fad9042c4676fff8e3e00e`.
- Eleven code/test file hashes match the current workspace; exact ZIP allowlist/CRC and Python/notebook syntax pass. In an isolated extracted code directory, **131 tests collect successfully**; collection is not another passing execution.
- Open a fresh **CPU Colab** runtime, upload only that code ZIP when prompted, and run notebook cells in order. Existing NumPy/Pillow/pytest/LittleCMS are detected; missing/incompatible dependencies stop, with no installation or fallback. No Drive mount, dental data, weights, owner packaging record or GPU is needed.
- Acceptance: 131 passed, zero failures/errors/skips, unchanged eleven hashes. Download `vision_option_a_export_runtime_evidence_v4.zip`, including actual environment, stdout and JUnit results. No Colab success is claimed here. `RUN_PILOT=False` and no training invocation remain explicit.

## Packaging blockers and next action

Real packaging remains inactive. It needs a **fresh, explicit local-development-packaging-only owner decision** accepting bounded exploratory colour loss, the new scope/version, current code/policy/DRAFT/plan hash bindings and a never-used output ID. Existing v3 permission is insufficient. Applicable data-use/privacy requirements must still be satisfied. Future real preflight and every source's actual composite check must pass; today's synthetic run does not guarantee all 733 will pass. No automatic exclusion, threshold widening or replacement is allowed on failure.

Missing MGI 0, scarce MGI 1, provisional labels, participant-independence uncertainty, pending clinical/methodological approvals and final research eligibility remain unresolved. Numerical engineering budgets are not clinically validated colour limits; source ICC accuracy, lighting and localized clinical relevance remain unknown. No final manifest, label approval or model-performance claim is created. Upload, a v4-compatible pilot reader and training are separate scopes.

**ONE next action:** run the new code-only CPU Colab integration notebook and return its actual evidence ZIP; do not upload dental images.

## Owner teaching notes

1. `_require_policy(measurements, receipt)` — உண்மையாக அளந்த colour values எல்லா frozen limits-க்கும் பொருந்தினால் மட்டுமே அந்த image-ஐ எழுதலாம். ஒரு condition fail ஆனாலும் நிற்கும்.
2. `authorise(..., authorization_bindings(...))` — புதிய code/policy/cohort/output-க்கு owner தனியாக permission கொடுத்தாரா பார்க்கிறது. பழைய permission புதிய export-ஐத் திறக்காது.
3. `validate_bundle(root, expected_manifest_sha256)` — நம்பகமான manifest hash, actual PNG pixels/metadata, stored QA எல்லாவற்றையும் சரிபார்க்கிறது. Original image இல்லாமல் அதன் colour-ஐ மறுபடியும் அளந்ததாகக் கூறாது.

Viva: **Why keep reverse error if it no longer rejects v4?** அது useful diagnostic. v4 acceptance-க்கு forward colour difference, gamut extent/severity மற்றும் integrity checks எல்லாம் தேவை. இதனால் clinical colour accuracy நிரூபிக்கப்பட்டதாக ஆகாது.
