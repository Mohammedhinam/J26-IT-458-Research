# Local development packaging attempt — v3, 2026-10-15

Branch **vinuthan**. Owner explicitly authorised local packaging only for `pp1_dev_bundle_v3_20261015`. **STOPPED at the first real-image safety failure. No image derivative, full-resolution CAM copy, final manifest or ZIP was created.** No retry, exclusion, threshold relaxation, code change, cloud upload, model operation, install/download, commit or push.

## Permission and pinned scope

The [published dataset record](https://data.mendeley.com/datasets/3253gj88rr/1) still declares **CC BY 4.0**. Its [licence terms](https://creativecommons.org/licenses/by/4.0/) permit copying/adaptation with attribution and indication of changes; privacy rights are separate. Applicable reviewed project instructions allow an explicitly owner-authorised isolated local exploratory package while retaining provisional labels and final-research gates. No conflicting local-copy restriction was identified in those reviewed rules. **No institutional, supervisor, clinical or cloud-use approval is claimed.** This review is scoped to documented requirements and private local copying, not blanket certification of institutional compliance, anonymity or future sharing.

The actual owner decision is retained in ignored `owner_decision.txt`; `package_authorization_v3.json` records Vinuthan T, date **2026-10-15**, the current conversation decision reference, existing limitation acknowledgements and the exact hash bindings. The unsigned template is unchanged. Clinical/participant/split/final approval flags remain false.

| Binding | Verified value |
|---|---|
| Frozen DRAFT SHA-256 | `b9777bdcb1ee88b2b7ac0f0a24c9d5404a9c54f1f8c5b677ab8ed9a5fe7f27c1` |
| Pinned source-plan digest | `7f7600b03ab209995324b53926bc283e6194bd65c381db73ecb5920958bcbf59` |
| Unchanged verified v3 code digest | `44455f3e80ad0629f509427e2f5e37af93a6cb7f5cab42b27d3fdc85f2d7b639` |
| Intended candidates | 680 Training + 53 Validation = **733** |
| Intended full-resolution copies | Validation/00733, 00734, 00766, additional copies of eligible records |
| Held/excluded records | **181**, no selected overlap; NP015 and protected/duplicate groups excluded |

The existing pinned development-only plan was reused; no Test labels, source images or archive were opened. The v3 code-only ZIP/source hashes matched before execution. Output/authorization paths are ignored; the target and ZIP did not exist before this attempt. Available disk before preparation was **169,322,708,992 bytes**; disk was not the failing check.

## Actual run and first failure

Existing `package_development` was invoked once, unchanged. A local observational wrapper recorded function-return counts and the failing source ID/numerical guard from the exception; it did not change return values, limits or image processing. Runtime: Pillow **12.3.0**, LittleCMS **2.19**, CPU. Existing synthetic checks were not repeated.

1. Live source SHA preflight: **733/733 MATCH**, **4,427,774,122 source bytes**, cohort 680/53; no source RGB decodes by this SHA stage.
2. Source-header compatibility scan: **733 passed** the existing RGB/orientation/ICC header guard. That is not a pixel-conversion result.
3. First source **Training/00001** was decoded and processed in memory for the authorised ICC→sRGB→source check. Maximum reverse-transform channel discrepancy was **7**; approved limit is **2** at eight-bit precision. The existing `ValueError` stopped processing before the first PNG write. The cause is not further diagnosed here: do not label it definitively as clipping versus quantisation versus another transform limitation without a separately scoped investigation.
4. Processing stopped immediately. Original bytes of the failed source were checked again and still match the pinned SHA. No other image was transformed, no rule changed and no failed record excluded. Empty newly created output directories are retained; no existing file was overwritten or deleted.

Exact error: `ICC colour round-trip exceeds quantisation/gamut guard; review required`.

## Actual delivered counts and bytes

| Item | Actual result |
|---|---:|
| Training derivatives | **0 / 680** |
| Validation derivatives | **0 / 53** |
| Full-resolution CAM copies | **0 / 3** |
| Exported image files / payload bytes | **0 / 0** |
| Successfully accepted source colour conversions | **0** |
| Rejected first source check | **1**, observed error 7 > 2 |
| Final bundle manifest | Not created |
| Final ZIP | Not created |
| ZIP byte size / SHA-256 | **Not applicable — no archive exists** |
| Elapsed builder attempt | **5.316 seconds** |

Intended output: `data/vision/pp1_dev_bundle_v3_20261015/` (empty directories only). No ready/uploadable/training-approved package exists. Planned CC BY creator/title/version/DOI/licence/conversion notice remains in the reviewed builder and local-use record; no completed bundle manifest is claimed.

Evidence locations:

- `data/vision/icc_colour_export_v3_20261015/package_authorization_v3.json`: genuine local-packaging-only owner record; no broader approvals.
- `data/vision/icc_colour_export_v3_20261015/local_packaging_attempt_v1_20261015/`: `owner_decision.txt`, `local_use_check.json`, `pre_run_checks.json`, `packaging.log`, `packaging_attempt.json`, `stopped_attempt_verification.json`, `preservation_verification.json`.

These are ignored local records, not image payloads or final research evidence. Original files, labels/splits, pinned DRAFT/source plan and verified code remain unchanged. The questionnaire branch and final research-training API are untouched.

## Remaining blocker and next safe step

The real source fails the approved colour round-trip limit. Packaging permission was granted and truthfully recorded; it does not permit bypassing a failed safety rule. **Stop here.** Next, obtain instructions for a focused colour-diagnostic review of this one failure, preferably beginning with generated-profile reproduction and the existing numerical evidence. Establish why the discrepancy occurs before proposing any method/guard change. Do not automatically rerun, resplit, exclude Training/00001, change labels, relax 2 to 7 or switch to a different package ID.

Any later implementation change requires affected regression verification and updated source-hash bindings; any retry needs an explicit instruction and fresh versioned output because the failed attempt's empty directories/evidence are preserved. Upload/training and final clinical/supervisor/participant approvals remain separate. No scientific model performance or completed clinical colour validation follows from prior synthetic passes.

Three blocks to understand: `dry_run` confirmed original source bytes; `managed_srgb` raised because **7 > 2**; `package_development` writes only after that guard returns, so **0 files** were exported. Viva: **Why can 95 synthetic checks pass but a real picture fail?** Tests verify the code on known fixtures, including rejection behaviour; a real image can correctly trigger its safety stop. That is not permission to change the limit.
