# Training/00001 — focused colour diagnostic v1

2026-10-15; branch **vinuthan**. Owner-authorised read-only, single-source diagnosis. **No implementation/guard change, image export, packaging retry/ZIP, Test access, model operation, installation, commit or push.** Original RGB arrays and ICC bytes remained in memory; no image, coordinates, thumbnail, raw ICC or private metadata values saved. Only aggregate numbers and source identity/hash are retained.

## Source and exact production reproduction

- Source: `data/vision/gingivitis/staging-16669f74665ff0deca6ddd25feb0d233e52fdc2313265465bf91731af1e8956b/Dataset/Training/Images/00001.jpg`; 7286×4863 = **35,431,818 pixels**.
- Original SHA-256 before/after: `48d69e63d549710a2ca850490cf760b613a41ce51d2b0bc62e7419c9f4f828a2` — MATCH.
- Supported source profile: monitor (`mntr`), RGB, XYZ PCS, matrix-shaper; relative-colorimetric input/output both supported. Estimated three-channel TRC gamma ≈2.199219. No descriptive/camera/creation/serial ICC fields were recorded.
- Existing forward source ICC→generated sRGB and reverse sRGB→source ICC used RGB 8-bit, intent 1, flags 0, no black-point compensation, unchanged geometry/orientation. Maximum source-channel reverse error **7**, reproducing the packaging stop at limit **2**. Source→source identity control maximum **0**.
- Runtime: Python 3.12.14, Pillow 12.3.0, NumPy 2.3.5, Pillow-linked LittleCMS 2.19. No completed synthetic suite rerun.

## Actual reverse RGB differences

Each channel has 35,431,818 observations. Statistics are absolute source-versus-restored 8-bit code differences; percentiles use exact linear interpolation over integer histograms.

| Channel | Max | Mean | Median | P90 | P95 | P99 | P99.9 | P99.99 | Count >2 | % >2 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| R | 4 | 0.001713855 | 0 | 0 | 0 | 0 | 1 | 1 | 279 | 0.000787428 |
| G | 4 | 0.031286738 | 0 | 0 | 0 | 1 | 4 | 4 | 112,920 | 0.318696602 |
| B | 7 | 0.039002599 | 0 | 0 | 0 | 1 | 4 | 4 | 157,994 | 0.445909945 |

**216,833 distinct pixels (0.611972550%) exceed 2 in at least one channel.** Channel counts overlap and must not be added as distinct pixels. All 271,193 channel observations exceeding 2 have original values ≤31; zero such observations above 31. Every affected pixel has at least one output sRGB endpoint (0/255), but endpoints alone do not prove gamut clipping.

| Per-pixel maximum error | Pixels |
|---:|---:|
| 0 | 34,148,846 |
| 1 | 1,038,729 |
| 2 | 27,410 |
| 3 | 70,902 |
| 4 | 145,919 |
| 5 | 6 |
| 6 | 4 |
| 7 | 2 |

**Maximum 7 occurs at only 2 pixels**, not across the picture. Errors 5–7 occur at 12 pixels total. Most pixels exceeding 2 have errors 3–4. Per-pixel maximum error: median/P90/P95 =0; P99=1; P99.9/P99.99=4; mean=0.053341858.

## Separate quantisation, gamut and transform controls

Floating-point diagnostic transforms use the **same installed LittleCMS library**, same source ICC, directly generated sRGB, intent 1, flags 0. Double RGB permits extended-range values without intermediate 8-bit clipping/rounding; double D50 Lab avoids Pillow 8-bit Lab encoding ambiguity. These are diagnostic controls, not a newly approved exporter.

- Unclipped floating source→sRGB→source: maximum **0.002034239** source-code-equivalent levels; mean **0.000003160584**. This demonstrates high numerical invertibility when no 8-bit destination clamp/rounding occurs; it does not mean negative sRGB is exportable.
- Explicitly clipping floating sRGB to [0,1], rounding to 8-bit, then reversing: maximum **7.267928431** source levels. This reproduces the magnitude of the observed 7, supporting destination quantisation/clipping rather than malformed ICC or unsupported intent as its mechanism.
- **9,355 pixels (0.026402822%)** have at least one floating sRGB component below −1e-6; none exceeds 1+1e-6. Minimum −0.006280792; maximum 0.901876748. These are numerical out-of-sRGB-gamut candidates requiring a clamp for an ordinary bounded PNG. This diagnostic epsilon is a numerical check, not a clinical or new production tolerance.
- Of pixels exceeding production reverse tolerance 2, **2,647** are outside that floating gamut criterion; **214,186** are not. Therefore gamut clipping alone cannot explain most >2 errors; low-code quantisation dominates that count. Conversely, real gamut loss is not zero.
- The separate largest-error check confirms **all 6 error-5, all 4 error-6 and both error-7 pixels are outside sRGB**. For the error-7 subset, unclipped floating inverse error ≤0.002034239 levels, whereas clipped/rounded inverse error reaches 7.267928431. Thus the two maximum outliers are associated with gamut clipping together with low-code quantisation; they must not be described as pure harmless rounding.
- NOOPTIMIZE diagnostic control still reaches **7** (125,821 pixels >2); changing optimisation does not eliminate the failure. Production flags remain 0. Its counts differ because the numerical transform path differs.
- Absolute forward raw RGB number change reaches 20, which alone is not a colour-loss metric: different ICC encodings assign different meanings to RGB numbers.

### Diagnostic cross-check issue, resolved without changing production

The first diagnostic cross-check expected packed C RGB to equal Pillow output exactly, but it failed before saving its final JSON. A second observational run retained aggregates and revealed a ≤1-level discrepancy in a bounded 512×512 probe. The cause was serialising a generated sRGB profile to ICC fixed-point fields before reopening it. With that same serialised profile, Pillow and C RGB/RGBA agree exactly on the probe; the generated-versus-serialised profile is the differing input, not an accepted production change. Finally, C `cmsCreate_sRGBProfile()` was used directly to match Pillow. **Final full-image C/Pillow forward and reverse mismatch counts are both zero.** Only final matching-profile measurements above are authoritative. Preliminary logs and `layout_crosscheck.json` retain this diagnosis; no source/production function was modified. These repeated computations were restricted to this one authorised image, not a dataset re-audit.

## Forward colour-managed difference, not clinical accuracy

ΔE76 compares source-RGB interpreted with its source ICC against the **actual production forward sRGB output** interpreted as generated standard sRGB, both transformed into double-precision D50 Lab. Per-pixel distances are retained only as aggregate statistics (percentiles computed from float32 distances; no spatial information).

| ΔE76 statistic | All pixels | Pixels with reverse error >2 |
|---|---:|---:|
| Mean | 0.278112676 | 0.221732239 |
| Maximum | 0.840949476 | 0.840949476 |
| P50 | 0.270075440 | 0.215846822 |
| P90 | 0.431293249 | 0.327223033 |
| P95 | 0.473226160 | 0.379926473 |
| P99 | 0.535694599 | 0.379926473 |
| P99.9 | 0.596127510 | 0.397727609 |
| P99.99 | 0.649260044 | 0.491067767 |

This shows a small numerical profile-relative forward difference and a rare reverse-code extreme, **not a measured large whole-image discrepancy**. It does not establish visual indistinguishability, clinical acceptability, calibrated camera/display accuracy, or preservation of diagnostic information. ΔE76 is not a clinical threshold; no observer study, calibration target, dental adjudication or acceptance threshold is supplied. The source profile itself may not accurately describe photographed tissue.

## Engineering options and ONE next action (proposed only)

| Option | Assessment |
|---|---|
| Raise the integer limit from 2 to 7, remove ICC, or exempt this image | Reject: fitted to a failed source, ignores real clipping or changes colour interpretation. |
| Disable optimisation / change rendering intent | NOOPTIMIZE still fails at 7; a new intent changes policy without solving representability. |
| Increase intermediate/export bit depth | Reduces quantisation but cannot place negative sRGB colours inside bounded sRGB; changes downstream format/runtime and is not the smallest fix. |
| Add forward colourimetric QA with explicit gamut-loss reporting | Recommended: measure the actual output appearance interpretation rather than equating gamma-encoded reverse integers with colour preservation. |

**Next single engineering action:** implement a small, separately tested **forward-colour QA helper** returning D50 Lab ΔE distribution, gamut-excursion counts/magnitudes and existing reverse-error statistics. Keep the current fail-closed production gate in force until a replacement composite acceptance rule and its fixed engineering bounds are explicitly approved. Do not choose bounds from 00001 merely to pass it; establish them with independent generated-profile fixtures, document quantisation versus real clipping, and route ambiguous/out-of-gamut cases to review. This is the minimal prerequisite to a defensible guard revision, not approval to package now. A maximum reverse-code difference alone is overly restrictive as a perceptual-preservation criterion, while also catching genuine nonzero clipping; it cannot decide clinical safety.

Required focused regressions for that helper/any later approved guard:

1. Generated sRGB identity: exact pixels, zero colour error/gamut flags, source SHA unchanged.
2. Generated gamma≈2.2 shadow ramps and matrix RGB fixtures: independently verified Lab reference; distinguish expected >2 reverse-code quantisation from actual forward error without raising the old cap silently.
3. Generated out-of-sRGB-gamut colours and deliberate wrong-profile/large colour shifts: detect clipping/excursions; reject/review under separately predefined bounds, even if a percentile averages them away.
4. Directly generated versus serialised sRGB fixtures: match identical-profile reference transforms; RGB/RGBX agreement; finite Lab results, invalid/missing/unsupported profiles and CMS exceptions fail closed.
5. Preserve geometry/alignment, original file SHA, metadata allowlist and independent payload hashes; retain existing Test/held/NP015/group rejection cases using generated records only.

**Fresh packaging authorisation is required** after any approved implementation/acceptance-policy revision: scoped tests, new code hashes, true owner/date bindings and a fresh output ID. Previous 733-candidate/three-CAM authorisation does not authorise changing the failed guard. No clinical, supervisor, institutional, upload or training approval is inferred. Packaging remains BLOCKED; no retry is performed.

## Evidence, preservation and teaching notes

Ignored local evidence: `data/vision/colour_diagnostic_00001_v1_20261015/` contains aggregate JSON/logs and RAM-only diagnostic recipes. No source pixels/coordinates/private ICC descriptions or bytes are persisted. `aggregate_diagnostics.json` and `extreme_aggregate.json` are the final numerical records; `preservation_verification.json` records existing-file preservation. Production source/tests, 95-check evidence, frozen cohort and previous packaging attempt are unchanged. Only this new report and append-only diary/AI log are project documentation changes.

Three blocks: (1) `profileToProfile(... intent=1, flags=0)` reproduces exactly what failed. (2) Per-pixel/channel histograms distinguish 2 maximum outliers from 216,833 tolerance failures without saving spatial data. (3) Actual-output→Lab versus source→Lab measures forward profile-relative colour difference; unclipped/quantised controls explain why reverse RGB integers differ.

Viva: **Why can seven RGB levels coexist with ΔE76 below one here?** RGB code spacing is nonlinear and profile-dependent. Dark-channel quantisation/clipping can produce several reverse source-code levels while the forward Lab distance remains small. Neither number alone establishes clinical acceptability.

Technical references: [Pillow ImageCms API](https://pillow.readthedocs.io/en/stable/reference/ImageCms.html), [Pillow 12.3 CMS implementation](https://github.com/python-pillow/Pillow/blob/12.3.0/src/_imagingcms.c), [LittleCMS 2.19 API/format definitions](https://github.com/mm2/Little-CMS/blob/lcms2.19/include/lcms2.h). These describe transforms/formats, not dental safety limits.
