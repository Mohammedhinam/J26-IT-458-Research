# PP1 exploratory colour-acceptance proposal v1

2026-10-15; branch **vinuthan**. Policy ID: `pp1-colour-policy-proposal-v1-20261015`. **PROPOSED / OWNER DECISION PENDING / NOT IMPLEMENTED / NOT ACTIVE.** One conservative policy for provisional, non-clinical, non-final PP1 exports only. Participant independence remains unverified. It does not approve clinical labels, a final manifest, upload or training.

Read AGENTS.md and the [existing diagnostic/helper evidence](vision_forward_colour_qa_v1.md). Reused the saved 40-test record and generated-fixture aggregates; no tests, real-image investigation or packaging repeated. Source code, current reverse limit 2, previous approvals and evidence remain unchanged.

## Reference basis and limits of the evidence

[CIE's ΔE76 definition](https://cie.co.at/eilvterm/17-23-077) specifies Euclidean distance in CIELAB. [CIE 199:2011's public summary](https://cie.co.at/publications/methods-evaluating-colour-differences-images) discusses comparing similar images under comparable media/viewing conditions. Neither supplies a dental-export acceptance tolerance. [CIE 230:2019's summary](https://cie.co.at/publications/validity-formulae-predicting-small-colour-differences) studies formula performance, including differences below 2 CIELAB units; it does **not** establish 2 as invisible or clinically acceptable. [ISO/CIE 11664-6:2022's public summary](https://cie.co.at/publications/colorimetry-part-6-ciede2000-colour-difference-formula-1) describes corrections for variation in colour-difference perception. ΔE76 is therefore retained as a reproducible numerical metric, not a universal visual or medical judgment. These references were read as public summaries/definitions, not as full paid standards.

[ICC guidance](https://www.color.org/displaygamut/) supports comparing compatible profile coordinates in a common D50 PCS; [ICC profile-assessment guidance](https://www.color.org/faqs/) separates colourimetric assessment from observer assessment and notes the influence of source/destination gamuts. The latter also cautions that camera profiles depend on illumination. None prescribes the project-specific limits below.

**Engineering choices:** nominal mean/tail/maximum budgets **0.50 / 1.00 / 2.00 ΔE76** form a deliberately restrictive hierarchy: low whole-image average, a tighter limit for at least 99.9% of pixels, and a bounded worst pixel. The ratio is a transparent project budget, not a derived probability, an industry-mandated tolerance or a just-noticeable-difference claim. Taking 2 as the top nominal budget keeps the proposal within the small-numerical-difference regime discussed by CIE; that context does not validate its clinical effect. These constants are not fitted to any source image, grade, model outcome or Test evidence, and may reject much of the pinned cohort.

An additional **0.01 ΔE engineering reserve** is charged to each statistic. This reuses the existing independent generated-reference agreement allowance rather than treating every digit as certain. Saved example maximum-ΔE reference residuals are 0.000000250, 0.000749654 and 0.002782908. This reserve is **not** a proven worst-case error bound over every possible ICC profile/runtime. A future implementation must first pass the independent fixture qualification; unqualified transforms/runtimes fail closed.

## One prospective decision table — all conditions required

Evaluate every pixel of each full-resolution, aligned source→actual eight-bit sRGB conversion in D50 Lab **before resizing**; no masking by tooth position, label, brightness or split. Keep intent 1 / flags 0 / no BPC. Let `N>0` be pixel count, `U99.9` the helper's enclosing upper bound for the nearest-rank P99.9, and `e(p)=max over RGB channels of max(0, -r, r-1)` for extended, unclipped normalized sRGB.

| Check | Exact proposed acceptance condition | Rationale/evidence and mandatory failure |
|---|---|---|
| Forward mean | `mean(ΔE76) + 0.01 ≤ 0.50` (observed mean ≤0.49) | Constrains widespread drift. An acceptable maximum alone cannot substitute for this check. |
| Forward tail | `U99.9(ΔE76) + 0.01 ≤ 1.00` (upper bound ≤0.99) | Constrains almost all pixels; use the **upper** 0.001-bin bound, never its lower edge/midpoint or rounded display value. |
| Forward worst pixel | `max(ΔE76) + 0.01 ≤ 2.00` (observed max ≤1.99) | Prevents the mean/tail from hiding a small number of large discrepancies. No isolated-pixel exemption. |
| Gamut pixel count | `C = count(e(p) > 1e-6) = 0` | **No genuine-gamut-loss allowance** is proposed without evidence supporting one. One above-epsilon pixel rejects the image/package attempt. |
| Gamut fraction | `C / N = 0` (exactly **0%**, not rounded to 0%) | Prevents a large image from disguising nonzero excursions as a tiny percentage. Count and fraction are intentionally redundant cross-checks. |
| Gamut excursion | `max(e) ≤ 1e-6` normalized encoded sRGB | Existing numerical reporting epsilon only: 0.000255 of an eight-bit code level. Raw nonzero-excursion counts/max remain logged even below epsilon. This is not proof of literally zero loss or a clinical tolerance. |
| Transform/integrity | All profile/mode/orientation/geometry/hash/metadata, finite-value, runtime qualification and `N`-coverage checks pass; all required statistics present | Any missing/NaN/Inf/unsupported/ambiguous/partial result rejects. No fallback to untagged colour, another intent, a missing statistic or a mean-only test. Existing untagged-as-sRGB contract is preserved only where already explicitly permitted. |
| Reverse RGB | Record all existing max/count diagnostics, including `>2`; **only after separately approved implementation** they cease to be the sole colour hard stop | Saved generated shadow ramp: reverse max 4, forward mean 0.082290276/max 0.227673421, no gamut excursions. Quantisation alone need not fail the future composite. **Today the production hard stop is still 2.** |
| Cohort/package safety | Existing owner/hash bindings, all holds/NP015/group/Test isolation, source preservation and metadata/export checks remain mandatory | A colour failure stops the attempt; no automatic source exclusion, substitute image, grade change, partial completed bundle or threshold adjustment. CAM full-resolution copies use the same policy; resized derivatives retain their existing exact resize/hash checks. |

Every `≤` is inclusive on full-precision measurements; values just above fail. No extra undocumented epsilon is added at policy boundaries. The 0.01 reserve is distinct from the 0.001 histogram bin width and from the gamut numerical epsilon. Whole-image statistics are evaluated per source image, never averaged across the 733 records. An out-of-gamut image remains rejected even if all ΔE statistics pass.

Saved generated-fixture evidence supports the intended separation: the shadow and interior fixtures have low forward differences and no above-epsilon gamut excursions; the expanded-gamut fixture has mean/max ΔE 12.902048868/26.658965929, 2/3 gamut pixels and maximum normalized excursion 1.291863441, and would fail. These are comparisons of existing saved numbers with the proposal, **not newly run policy tests or proof of general sensitivity**. The final gate does not exist yet.

The already documented Training/00001 gamut finding is incompatible with this zero-above-epsilon-clipping policy. It therefore **remains blocked**, based on existing evidence only; its diagnosis was not rerun. No statement about the other 732 candidates' eligibility is made. If this strict proposal prevents the fixed cohort from being packaged, stop: a different gamut/representation decision would require a new documented approval, not tuning these limits until all images pass.

## Explicit replacement process, not a bypass

After owner approval of this exact proposal, a **separate implementation instruction** may authorize a new versioned composite colour gate. That change would explicitly replace only the old reverse-max-based acceptance decision; reverse statistics remain in provenance. The actual export pixels, source RGB hashes, metadata policy and other research/data gates must remain checked. No try/except around the old error, per-image exemptions, silent fallback, old-authorization reuse or dual-policy auto-selection is permitted.

Future implementation must fail before payload write on any composite failure and bind the policy ID, constants, runtime/source hashes and measured QA record to its authorization/manifest. Scoped synthetic regressions must pass before any real-image attempt. A fresh, explicit local-packaging instruction/hash-bound authorization and fresh output ID are still required afterward. **This document changes no executable rule or existing approval.**

## Minimum synthetic regression additions for a future authorized implementation

1. **Boundary/AND logic:** test below/equal/above 0.49 mean, 0.99 tail-upper and 1.99 max; a single violating statistic rejects even when others pass. Verify 0.001-bin upper-bound use, small-`N` nearest-rank semantics, full-precision comparison and missing/overflow/incomplete statistics. Outlier fixtures must not pass through averaging.
2. **Gamut boundaries:** generated extended-RGB cases at/below/above `1e-6`, one-pixel excursions, both upper/lower boundaries, overlapping channels and different image sizes. Any above-epsilon count/fraction or excursion rejects even with low ΔE; no rounding-to-zero acceptance.
3. **Independent physical encoding references:** reuse generated sRGB identity, pure-power shadow/interior profiles, expanded-gamut and wrong-profile cases. Add boundary fixture coverage prospectively; confirm NumPy matrix/TRC→XYZ→D50 Lab reference agreement within existing `0.01 ΔE` fixture allowance. A new fixture failure blocks qualification, not automatic tolerance widening. Do not modify 00001 or use dental/Test pixels as fixtures.
4. **Replacement behaviour:** synthetic quantisation-only reverse `>2` may pass **only** if every new criterion passes under explicit new authorization. Wrong-profile/clipping/non-finite/unsupported transforms reject. Old authorization, unknown/missing policy ID or unavailable QA must fail closed; no catch-and-continue route.
5. **Export/isolation regression:** generated-file source immutability, actual-versus-expected export hashes/pixels/geometry, metadata allowlist, CAM/resize consistency, Test/held/NP015/group rejection and no file before acceptance. Retain tiled reproducibility, bounded arrays and native-handle cleanup from the existing focused suite.

No tests were added or executed for this proposal. Existing **40 passed / 0 failed / 0 skipped** remains the historical helper result, not verification of a new gate.

## Remaining uncertainty and next single action

No technical metric alone establishes source-camera colour truth, controlled display appearance, clinical tissue fidelity, label validity or participant independence. These need acquisition/calibration/qualified research evidence beyond a file conversion check. The proposed constants are owner-reviewable engineering risk choices; references do not make them medically validated. The limited generated fixtures and one previously diagnosed source cannot establish dataset-wide feasibility.

**Next single action: owner decision on this exact zero-above-epsilon-clipping composite proposal**, acknowledging that it does not unblock Training/00001 or guarantee all 733 records. Approval of the proposal would still not authorize implementation or packaging unless that separate scope is explicitly granted. Current code, guard 2, datasets, Test boundary, approvals and dirty tree are preserved. No install/download, inference/training, upload, commit or push.

Viva: **Why replace reverse RGB with a composite?** Reverse numbers depend on nonlinear coding/quantisation. Forward Lab plus a strict gamut check separately measure output colour difference and representability loss; neither certifies clinical colour accuracy.
