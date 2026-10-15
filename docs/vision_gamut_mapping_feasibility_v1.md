# Generated-only gamut-mapping feasibility study v1

2026-10-15, branch **vinuthan**. Isolated numerical study, not an exporter, dataset decision or clinical experiment. No production activation, changed budgets, real-image access, packaging, training, installs/downloads, commit or push.

## Protocol fixed before execution

Ten 100×100 generated RGB cases: sRGB identity; safe interior patches; gamma2.2 shadows; one saturated-red spot at matrix expansions 2^-12,2^-10,2^-6; 10 and11 strong red spots; dense red palette at2^-8; mixed shadows/100 red spots at2^-8. All red spots use synthetic RGB(224,48,0), not a sampled dental pixel. ICC matrix red/blue expansion preserves white; source TRCs are generated pure-power functions. Fixed source matrices/TRCs and image construction are independent of dataset/Test evidence. No random parameter search or post-result fixture/method adjustment.

Methods: actual Pillow intent1/flags0 baseline; locally supported intents0/2/3 with flags0; one experimental coordinate search on out-of-gamut unique source colours. Search starts from baseline, uses steps8,4,2,1, two sweeps per step and R/G/B coordinate order. At each update compare centre/lower/upper legal eight-bit code values in D50 Lab; keep minimum error, prefer centre on ties. Bounded local search, not a global optimum or perceptual/clinical colour guarantee. No real image or profile is an input to the public study runner.

Measure actual source→output D50 ΔE76 mean, P99.9 enclosing upper and maximum; intrinsic source→unbounded-relative-sRGB gamut count/fraction/excursion; reverse RGB; source/output hashes, output changes and finite/malformed/unsupported controls. Preserve source-intrinsic gamut measurements for every method. Bounded output values are a separate check and cannot replace original excursion evidence.

Compare the unchanged frozen Option A **numerical conditions**, including0.01 reserve and extent/severity limits, through the existing pure evaluator. A numerical PASS is not full policy/authorization/production eligibility; all workflows remain ineligible for production. Intents other than1 are explicit study alternatives, not silently treated as the approved recipe. Malformed/non-RGB/unsupported profiles must reject, not receive fabricated metrics. Independent generated matrix/TRC equations check Lab and excursion measurements; focused tests check determinism, no image/file access and unchanged production protections.

## Actual results

**34 focused tests passed, 0 failed, 0 errors, 0 skipped (2.49 s).** Separate standalone study executed all **50 method/case combinations**. Runtime: Python3.12.14, NumPy2.3.5, Pillow12.3.0, LittleCMS2.19, pytest9.1.1, existing Mac CPU environment. Nothing installed. Fixture parameters and method settings above were not changed after results.

All four intents were reported supported and executed. **Perceptual0, saturation2 and absolute3 were byte-identical to relative1 on every generated case**. These generated matrix/TRC profiles do not provide a useful alternative perceptual mapping here; support does not mean a distinct gamut-compression algorithm. This finding is not generalized to arbitrary LUT profiles/CMS implementations.

All cases have N=10,000. These **original source-intrinsic** metrics are identical across all five methods; bounded mapped outputs do not replace them:

| Fixture | Gamut count | Fraction | Maximum excursion |
|---|---:|---:|---:|
| identity | 0 | 0 | 0 |
| interior | 0 | 0 | 0 |
| shadows | 0 | 0 | 0 |
| red_weak_1 | 1 | 0.0001 | 0.002413078 |
| red_medium_1 | 1 | 0.0001 | 0.009586153 |
| red_strong_1 | 1 | 0.0001 | 0.151913077 |
| red_strong_10 | 10 | 0.0010 | 0.151913077 |
| red_strong_11 | 11 | 0.0011 | 0.151913077 |
| red_dense | 8,332 | 0.8332 | 0.044187974 |
| mixed | 82 | 0.0082 | 0.044187974 |

For each **Baseline** row below, all four ICC intents have exactly the same measured results. **Search** is the isolated coordinate-search strategy. PASS/FAIL concerns all frozen **numerical colour conditions only**, not full production eligibility, authorization or acceptance of another rendering recipe. Values shown rounded; decisions use full precision and the existing evaluator.

| Fixture | Method | Mean ΔE76 | P99.9 upper | Maximum ΔE76 | Reverse max | Budget |
|---|---|---:|---:|---:|---:|---|
| identity | Baseline | 0.001550 | 0.001717 | 0.001717 | 0 | PASS |
| identity | Search | 0.001550 | 0.001717 | 0.001717 | 0 | PASS |
| interior | Baseline | 0.322492 | 0.510735 | 0.510735 | 0 | PASS |
| interior | Search | 0.322492 | 0.510735 | 0.510735 | 0 | PASS |
| shadows | Baseline | 0.082261 | 0.227673 | 0.227673 | 4 | PASS |
| shadows | Search | 0.082261 | 0.227673 | 0.227673 | 4 | PASS |
| red_weak_1 | Baseline | 0.000866 | 0.001000 | 0.172027 | 5 | PASS |
| red_weak_1 | Search | 0.000866 | 0.001000 | 0.172027 | 5 | PASS |
| red_medium_1 | Baseline | 0.000917 | 0.001000 | 0.682274 | 10 | FAIL |
| red_medium_1 | Search | 0.000903 | 0.001000 | 0.542457 | 10 | FAIL |
| red_strong_1 | Baseline | 0.002223 | 0.001000 | 13.749235 | 34 | FAIL |
| red_strong_1 | Search | 0.001923 | 0.001000 | 10.741853 | 37 | FAIL |
| red_strong_10 | Baseline | 0.014597 | 0.001000 | 13.749235 | 34 | FAIL |
| red_strong_10 | Search | 0.011589 | 0.001000 | 10.741853 | 37 | FAIL |
| red_strong_11 | Baseline | 0.015972 | 13.749235 | 13.749235 | 34 | FAIL |
| red_strong_11 | Search | 0.012664 | 10.741853 | 10.741853 | 37 | FAIL |
| red_dense | Baseline | 1.434364 | 3.404485 | 3.404485 | 19 | FAIL |
| red_dense | Search | 1.166819 | 2.726249 | 2.726249 | 20 | FAIL |
| mixed | Baseline | 0.095593 | 2.983000 | 3.404485 | 19 | FAIL |
| mixed | Search | 0.092955 | 2.444000 | 2.726249 | 20 | FAIL |

The identity case reproduces unchanged pixels; its tiny nonzero Lab difference reflects the generated-versus-serialized profile numerical distinction, not a visible-change claim. Shadow reverse error4 does not fail the forward composite. Malformed, non-RGB and unsupported-class controls were rejected before measurement. Deliberately ignoring the source profile gave mean ΔE7.320008 /maximum7.737181 and failed the forward conditions.

## Answers and limits

1. **Methods:** relative/perceptual/saturation/absolute ICC conversions plus bounded Lab-error coordinate search; no third-party mapping library or downloads.
2. **Reduction:** search reduced colour error in six stress cases; e.g. dense-red maximum3.404485→2.726249 and mean1.434364→1.166819. It does not remove original source out-of-gamut excursions or establish safer clinical appearance. Reverse error sometimes increased, e.g. strong-red34→37. Safe cases were unchanged.
3. **New budget passes:** **zero of six baseline-failing cases became PASS** with any tested alternative. Medium-red still fails excursion; strong-red1/10 fail maximum/excursion;11 spots additionally fail tail/count/fraction; dense-red fails every numeric colour budget; mixed fails tail/maximum/count/fraction/excursion. No original source gamut failure can be made to disappear simply by bounding the output. Reporting post-map count0 instead would change policy semantics and is expressly not done.
4. **Production qualification:** **not justified as an unblocking step under the current policy**. The tested mapper reduces a numerical objective but does not meet the frozen conditions on failed stress cases. No production wiring, activation or real packaging retry is recommended from this evidence.
5. **Unknown:** global optimal mapping, arbitrary ICC LUT behaviour, other runtimes, real-source/cohort feasibility, smoothness/hue/texture effects, clinical fidelity and practical full-resolution performance. The search is local and does not prove that no other sRGB mapping could reduce ΔE further. Source-intrinsic gamut checks remain a separate mathematical constraint regardless. No dental or Test image/profile/pixel was used, including as a fixture.

**Conclusion: NOT PROMISING for unblocking frozen Option A packaging.** There is limited promise for reducing synthetic ΔE, which is a different result from satisfying all current guards.

**ONE next recommended action:** prepare a separate **plan-only metadata-safe canonical/wider-gamut RGB representation proposal**, including consistent model preprocessing and display/CAM colour interpretation. Reuse the existing Option B discussion; do not implement it, change budgets or process real images without new authorization. It is not a drop-in ICC-preservation fix.

## Verification and preservation

Tests cover deterministic source/profile bytes and outputs; independent NumPy matrix/TRC→XYZ/Lab and inverse-matrix sRGB references (existing generated-fixture0.01 ΔE allowance,1e-6 excursion allowance, not clinical tolerances); per-pixel search error never increasing; unchanged in-gamut pixels; original gamut evidence preserved across methods; malformed/wrong profiles; unsupported intent with no fallback; NaN/±Inf rejection; no source mutation. A complete study run with `open`, `Path.open`, `Image.open`, image saving, packaging and authorization patched to fail passed. Production source hashes/configuration remain unchanged.

New files: `src/vision/gamut_mapping_feasibility.py`, `tests/test_gamut_mapping_feasibility.py`, this report. Existing diary/AI log receive one factual append-only task entry. Ignored evidence: `data/vision/gamut_mapping_feasibility_v1_20261015/study.json`, `tests_initial.log`, `junit_initial.xml`, verification/preservation JSON. All50 measured records, including identical-intent rows and full QA summaries, are retained. No prior test suite, Colab workflow or real diagnosis was repeated. This is not a repository-wide test result or real-image qualification.

Owner explanation: (1) rendering intent support does not guarantee different pixels; (2) the search keeps a candidate only when Lab error is no larger; (3) original gamut metrics remain attached to the source, so reducing ΔE cannot erase their failures. Viva: **Can bounded RGB output prove colour preservation?** இல்லை. எல்லா output channels0–255-க்குள் இருந்தாலும் source நிறங்கள் மாறியிருக்கலாம்; original-versus-output colour difference மற்றும் source gamut evidence இரண்டையும் பார்க்க வேண்டும்.
