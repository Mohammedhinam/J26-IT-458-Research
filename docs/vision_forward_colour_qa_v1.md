# Forward-colour QA helper — diagnostic v1

2026-10-15, branch **vinuthan**. **40 focused synthetic tests passed, 0 failed, 0 errors, 0 skipped (0.18 s).** No original dental image/header was opened, transformed or exported. No dataset audit, previous real-image diagnosis, old test suite, packaging, cloud/model operation, install/download, commit or push was repeated.

## Scope and API

New `src/vision/colour_qa.py` exposes `diagnose_forward_colour(source, exported_srgb=None, tile_pixels=65536)`. Inputs are caller-owned PIL images, not paths/manifests. The helper cannot scan a cohort or write an image/archive. It is **not connected to the exporter or training gate**. Existing `exploratory_bundle.py`, `ROUNDTRIP_LIMIT = 2`, approved-training safeguards and versioned code ZIPs remain byte-identical.

- Reuses `check_source_colour` for source RGB/orientation/profile/intent rules and the existing explicit untagged-as-sRGB contract. It does not invent a missing-profile interpretation.
- With no output supplied, simulates the existing intent-1/flags-0 forward conversion **per tile in memory**. With supplied output, measures those actual aligned, full-resolution standard-sRGB pixels. Supplied output must have identical geometry, RGB mode, and absent metadata or only the fixed `srgb=1` declaration. Profile-bearing, ambiguous, private-metadata-bearing or misaligned output is rejected. Resized/letterboxed images are intentionally outside this pixel-aligned diagnostic API.
- Reports source-profile Lab versus actual output-sRGB Lab **ΔE76 in D50**, separate source→sRGB extended-floating gamut counts/excursions, and separate actual-output→source reverse RGB statistics.
- Output always states `diagnostic_only=True` and `acceptance_decision="not_evaluated"`. A finite result is neither an image approval nor evidence of clinical colour accuracy.

Pillow's installed `_imagingcms` library supplies LittleCMS. A small ctypes binding uses its documented double-Lab/extended-RGB formats: no extra dependency or alternative colour engine. Direct `cmsCreate_sRGBProfile()` matches Pillow's generated profile without the serialization-rounding mismatch documented in the earlier diagnosis. Missing symbols/profile handles/transforms or non-finite results fail closed; native handles are released even after partial initialization/failure. Unsupported platforms get an error, not a fallback or permission to package.

## Statistics and memory

| Measurement | Meaning |
|---|---|
| Forward ΔE76 | Count, mean, min/max and enclosing percentile bins at P50/90/95/99/99.9; numerical profile-relative difference, not clinical assessment |
| Gamut | Unique pixels outside [0,1] beyond numerical epsilon `1e-6`, count/percentage, below/above counts, per-channel counts and maximum excursions; normalized encoded-sRGB units |
| Excursion magnitude | Maximum per channel/overall and mean across all channel samples; also report raw nonzero-excursion pixel count so the numerical epsilon does not conceal its existence |
| Reverse RGB | Per-channel and per-pixel-maximum means/maxima/nearest-rank percentiles and counts exceeding the **unchanged current limit 2** |

Below/above and channel counts can overlap; unique pixel counts use `any` and must not be reconstructed by summing channels. A destination channel at zero alone is not proof of gamut loss; the extended transform is used instead.

Tile size defaults to 65,536 pixels, is capped at 262,144, and bounds both rows and columns even for very wide inputs. No full-size Lab/floating/forward/reverse arrays or per-pixel samples are retained. Fixed Lab histogram storage is **512,001 × 8 = 4,096,008 bytes**. ΔE bins are 0.001 wide up to 512 with an explicit overflow bin; outliers retain their exact maximum, mean contribution and overflow count. Percentiles are enclosing nearest-rank bounds, not falsely precise exact percentiles. Reverse statistics use exact integer histograms.

Pillow can decode each original caller-owned RGB input fully; those input images are not promised to be streamed from disk. Working arrays are tile-bounded in addition to these inputs and native CMS tables. Tests instrument the transform buffer sizes; **no real/full-resolution memory benchmark or 16-GB-machine RSS measurement is claimed**. The helper does not solve image I/O authorization; callers must retain separate cohort/Test/privacy gates.

## Independent generated-fixture evidence

The tests generate ICC profiles with explicitly encoded pure-power TRCs and known XYZ matrices; an intentionally expanded red/green gamut preserves the white point. Expected colours are calculated separately in NumPy using the encoded matrix/TRC, standard sRGB transfer equations, XYZ→D50 Lab and Euclidean ΔE76. Expected gamut excursions are calculated through the independent inverse matrix/transfer equations. Pillow forward/reverse conversions also cross-check the helper's packed-RGB CMS path. No Training/00001 measurements are used to set assertions.

| Generated fixture | Pixels | Reverse max | Forward ΔE76 mean | Forward ΔE76 max | Gamut pixels |
|---|---:|---:|---:|---:|---:|
| Neutral shadow ramp, gamma≈2.2 | 32 | 4 | 0.082290276 | 0.227673421 | 0 |
| Interior RGB patches, gamma≈1.8 | 3 | 0 | 0.135866428 | 0.154988731 | 0 |
| Expanded-gamut red/green + neutral | 3 | 21 | 12.902048868 | 26.658965929 | 2 |

For these examples, absolute analytic-versus-CMS maximum-ΔE discrepancies are respectively **0.000000250, 0.000749654, 0.002782908**. Test allowance `0.01 ΔE` is **reference implementation precision on generated fixtures only**, not permission to export a dental image, a universal transform-error guarantee or a clinical tolerance. Gamut reference allowance `0.002` is likewise a generated-fixture numerical agreement assertion in normalized RGB. The gamut example's maximum measured excursion is **1.291863441** normalized sRGB units.

Other tests cover discarded ICC and deliberately incorrect-profile conversion (large forward differences), metadata privacy, wrong geometry/mode/profile, malformed/non-RGB/unsupported ICC classes, repeatability, tile consistency, histogram overflow, unavailable CMS, injected NaN/±Inf, initialization/handle cleanup and no-write/no-package behaviour. A generated shadow source still raises at the existing exporter guard before any output file is written. A generated source file remains byte-identical after diagnosis. Existing dataset/manifest and real dental pixels are not test fixtures.

Initial run: **36 passed / 3 failed**, because the independent Pillow fixture retained an attached ICC profile and the helper correctly rejected its metadata. The fixture was corrected to a fresh pixels-only sRGB image; the helper validation was not weakened. The subsequent 39-case checks passed; an additional wrong-profile case and direct forward equivalence assertions produced the final **40/40** run. Initial and intermediate logs/XML remain retained. This is a selected new-module run, not a repository-wide test result or clinical verification.

Runtime: Python **3.12.14**, Pillow **12.3.0**, NumPy **2.3.5**, pytest **9.1.1**, LittleCMS **2.19**, CPU. Existing pure-Python pytest was made importable from the existing `.venv` after bundled dependencies; no package installation or environment modification.

Ignored evidence: `data/vision/forward_colour_qa_v1_20261015/` contains initial/intermediate/final pytest logs and XML, `synthetic_verification.json`, `generated_fixture_aggregates.json` and preservation verification. No real image payload or private ICC data is present. The earlier real-image diagnostic report and evidence are preserved and were read, not rerun.

## PROPOSED future composite policy — NOT ACTIVE

| Layer | Proposed decision rule | Status |
|---|---|---|
| Integrity/interpretation | Hash/geometry/metadata/profile/finite-transform checks must all pass. Never guess an ambiguous source profile or hide a failed image. | Existing gates preserved; no new activation |
| Numerical correctness | Identical transform settings and independent generated-reference regressions must pass. Declare runtime/profile generation and histogram precision. | Verified for selected fixtures on this Mac |
| Forward fidelity | Require **all** predefined mean, tail-percentile and maximum ΔE bounds, using upper percentile-bin bounds; never let an average mask isolated large shifts. | Numeric image-acceptance bounds **UNSET**, owner decision required before implementation |
| Gamut loss | Record unique count/fraction plus maximum excursion. Conservative default proposal: any excursion beyond numerical epsilon requires review; no silent clipping allowance. A future bounded-loss exception needs a separately documented count AND magnitude rule. | No allowance approved; epsilon is not permission to clip |
| Reverse evidence | Retain reverse counts/max as quantisation/clipping diagnostics. Any proposal to replace the current hard limit requires explicit approval; do not raise 2 to 7 or exempt a record. | Production hard stop **2 remains active** |
| Research/privacy | Keep provisional labels, no clinical validation claim, separate source-isolation/authorization gates and all existing exclusions. | No label/manifest/training approval inferred |

This policy is scientifically defensible as an engineering QA framework because it separates numerical correctness, forward colour difference, actual representability loss and human acceptance. It intentionally does **not** infer clinical tolerances from ΔE or synthetic tests. Fixed bounds must be selected prospectively from documented numerical/display requirements and independent fixtures, not tuned to pass Training/00001 or Test images. No colour acceptance policy alone proves diagnostic colour fidelity or tissue grading validity.

**Next single safe step:** owner review of this proposed composite specification, particularly the forward mean/tail/max bounds and how any genuine gamut loss is handled. These decisions are currently blockers. Only a separately authorised, regression-tested gate revision with new code hashes and a fresh packaging authorization/output can permit a future retry. The existing failed source remains blocked; the helper's successful synthetic checks do not unblock it. Cloud upload, model training and final-research approval remain separate.

## Three blocks and viva

1. `source_lab` versus `output_lab`: ஒரே D50 Lab அளவில் source/output நிறத்தை ஒப்பிடுகிறது; output ΔE statistics. RGB numbers மட்டும் ஒப்பிடுவதைவிட colour meaning-ஐ அளவிட உதவுகிறது.
2. `excursion > GAMUT_EPSILON`: sRGB-ல் அடங்காத நிறங்களை எண்ணுகிறது; output count/magnitude. Zero destination channel மட்டும் clipping என்று முடிவு செய்யவில்லை.
3. `acceptance_decision="not_evaluated"`: அளவீடு வந்தாலும் approval கிடையாது; பழைய limit 2 மற்றும் packaging gate தொடரும்.

Viva: **Can these tests certify clinical colour accuracy?** இல்லை. Generated profiles-ல் கணக்கு சரியாக இயங்குவதைச் சோதிக்கின்றன; உண்மையான tissue colour அல்லது clinical grading accuracy-ஐ validate செய்யவில்லை.
