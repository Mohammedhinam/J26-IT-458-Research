# Development-only packaging preflight — v1

Recorded 2026-10-14; branch `vinuthan`. **Cohort/hash dry-run PASS. Overall safe packaging preflight FAIL / BLOCKED pending metadata-safe export and explicit packaging authorisation.** No real dental image was exported, packaged, uploaded or trained. No Test image/label payload was accessed. This is not a new dataset audit or clinical approval.

Every exploratory result retains: **Provisional labels; non-clinical; non-final; participant independence unverified.**

## Verified checks

| Check | Actual result | Status |
|---|---|---|
| Candidate cohort | 680 Training + 53 Validation = **733** | PASS |
| Selected source byte hashes | **733/733 MATCH** against cached inventory | PASS |
| Held development records | **181 excluded**: 52 Training / 129 Validation; selected/held overlap 0 | PASS |
| NP015 | Training/00591 and Validation/00736 excluded; uncertain-group intersection 0 | PASS |
| Known content boundaries | 733 unique singleton content groups; Training/Validation intersection 0; protected-Test group intersection 0 | PASS |
| Test supply | 0 Test records or image/annotation/archive entries planned | PASS |
| Source preservation | Read-only SHA checks; 0 RGB decodes by builder; 0 image exports/packages | PASS |
| Qualification | 0 qualified-approved labels; final manifest inactive; participant identity unverified | Still provisional |
| Saved Colab evidence | 60 passed / 0 failed / 0 errors / 0 skipped; six hashes match current source and code ZIP | PASS, synthetic only |
| Dataset reuse permission | Published dataset CC BY 4.0; attribution/modification notices needed; privacy rights are separate | Conditional |
| Export metadata protection | Three planned full-resolution CAM originals contain GPSInfo/opaque MakerNote tags; v1 copies them verbatim | **FAIL / BLOCKED** |
| Real packaging permission | No owner-confirmed packaging record; existing template remains unsigned/pending | Required next gate |

Original source splits, all QA/review statuses, draft and existing trainer are unchanged. Group isolation covers known content, not independently verified participant identity. Candidate MGI 0–4 counts remain Training **0/12/84/223/361**, Validation **0/1/13/22/17**; five-output code does not establish five-grade validity.

## Actual dry-run and local artifacts

Ignored output: `data/vision/pp1_packaging_preflight_v1_20261014/`.

- `dry_run.json`: actual existing-builder output.
- `source_plan.json`: same pinned 733-candidate plan, not a training-ready manifest.
- `cohort_preflight.json`: holds, group isolation, counts, checksums and measured free disk.
- `source_to_output_mapping.json`: one planned path/hash mapping per selected source; no images created.
- `package_size_projection.json`: measured source sizes and estimated derivative storage.
- `colab_evidence_verification.json`: saved JSON/log/XML/source-bundle verification, no test rerun.
- `privacy_preflight.json`: tag names/presence for the three fixed development CAM originals and a generated-image-only metadata probe; no coordinates/identity values.

```bash
cd /Users/vinuthanvinuthan/Desktop/RP-J26-IT-458
task_preflight_python=/Users/vinuthanvinuthan/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3
task_preflight_staging="$PWD/data/vision/gingivitis/staging-16669f74665ff0deca6ddd25feb0d233e52fdc2313265465bf91731af1e8956b"
"$task_preflight_python" -B -m src.vision.exploratory_bundle \
  --draft "$task_preflight_staging/strict_clean_development_draft_v1_20261014/development_manifest_draft_v1.json" \
  --hash-inventory "$task_preflight_staging/audit_verified/integrity_results.json" \
  --source-root "$task_preflight_staging" \
  --output "$PWD/data/vision/pp1_packaging_preflight_v1_20261014"
```

This exact dry-run command was executed successfully. Its output location now exists: do not rerun into it; use a new versioned location if a later changed preflight is necessary. The builder streams development path/hash/dimension fields from the cached inventory, skips Test/annotation fields before deserialisation, and hashes only selected development image bytes. Hashing evidence files does not derive or use their Test labels.

| Binding | Verified SHA-256 |
|---|---|
| Frozen development DRAFT | `b9777bdcb1ee88b2b7ac0f0a24c9d5404a9c54f1f8c5b677ab8ed9a5fe7f27c1` |
| Source plan JSON digest | `7f7600b03ab209995324b53926bc283e6194bd65c381db73ecb5920958bcbf59` |
| Current four-module code digest | `0e6960c0a1008c166ecda91afacf64a935c1a9ef4b8b948aa56ef5c9a927b314` |

These bind the current preflight; **the current code digest must not be represented as metadata-safe**. A scoped export fix changes the code digest and requires a new source bundle/verification record and authorisation binding. The DRAFT/source plan need not change.

## Expected structure and projected size

Current v1 mapping, **not produced**:

```text
bundle_manifest.json
images/Training/<original ID>.png       # 680 aspect-preserving RGB derivatives
images/Validation/<original ID>.png     # 53 derivatives
cam/Validation/00733.jpg                # current v1 verbatim original — blocked
cam/Validation/00734.jpg                # blocked
cam/Validation/00766.jpg                # blocked
```

For example, `Dataset/Training/Images/00001.jpg` maps to `images/Training/00001.png` only if selected; the complete mapping is in the ignored JSON, with original relative paths/SHA and group IDs. PNG changes the derivative extension, never the source filename or original record/split. Three CAM files are additional copies of eligible Validation images, not three new participants. The current allowlist would contain **737 ZIP entries**: 733 resized PNGs, three CAM JPEGs and one manifest. No source CSV, TXT, RAR, full data directory, Test payload or weights are permitted. Opaque protected-group IDs are boundary evidence, not Test grades.

Measured source bytes: **4,427,774,122** (4.12 GiB). Three CAM JPEGs: **16,932,897** bytes (16.15 MiB). Resized RGB pixel storage upper bound: **110,337,024** bytes (105.23 MiB), before compression/metadata/manifest overhead. Earlier **250 MiB** allowance is a planning budget for the current v1 layout, not a measured archive size. No archive exists. Measured available disk: **168,551,460,864 bytes**.

If full-resolution metadata-free RGB PNGs are chosen for the three CAM copies, their decoded RGB payload would be **318,886,362 bytes** (304.11 MiB); combined with the resized bound, **409.34 MiB before overhead/compression**. A proposed 512 MiB bundle allowance would replace the earlier estimate; this remains unapproved/unmeasured. Original RGB geometry/colour and source-byte hashes must remain traceable. The matching CAM payload/hash checks need a scoped update; simply swapping JPEG bytes would fail existing integrity checks.

## Permission and metadata evidence

The [Mendeley version 1 dataset record](https://data.mendeley.com/datasets/3253gj88rr/1) declares **CC BY 4.0**. That licence permits copying/adaptation with credit, a licence link and indication of changes; it does not waive privacy/publicity rights ([Creative Commons terms](https://creativecommons.org/licenses/by/4.0/)). Retain attribution to Duy Hoang Bao, dataset title, version 1, DOI `10.17632/3253gj88rr.1`, source URL/licence, and a note identifying resizing/metadata removal and provisional derived labels. Embed this in the allowlisted manifest so no unapproved extra payload is needed. Current v1 has no explicit dataset-attribution field; add it in the scoped packaging-safety revision. The dataset licence is distinct from the paper's CC BY-NC licence.

The [original paper's Ethics Statement](https://www.sciencedirect.com/science/article/pii/S2352340924009223) reports Hanoi Medical University IRB approval `1149/GCN-HMUIRB`, dated 2023-12-28, and explained/consented data collection; its consent subsection also states formal consent was not required for this study. It does **not supply local individual consent forms or establish explicit consent for sharing potentially identifying metadata with this project's cloud service**. Do not assert those records exist. The owner's packaging/Colab authorisation must acknowledge applicable institutional data-use/cloud requirements; no blanket institutional approval is inferred from the public copyright licence.

The existing audit already recorded absent nonempty identity strings in checked fields, unresolved opaque MakerNotes and GPSInfo tags. No repeat 1,096-image metadata audit was performed. Header-only checks of **Validation/00733, 00734, 00766** confirm GPSInfo, DateTime and MakerNote tag presence in all three. Their GPS IFD contains **GPSVersionID only: no latitude/longitude or GPS time/date fields**. This is not a confirmed location leak. DateTime is nonempty; opaque MakerNotes remain uninterpreted. No GPS values, timestamps, serials or clinical interpretation were printed or exported. The export review blocker is unreviewed metadata passthrough, not proof of identified patients. Intraoral pictures can still be sensitive; comprehensive anonymity is not certified.

`package_development` currently uses `shutil.copyfile` for these originals, so their embedded metadata would survive unchanged. A generated-image-only probe under Mac Pillow **12.3.0** found resize retains `info['exif']`, but the default PNG save in that runtime did **not** emit its synthetic EXIF description. Do not extrapolate that result to every metadata type/version or claim all resized outputs are privacy-clean. A safe revision must explicitly remove identifying/opaque metadata from exported copies, verify output headers, preserve RGB pixels/alignment, retain original source hashes and bind separate exported-payload hashes. Never edit original datasets.

Use a fresh private Colab VM, no Drive mount/full archive, no public sharing, no images/metadata in AI prompts, and review notebook outputs before sharing. The [official Colab FAQ](https://research.google.com/colaboratory/faq.html) explains private account VMs, shared notebook outputs and broad Drive-mount access. Private runtime use is not a patient-consent guarantee.

## Exact next authorisation and future commands

**Next single action: approve a narrowly scoped packaging-safety revision and synthetic regression checks, not packaging/training.** Suggested wording:

> I authorise a versioned metadata-safe export revision for only the existing development cohort and three eligible Validation CAM images, plus dataset attribution and source/export-hash verification. Preserve originals, RGB pixels/colours/alignment, labels, splits, all holds and the existing approved trainer. Use generated-image tests; update only affected verification/bundle instructions. This does not authorise real image packaging, uploads, training, weights downloads or final approvals.

Only after that revision passes and the revised hashes/structure are shown, request a **separate actual packaging decision**:

> I authorise packaging only the pinned 680 Training and 53 Validation provisional candidates, plus metadata-safe full-resolution copies of Validation/00733, 00734 and 00766, into the new isolated development bundle. Retain attribution/source provenance and all Test/hold/NP015 exclusions. I acknowledge provisional labels, non-clinical/non-final use, unknown participant independence and missing/scarce grades, and confirm permitted data use under applicable institutional/cloud rules. No upload, training, inference, weight download or final manifest activation is authorised.

Record the real authorizer/date/decision reference, required acknowledgements, unchanged DRAFT/source-plan digests, **revised** code digest and exact new bundle ID. Existing unsigned templates remain pending; no fields were populated as approvals. Proposed reserved output name below is a versioned location, not an approval.

**Future command shape only — do not execute with today's v1 code or unsigned records:**

```bash
"$task_preflight_python" -B -m src.vision.exploratory_bundle \
  --draft "$task_preflight_staging/strict_clean_development_draft_v1_20261014/development_manifest_draft_v1.json" \
  --hash-inventory "$task_preflight_staging/audit_verified/integrity_results.json" \
  --source-root "$task_preflight_staging" \
  --output "$PWD/data/vision/pp1_dev_bundle_v2_20261014" \
  --package --opt-in \
  --authorization "$PWD/data/vision/pp1_packaging_preflight_v1_20261014/package_authorization_v2.json"
```

That authorisation file does not exist today. Revised code/SHA and synthetic verification must be supplied first; no checksum bypass. Future packaging must recheck live sources, exact allowlist, metadata absence, pixels/tensor equivalence, groups and zero Test entries; record actual ZIP size and SHA. Colab upload/execution requires another explicit decision and run-bound archive/manifest/config/code/weight provenance. Leave `RUN_PILOT=False`. Missing documented pretrained weights remains a future execution requirement, not a reason to download now. Final qualified labels/participant independence/manifest approval remain separate from exploratory engineering permission.

Teaching: the source SHA verifies which bytes were selected; group exclusion prevents known aliases crossing boundaries; byte-for-byte integrity is not privacy sanitisation. Viva: **Does 60 synthetic passes make these pictures safe to upload?** No—runtime checks and source hashes passed, while export metadata and explicit data-use permission are separate gates.
