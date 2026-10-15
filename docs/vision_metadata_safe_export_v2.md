# Metadata-safe development export revision — v2

Recorded **2026-10-15**, branch `vinuthan`; work continued across midnight from the Oct 14 preflight. Owner authorised implementation and generated-image regression checks only. **No dental image derivatives/package/upload, model training/inference, weight download, Test payload access, installation, commit or push.**

**Code/synthetic verification PASS. Real packaging remains BLOCKED by source colour-profile handling and missing packaging authorisation.** No clinical label, source split, final manifest or research-training gate was changed. Every exploratory result retains: **Provisional labels; non-clinical; non-final; participant independence unverified.**

## Exact changed files

| File | Scoped change |
|---|---|
| `src/vision/exploratory_bundle.py` | Fresh RGB-only lossless PNG export; orientation/colour guards; source/payload/pixel/dimension checks; strict PNG chunk/CRC verification; v2 schema and attribution; source-plan holds/NP015 guards |
| `src/vision/exploratory_pilot.py` | CAM consumer reads a verified full-resolution PNG and checks its exported-payload hash, not the JPEG source hash |
| `tests/test_exploratory_bundle.py` | Generated metadata/pixel preservation, profile/orientation rejection, injection/tamper checks and exclusion regressions |
| `tests/test_exploratory_pilot.py` | Updated generated CAM fixture and payload-tamper rejection before mocked explanation |
| `docs/vision_pp1_metadata_safe_code_v2.zip` | New code-only snapshot: six sources/tests plus SHA manifest; no datasets/weights |
| `docs/vision_pp1_metadata_safe_verification_v2.ipynb` | New CPU metadata-regression workflow; no real-data/training cell; RUN_PILOT=False |
| `docs/vision_metadata_safe_export_v2.md` | This report, commands, limitations and future approval requirements |
| `docs/vision_pp1_exploratory_scaffold_v1.md` | Append-only pointer to current revision; historical instructions retained |
| `docs/vision_runtime_verification_results.md` | Append-only distinction between historical Colab v1 snapshot and new local verification |
| `docs/diary.md`, `docs/ai_log.md` | Factual task entries; owner-understanding line remains blank |

Existing `model_pipeline.py`, `train_pipeline.py`, original notebook/code bundles and all earlier evidence ZIPs remain byte-identical. New ignored verification records are under `data/vision/metadata_safe_export_v2_20261015/`; they contain logs/JSON/XML/checksums, not dental-image exports or approvals.

## Export behaviour and colour limitation

- Derivatives keep the existing aspect-preserving 224-pixel resize and exact preprocessing tensor. Three CAM copies become **lossless full-resolution RGB PNGs**, with original decoded pixel array and dimensions unchanged. Original JPEG paths/filenames remain provenance; source files are never rewritten.
- `Image.frombytes('RGB', image.size, image.tobytes())` creates a new pixels-only image. The writer adds no EXIF, GPSInfo, DateTime, MakerNote, XMP, comments, inherited ICC or private blobs. Allowed output PNG chunks are **IHDR, IDAT, IEND only**, canonical eight-bit RGB; CRCs, absence of trailing data, mode, dimensions and pixel digests are checked.
- `source_sha256` remains the original JPEG byte hash. `source_rgb_sha256` fingerprints decoded full-resolution pixels. `image_payload_sha256` / `cam_payload_sha256` fingerprint exported PNG bytes; independent pixel/dimension fields and the manifest files map must agree. CAM pixels/dimensions must equal the source fields. These are integrity/provenance checks, not clinical validation.
- Identity/missing EXIF orientation is accepted. Orientation 2–8 is rejected, not silently rotated, mirrored or discarded. This preserves the established raw decoded-RGB coordinate frame and prevents a change to CAM alignment without approval.
- Embedded ICC, nonsRGB/uncalibrated EXIF ColorSpace, or gamma/chromaticity-dependent interpretation **fails closed before any packaging output is created**. ICC affects the meaning/display of RGB numbers: preserving numeric pixels alone does not prove preserved visible colour after stripping it. This revision therefore makes no silent ICC conversion or all-source colour-preservation claim.

**Actual permitted header-only check:** Validation `00733`, `00734`, `00766` each has dimensions **7286×4863**, orientation **1**, an embedded ICC profile and EXIF ColorSpace **65535 (uncalibrated)**. No source pixels were decoded/exported during this check. These originals are deliberately rejected by the new colour guard. The Oct 14 GPS check found **GPSVersionID only**, no latitude/longitude/time/date fields; no confirmed location leak is claimed. ICC/EXIF values that could identify a person were not logged.

To unblock those sources while retaining exact RGB pixels and visible colours, first review an appropriate **trusted, non-identifying colour-profile preservation/allowlist policy**, or a separately approved alternative. Converting to sRGB would change numeric pixels/preprocessing and is not authorised by this task. Do not bypass the guard, strip ICC without review or claim all 733 actual exports have been verified. Only the three allowed development headers were inspected; no fresh full metadata audit was performed.

## Actual synthetic verification

Final focused result: **73 passed, 0 failed, 0 errors, 0 skipped** in **0.54 seconds**. Runtime: Python **3.12.14**, NumPy **2.3.5**, Pillow **12.3.0**, pytest **9.1.1**, CPU. Reused bundled Python/NumPy/Pillow and the existing `.venv` pure-Python pytest package; no install. The 73 selected checks comprise the affected bundle tests plus four affected CAM/approval checks. No architecture optimisation, model fit or actual Grad-CAM inference was executed; the CAM output test uses a generated-array mock. Historical Colab tests were not repeated.

Covered: original-byte preservation, exact decoded RGB/full-resolution geometry, unchanged resized tensors, metadata-free outputs, independent source/payload hashes, PNG/manifest/pixel/geometry/CRC tampering, old-schema rejection, attribution, orientation/ICC rejection, no overwrite, Test/held/NP015/protected-group rejection and known group isolation. The original approved-training API still rejects provisional metadata before image access.

Initial local run caught a verification-order bug: `getexif()` loaded the PNG before Pillow `verify()`. Initial counts were **50 passed, 4 failed, 17 errors**, zero skipped; the redundant call was removed because the explicit chunk allowlist already forbids EXIF. The repaired run passed 71 checks; CRC and direct bundle-NP015 regressions brought the final selection to 73. All three actual XML records are retained; only the final run is the current result.

```bash
cd /Users/vinuthanvinuthan/Desktop/RP-J26-IT-458
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 \
/Users/vinuthanvinuthan/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -B - <<'PY'
import sys
import numpy, PIL
sys.path.append('/Users/vinuthanvinuthan/Desktop/RP-J26-IT-458/.venv/lib/python3.13/site-packages')
import pytest
raise SystemExit(pytest.main([
    '-q', '-rs', '-p', 'no:cacheprovider', 'tests/test_exploratory_bundle.py',
    'tests/test_exploratory_pilot.py::test_cam_artifacts_always_carry_notice_and_unsupported_prediction',
    'tests/test_exploratory_pilot.py::test_unlisted_cam_example_blocked_before_image_read',
    'tests/test_exploratory_pilot.py::test_cam_rejects_payload_tampering_before_explanation',
    'tests/test_exploratory_pilot.py::test_production_training_gate_still_rejects_exploratory_metadata',
]))
PY
```

Equivalent final selection was executed with captured output/JUnit. No repeat is necessary for the unchanged snapshot. Saved evidence: `synthetic_export_final.json`, `.log`, `.xml`; preceding failure/repaired XML retained. These selected local checks are not a full repository run or new Colab execution.

## Versioned source bundle and optional affected-runtime checks

Code ZIP: `docs/vision_pp1_metadata_safe_code_v2.zip`; SHA-256 **`52ab60b1a0c7dc87da4fd2804f97d4ce709ca411b9928306986df9149c47f98b`**. Six file hashes match current source and bundled bytes; seven entries, ZIP CRC passes. Notebook code cells parse, have empty outputs and no execution counts. **The new notebook has not run in Colab.** The historical 60-pass T4 evidence remains an unchanged v1 snapshot; four of its six files have now changed, so it does not certify this revision. Model/trainer hashes remain unchanged.

Optional future portability check: upload only the new notebook and code ZIP to a fresh CPU Colab VM, no Drive/data/weights; execute the metadata-only cells with installed NumPy/Pillow/pytest. Acceptance is the selected **73/0/0/0** plus unchanged six hashes. Its evidence filename is `vision_metadata_safe_export_runtime_evidence_v2.zip`. This is a new affected-code check, never a reason to rerun completed model/trainer workflows or enable a pilot.

Current four-module code digest: **`3c3f79231082282acdcbb6a6c0cd3a45701e7c1e179bec164c425caafaef9719`**. Full six-file map is in the new code manifest and ignored `code_bundle_v2_verification.json`. Any later colour-policy change requires new hashes/versioned verification; do not sign this digest for code that changes afterwards.

## Separately authorising real development packaging

1. Resolve the actual ICC/colour-preservation conflict without silently changing pixels, geometry, visible colours or frozen preprocessing; verify only affected code with generated data and publish its new digest if changed. No real package can currently pass the source colour guard.
2. Keep the pinned DRAFT **`b9777bdcb1ee88b2b7ac0f0a24c9d5404a9c54f1f8c5b677ab8ed9a5fe7f27c1`** and source-plan digest **`7f7600b03ab209995324b53926bc283e6194bd65c381db73ecb5920958bcbf59`**. Reuse the verified 680/53 candidate selection, 181 exclusions, NP015 and protected content boundaries; these are cached preflight counts, not a new dental export result.
3. Obtain an actual owner packaging-only decision with authorizer/date/evidence, all existing provisional/non-clinical/non-final/unknown-participant/missing-class acknowledgements, the current verified code digest and a fresh exact bundle ID. Include permission to create only **733 development derivatives + three metadata-safe full-resolution Validation copies**, preserving originals/labels/splits and excluding every Test/held/NP015 record. A later upload/run needs separate authorisation. No record was signed or filled in this task.
4. Record source [dataset](https://data.mendeley.com/datasets/3253gj88rr/1), creator Duy Hoang Bao, title/version, DOI **10.17632/3253gj88rr.1**, [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) link and transformations in the allowlisted manifest. This attribution is now mandatory in code; source camera/private metadata is not licence attribution. Applicable privacy/institutional/cloud requirements are not waived by the copyright licence.
5. Future authorised packaging must recheck live source hashes and colour/orientation headers before exports; verify each payload's metadata absence, pixels/tensors, dimensions, independent hashes, exact inventory and known group boundaries. Report actual archive size/SHA only after packaging. The PNG-only layout would have **737 ZIP entries** (733 derivatives, three CAM PNGs, one manifest); none exists now.

Suggested future decision, **only after colour handling is resolved**:

> I authorise packaging only the pinned 680 Training and 53 Validation provisional candidates and metadata-safe full-resolution copies of Validation/00733, 00734, 00766 using the reviewed colour policy and verified code hash into the named new bundle. Preserve originals, pixels/geometry/colour, source provenance, labels/splits, exclusions and CC BY attribution. I acknowledge the recorded limitations and permitted data use. This authorises packaging only; no upload, training/inference, weights download or final manifest activation.

Existing unsigned templates remain pending. Final clinically approved labels, participant independence, scientific manifest and dental training remain separate gates. Missing/scarce whole-image classes are unchanged. The quickest next step is the narrowly scoped trusted-colour-profile review; merely approving packaging cannot override its safety guard.

## Three blocks to understand

1. **`export_rgb_png`**: fresh pixel-only PNG, no inherited metadata; decoded pixels and full-resolution geometry remain equal. Tamil: படம் மட்டும் புதிய file-ல் வரும்; camera/private metadata வராது.
2. **`verify_rgb_export`**: checks PNG chunk allowlist/CRC plus payload/pixel hashes/dimensions; injected metadata or changed pixels fail even if the files-map byte hash is rewritten. Tamil: hash மட்டும் போதாது; file அமைப்பு, pixels, size-யும் சரிபார்க்கிறோம்.
3. **`check_source_colour` + CAM payload hash**: stops unsupported orientation/ICC rather than changing the image; CAM checks the exported PNG hash separately from the original JPEG. Tamil: original hash வேறு, export hash வேறு; ICC-ஐ நீக்கியதால் நிறம் மாறக் கூடாது.

Viva: **Identical RGB numbers mean identical visible colours after removing ICC?** இல்லை. ICC நிறங்களின் interpretation-ஐ நிர்ணயிக்கும்; அதனால் unreviewed ICC-ஐ silent-ஆக நீக்காமல் export-ஐ நிறுத்துகிறோம்.


## 2026-10-15 — ICC-to-sRGB metadata-safe export v3

The owner subsequently authorised ICC conversion explicitly. [ICC export v3](vision_icc_colour_export_v3.md) supersedes this report's historical blanket ICC block: supported RGB matrix-shaper profiles are converted to generated standard sRGB before resize, with fixed relative intent/flags and a conservative numerical round-trip guard. Original bytes/geometry remain unchanged; converted RGB numbers may differ and managed/payload hashes are now separate. A fixed non-identifying sRGB PNG declaration is allowlisted; original ICC/private metadata is not copied.

Actual new selection: **95 passed, 0 failed/errors/skipped**, generated profiles/images only. Three fixed CAM headers pass supported-profile validation, but no actual dental pixels were converted/exported or all-733 round trips verified. Real packaging is still separately unauthorised. New v3 code ZIP/notebook/source hashes replace neither old evidence nor the final research gate. Do not reuse v2 code hashes/templates for v3; exact next packaging-only wording and bindings are in the new report. No Test payload access, clinical/split changes, models, installs/downloads, commit or push.
