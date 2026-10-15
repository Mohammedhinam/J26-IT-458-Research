# One local Option A v4 packaging attempt — stopped

2026-10-15, branch **vinuthan**. The owner explicitly authorized **one local-only exploratory packaging attempt**, accepting the frozen bounded colour transformation. Existing `exploratory_bundle_v4.package_development` was invoked **once**, unchanged. **Overall result: FAIL / STOPPED at Training/00004. No final manifest or ZIP exists.** No retry, candidate exclusion, repair, fallback, threshold change, upload, model execution, installation/download, commit or push.

## Scope, authorization and preflight

Owner authorization, actual local timestamp, single-attempt limit and provenance are recorded in ignored `owner_decision.txt` and `package_authorization_v4.json`. Scope is `package_development_option_a_v4`; no clinical-label, institutional, final-research, cloud-use or model-training approval is inferred. Existing local-copy/data-use records and CC BY 4.0 attribution requirements were reviewed; no conflicting local-copy restriction was found in those reviewed project rules. This does not certify institutional compliance, anonymity or clinical validity.

| Pinned preflight check before source-image access | Actual result |
|---|---|
| Training / Validation selected | **680 / 53 = 733** |
| Held development records excluded | **181** |
| Selected NP015 / protected / uncertain groups | **0** |
| Known cross-split group collisions | **0**; 733 distinct selected content groups |
| Test records/payloads selected | **0** |
| Eligible fixed full-resolution CAM IDs | Validation/00733, 00734, 00766 |
| Fresh ignored output / adjacent ZIP | Both nonexistent before attempt |
| Available disk before attempt | **169,380,626,432 bytes** |

Current bindings were recomputed, not copied from an old permission:

- DRAFT SHA-256: `b9777bdcb1ee88b2b7ac0f0a24c9d5404a9c54f1f8c5b677ab8ed9a5fe7f27c1`.
- Source-plan digest: `7f7600b03ab209995324b53926bc283e6194bd65c381db73ecb5920958bcbf59`.
- Six-module v4 code digest: `5d4970e113230f45dd79f384fc1f2fe8eb5f27917f72a257c1967daf5e2fb24b`.
- Frozen policy specification SHA-256: `b90937f2a7255a58ac65b3efb77ce58f03ec3865a9e0b096d48f6e27f639cc6a`.
- Export version: `pp1-exploratory-bundle-v4-option-a`; its separate string SHA is retained in `preflight.json`.
- New output ID: `pp1_dev_bundle_v4_20261015T035028056553Z`.

Owner-reported corrected Colab v4_1 success was context, not independently reverified here because no new evidence ZIP was attached. Existing Mac generated verification was reused; no tests or completed dataset audit were repeated.

## Actual single run and first failure

1. **733/733 original source SHA-256 checks MATCH**; source bytes **4,427,774,122**. Byte checking did not decode image RGB.
2. **733/733 source headers pass** the existing supported RGB/identity-orientation/ICC guard. Header success is not full-resolution colour acceptance.
3. Full-resolution QA completed for **four Training sources, 00001–00004**. The first three passed all v4 colour conditions and per-row output checks; three resized metadata-safe PNG derivatives were written. No full-resolution CAM source had been reached.
4. **Training/00004 failed** maximum forward ΔE76 and maximum normalized gamut excursion. The exporter raised before writing that source's derivative. Processing stopped immediately; the remaining **729 sources did not undergo full-resolution colour QA**.

Exact exception: `Option A colour rejection: max_delta_e,gamut_excursion`.

| Training/00004 measured condition | Actual measurement | Frozen acceptance | Result |
|---|---:|---:|---|
| Mean forward ΔE76 | 0.2782854788739305 | mean +0.01 ≤0.50 | PASS |
| P99.9 enclosing upper bound | 0.605; enclosing interval [0.604, 0.605] | upper +0.01 ≤1.00 | PASS |
| Maximum forward ΔE76 | **3.016736865277825** | max +0.01 ≤2.00 | **FAIL: 3.026736865277825 >2.00** |
| Out-of-gamut pixels | 28,616 /35,431,818 | count ≤35,431 | PASS |
| Out-of-gamut fraction | 0.0008076356680314852 | ≤0.001 | PASS |
| Maximum normalized excursion | **0.038690466433763504** | ≤2/255 =0.00784313725490196 | **FAIL** |
| Reverse RGB maximum | 15 | Diagnostic only in v4 | Not the rejection gate |

All numeric measurement-schema checks passed. A low mean and small affected fraction did not override the severe-pixel limits. These measurements establish an engineering-policy failure, not clinical colour significance or its physical cause. No further diagnosis or policy proposal was attempted in this task.

The unchanged production code checks original source hashes before processing and after QA; accepted sources also pass the after-export source hash. Original images/annotations/labels/splits were never written. Observational Python profiling recorded function results and safe aggregate metrics without replacing processing functions, return values, exceptions or thresholds. An independent verifier subprocess was prepared to run after internal verification and before ZIP creation; it **was not invoked**, because no final manifest was reached.

## Delivered output: incomplete, not a package

| Item | Actual result |
|---|---:|
| Resized derivatives | **3 /733**, all Training |
| Validation derivatives | **0 /53** |
| Full-resolution CAM copies | **0 /3** |
| Partial PNG bytes | **163,138** |
| Full-resolution colour QA | **4 checked: 3 passed, 1 failed** |
| Final manifest | **Not created** |
| Independent complete-bundle verification | **Not run: no final manifest** |
| Final ZIP / size / SHA-256 | **Not applicable — no ZIP exists** |
| Existing builder invocation time | **84.59483012501732 seconds** |

Partial output is preserved, not promoted, deleted or reused:

`/Users/vinuthanvinuthan/Desktop/RP-J26-IT-458/data/vision/pp1_dev_bundle_v4_20261015T035028056553Z/`

Ignored authorization/run evidence:

`/Users/vinuthanvinuthan/Desktop/RP-J26-IT-458/data/vision/option_a_packaging_attempt_v4_20261015T035028056553Z/`

Contains owner decision, exact authorization/bindings, pinned preflight, local-use record, single invocation marker, stdout, four safe aggregate QA records, failure trace, `attempt_result.json`, consumed-attempt marker and preservation evidence. No private source metadata values, ICC profile bytes or diagnostic image derivatives were saved into logs. The three permitted PNG exports are only in the incomplete output directory.

Current exporter/helper/policy/model/trainer, old v3/v4 code artifacts, DRAFT, approvals and dirty work remain unchanged. Only this factual report, append-only diary/AI log and ignored attempt records/partial output are task additions.

**One next action:** obtain separate authorization for a focused **read-only Training/00004 colour diagnosis**. Do not retry packaging, increase budgets, omit that source or reuse this consumed attempt permission.

Teaching: `_prepare` freezes who may enter; `_require_policy` requires every frozen condition, so maximum/severity failures stop despite acceptable averages; the package manifest/ZIP is written only after all sources pass. Viva: **Did packaging succeed because three files were exported?** இல்லை. 733-லும் checks முடிந்து final manifest/ZIP verify ஆனால்தான் package success. இப்போது அது முழுமையற்ற stopped output மட்டுமே.
