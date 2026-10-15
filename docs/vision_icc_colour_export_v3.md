# ICC-managed metadata-safe export — v3

2026-10-15, branch **vinuthan**. Owner explicitly authorised the ICC-to-sRGB implementation and generated-profile regression checks. **No real dental pixels converted/exported/packaged/uploaded, model training/inference, Test payload access, source image/annotation/label/split modification, installation/download, commit or push.**

**Focused synthetic verification: 95 passed, 0 failed, 0 errors, 0 skipped.** The previous blanket rejection of embedded ICC is replaced by a supported-profile conversion path. The three fixed CAM headers pass that path's header validation; actual dental pixel conversion/round trips and all-733 export readiness are unverified until separately authorised packaging. No full dataset audit or completed architecture/trainer/Colab run was repeated.

## Small scoped implementation

1. `check_source_colour` requires RGB and identity/missing EXIF orientation. Embedded ICC must be bounded, structurally plausible, parseable by LittleCMS, RGB matrix-shaper monitor/input class, XYZ/Lab connection space and support the fixed forward/reverse intent. Empty/truncated/invalid/non-RGB/LUT/device-link/abstract/unsupported profiles fail closed, without printing original ICC descriptions or bytes. Gamma/chromaticity ambiguity also fails. A valid supported ICC supplies interpretation when EXIF ColorSpace=65535; missing ICC with that declaration is rejected.
2. `managed_srgb` uses [Pillow ImageCms / LittleCMS](https://pillow.readthedocs.io/en/stable/reference/ImageCms.html): supported source ICC → generated standard sRGB, **relative-colorimetric intent 1, flags 0**, at full resolution **before resize**. No black-point compensation, rotation or hidden fallback. This is the now-authorised colour conversion; the previous v2 prohibition is historical, not current permission.
3. A source→sRGB→source round trip must differ by no more than **2 integer levels per channel** at eight-bit precision. This is a conservative implementation/quantisation guard, **not a clinical tolerance, proof of identical appearance or complete gamut certification**. Large clipping/quantisation/transform loss stops the export before that image is written. sRGB cannot represent every possible source colour; unmanaged displays are not controlled by this code. Do not silently relax the bound or drop a failed source to achieve 733 records.
4. Accepted untagged RGB follows the existing explicit untagged-as-sRGB input contract; explicit sRGB is accepted too. Without conversion, pixels remain byte-identical. Missing ICC plus contradictory non-sRGB metadata is ambiguous and rejected. No unsupported colour space is guessed. Tagged sRGB identity and generated nonidentity profiles are separately tested.
5. Fresh lossless RGB PNGs contain **IHDR, exactly one fixed sRGB intent byte `1`, IDAT, IEND** only. The sRGB byte is a standard non-identifying declaration: no camera/ICC profile, date, manufacturer, EXIF/GPS/MakerNote/XMP/comment/opaque text is copied. PNG CRC/order, canonical geometry, metadata allowlist, pixel/payload hashes and no trailing data are checked. `ImageCms` output metadata is discarded through a fresh pixels-only image. The later CAM panels use the same sRGB declaration plus their existing provisional notice.

The normalisation/letterbox/model functions and approved research trainer are unchanged. For ICC-tagged originals, the RGB numbers and therefore model tensors **can change** after colour management. The exact-resize/tensor equivalence check now compares a managed full-resolution image with its managed derivative, not with the unconverted camera RGB values. Geometry, original dimensions for CAM and image alignment remain unchanged.

## Provenance and schema

v3 rejects old v1/v2 package schemas. Mandatory CC BY attribution/DOI/licence links remain, with a revised conversion/transformation notice. Existing DRAFT, 733-candidate identity, original splits, all 181 holds, NP015 and protected-content guards remain unchanged; final clinical/research approvals stay false.

| Recorded value | Meaning |
|---|---|
| `source_sha256` | Original source-file bytes, unchanged including its source metadata |
| `source_rgb_sha256` | Raw decoded original RGB pixels |
| `colour_managed_rgb_sha256` | Full-resolution standard-sRGB pixels after any required conversion |
| `colour_conversion` | `icc_to_srgb` or explicit `untagged_srgb_identity` |
| `colour_roundtrip_max_channel_error` | Measured integer reverse-transform discrepancy; 0–2 only |
| Image/CAM payload SHA and RGB SHA | Independent exported-file bytes and exported pixels |
| Source/image/CAM dimensions | Original and resized geometry; CAM must match original dimensions |

CAM RGB hash must equal the **managed** full-resolution hash. It is no longer incorrectly required to equal raw source RGB after a nonidentity conversion. Identity-path raw and managed hashes must still agree. Neither a matching hash nor a colour-managed export approves a label, establishes participant independence or validates clinical colour/grade accuracy.

## Actual checks and remaining uncertainty

Selected run: **95/95 passed in 0.59 seconds**, no failures/errors/skips. Includes 21 new generated-profile cases plus the affected bundle/CAM/approval regressions. Runtime: Python **3.12.14**, NumPy **2.3.5**, Pillow **12.3.0**, LittleCMS **2.19**, existing pytest **9.1.1**, CPU; no installs. All model operations are absent or mocked, not real inference. No architecture optimisation tests were run.

Generated same-primaries gamma-1.8 RGB profiles demonstrate a nonidentity conversion: RGB numbers change, results match an independently constructed LittleCMS reference path, dimensions match, and the interior test patches' source-profile Lab versus sRGB-output Lab difference is within the fixed fixture's **DeltaE76 ≤2** assertion. That fixture check is numerical library/wiring evidence, not a chosen clinical colour threshold or independent perceptual study. Source-file bytes and source PIL metadata remain unchanged. Tests cover no-conversion exact pixels, metadata stripping, separate hashes, full-resolution CAM/resize consistency, invalid profile classes, malformed/missing profiles, excessive round-trip error, altered sRGB declaration, injection/tampering and all source-isolation gates.

Only the three already fixed development CAM headers were checked against the new parser: **Validation/00733, 00734, 00766** all have supported ICC headers, identity orientation and dimensions **7286×4863**. No real pixel array was decoded, transformed or saved. This resolves their v2 *header-level blanket ICC rejection*; it does not certify their pixel-level round trips or every other source. Prior GPS evidence remains GPSVersionID only, no coordinate/time/date fields; no location leak is claimed.

Ignored records under `data/vision/icc_colour_export_v3_20261015/`: `synthetic_icc_checks_initial.log/.xml`, `synthetic_icc_verification.json`, `three_CAM_header_compatibility.json`, `code_bundle_v3_verification.json`, `revision_preservation.json` and an unsigned `package_authorization_v3.template.json`. No dental-image payloads or confirmed approvals are stored there. The first actual ICC run passed; no failed count is hidden. Older v2's development/fix evidence remains historical.

## Changed files and versioned code-only artifacts

| Path | Change |
|---|---|
| `src/vision/exploratory_bundle.py` | ICC/sRGB helpers, fixed sRGB PNG allowlist, v3 schema, managed-pixel provenance and updated attribution |
| `src/vision/exploratory_pilot.py` | Matching standard sRGB declaration in future CAM panels; research gate unchanged |
| `tests/test_exploratory_bundle.py` | Updated allowlist/tamper checks and converted-package/CAM integration regression |
| `tests/test_exploratory_pilot.py` | Confirms the generated mocked CAM output declares sRGB |
| `tests/test_icc_colour_export.py` | New generated-profile regression cases |
| `docs/vision_pp1_icc_safe_code_v3.zip` | Seven current source/test files + SHA manifest; no dataset/weights |
| `docs/vision_pp1_icc_safe_verification_v3.ipynb` | New optional metadata/ICC CPU verification workflow; RUN_PILOT=False, no real-data cell |
| `docs/vision_icc_colour_export_v3.md` | This report and exact packaging gate |
| `docs/vision_metadata_safe_export_v2.md`, `docs/vision_runtime_verification_results.md` | Append-only current-revision pointers; historical evidence retained |
| `docs/diary.md`, `docs/ai_log.md` | Factual entries; owner-understanding line remains blank |

Code-only ZIP SHA-256: **`324f9fe84a4783b71ccc1371a1764ffb3665f8670cc6cc97377d005990acf7d6`**. Current four-module code digest: **`44455f3e80ad0629f509427e2f5e37af93a6cb7f5cab42b27d3fdc85f2d7b639`**. Seven source hashes/current bytes, eight ZIP entries/CRC and all notebook code-cell syntax/off state were checked. `model_pipeline.py`, `train_pipeline.py` and earlier ZIPs/notebooks/evidence remain byte-identical.

The new notebook has **not** executed in Colab. If portability verification is later wanted, upload only this new notebook/code ZIP to a fresh CPU runtime; detect installed NumPy/Pillow/pytest/LittleCMS, no Drive/data/weights or installs. It selects only these 95 generated-data checks and verifies seven before/after hashes; evidence filename `vision_icc_colour_runtime_evidence_v3.zip`. This is not a reason to repeat completed model/trainer workflows. Local Mac packaging uses the locally verified colour runtime; cross-version pixel-identical conversion is not assumed.

## Next single action: separate packaging-only authorisation

No remaining **blanket** ICC rejection for the three checked headers. Remaining conditions are explicit packaging permission, applicable data-use/privacy requirements and actual source/transform validation during authorised packaging. Metadata safety alone is not full patient anonymity. No automatic clinical/supervisor approval follows from this code.

Required bindings:

- Same DRAFT SHA **`b9777bdcb1ee88b2b7ac0f0a24c9d5404a9c54f1f8c5b677ab8ed9a5fe7f27c1`**.
- Same source-plan digest **`7f7600b03ab209995324b53926bc283e6194bd65c381db73ecb5920958bcbf59`**: cached **680 Training + 53 Validation =733**, all 181 holds, NP015 and protected groups excluded; these counts were reused, not re-audited.
- Current verified code digest above; named fresh output **`pp1_dev_bundle_v3_20261015`**; real owner/date/decision reference and all existing provisional/non-clinical/non-final/unknown-participant/no-Test/missing-class/no-final-promotion acknowledgements.
- Scope only **733 managed development derivatives + three full-resolution managed Validation copies**, source provenance and attribution; no upload, training/inference, pretrained download or final manifest activation. Source RGB numbers may change only by the declared ICC→sRGB policy; originals, geometry, labels and splits remain unchanged.

Suggested exact owner decision:

> I authorise packaging only the pinned 680 Training and 53 Validation provisional candidates plus full-resolution copies of Validation/00733, 00734 and 00766 into pp1_dev_bundle_v3_20261015 using the verified v3 code, declared ICC-to-sRGB policy and fixed round-trip guard. Preserve originals, geometry, labels/splits, exclusions, source/export hashes and CC BY attribution. I acknowledge provisional/non-clinical/non-final use, unverified participant independence, absent/scarce classes and permitted data use. Stop and report any source/colour/hash/isolation failure without excluding records or relaxing guards. No upload, model training/inference, weights download or final approval is authorised.

Only after that real decision may its pending template be populated as a **new** `package_authorization_v3.json`. It is not created/signed today. Future command shape, **not executed**:

```bash
task_icc_python=/Users/vinuthanvinuthan/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3
task_icc_staging="$PWD/data/vision/gingivitis/staging-16669f74665ff0deca6ddd25feb0d233e52fdc2313265465bf91731af1e8956b"
"$task_icc_python" -B -m src.vision.exploratory_bundle \
  --draft "$task_icc_staging/strict_clean_development_draft_v1_20261014/development_manifest_draft_v1.json" \
  --hash-inventory "$task_icc_staging/audit_verified/integrity_results.json" \
  --source-root "$task_icc_staging" \
  --output "$PWD/data/vision/pp1_dev_bundle_v3_20261015" \
  --package --opt-in \
  --authorization "$PWD/data/vision/icc_colour_export_v3_20261015/package_authorization_v3.json"
```

Authorised packaging must recheck live source hashes/headers, conversion guards, pixels/geometry, exactly 733 records and the 737-entry allowlist, zero Test/held/NP015 overlap, and actual archive/manifest SHA/size. A failure means no successful bundle: preserve originals and stop; never silently alter eligibility, splits or colour limits. Later Colab upload/execution needs separate authorisation and documented weights. Final qualified labels, participant independence, MGI-0 feasibility and research-training approval remain pending.

## Three concepts for viva

1. **Convert before resize:** source ICC → standard sRGB → resize; full-resolution CAM uses the same managed image. Tamil: model image-க்கும் CAM original-க்கும் ஒரே colour meaning வேண்டும்.
2. **Raw hash versus managed hash:** original bytes/pixels remain evidence; ICC may change RGB numbers, so CAM matches managed pixels. Tamil: நிறத்தைச் சரியாகக் காட்ட RGB number மாறலாம்; source file மாறாது.
3. **Fixed sRGB byte and guard:** no private profile survives; malformed or lossy/ambiguous conversion stops. Tamil: private metadata எடுத்துச் செல்லாமல் standard colour policy மட்டும் இருக்கும்; இது clinical validation அல்ல.

Viva: **Why not delete ICC and leave the RGB numbers?** ICC tells a viewer what those numbers mean. Converting to standard sRGB preserves the declared colour interpretation within representable/quantised limits; blindly deleting ICC can change appearance.


## 2026-10-15 — Authorised local v3 packaging stopped on first safety failure

The owner subsequently authorised local packaging for the exact v3 bundle ID and pinned cohort; the actual decision/date/hash-bound record is saved. Local licence/project-scope review found no documented conflicting local-copy restriction and claims no institutional, clinical, supervisor or cloud approval.

The unchanged builder's live SHA stage verified **733/733 MATCH** and all 733 source headers passed. First actual source **Training/00001** then failed its colour round-trip guard: measured **7 channel levels > approved 2**. Processing stopped before the first PNG write: **0 Training, 0 Validation, 0 CAM copies; no manifest/ZIP**, so archive size/SHA are not applicable. The failed source bytes still match their original hash. No retry, exclusion, guard/code/label/split change, upload, model operation or new tests occurred. See [exact stopped-attempt report](vision_local_packaging_attempt_v3_20261015.md) and its ignored evidence. Further work requires a focused review/instruction; do not silently relax the limit or overwrite the retained empty output directory.
