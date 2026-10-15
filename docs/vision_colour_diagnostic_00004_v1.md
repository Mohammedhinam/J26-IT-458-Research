# Training/00004 — read-only colour diagnosis

2026-10-15; branch **vinuthan**. Owner authorized this original image only. **Confirmed engineering mechanism: the current relative-colourimetric source-ICC→bounded-sRGB conversion clips negative blue components in a small, concentrated high-chroma region. Clipping, with additional eight-bit quantisation, causes the frozen maximum/severity failures.** No implementation defect was found in the measured transforms. This does not validate the camera's assigned profile, clinical colour fidelity or an alternative export policy.

Only this report and one ignored non-sensitive aggregate JSON were created. No original/image export, crop, screenshot, coordinates, tile map, pixel-array dump, source ICC bytes or private metadata values were saved. Existing diary/AI log, code, DRAFT, annotations, labels, splits, policies, approvals and incomplete packaging evidence remain unchanged. No other original image, Test payload, packaging retry, upload, model, installation/download, commit or push was used.

## Identity and reproducibility

- Original: `data/vision/gingivitis/staging-16669f74665ff0deca6ddd25feb0d233e52fdc2313265465bf91731af1e8956b/Dataset/Training/Images/00004.jpg`.
- Pinned source SHA-256, verified **before and after** diagnosis: `7f77c3c96c9fa924b8c35eec3e3074d9f10ddb525b3ebd2bae1f567b62c35e7e` — MATCH. Target file metadata was projected from the hash-bound cached inventory without decoding annotation fields or Test labels; no other source image was opened.
- Dimensions: **7286×4863 =35,431,818 pixels**. Supported monitor (`mntr`), RGB, XYZ PCS matrix/shaper profile; three single-gamma TRCs, gamma **2.19921875**. Relative-colourimetric input/output supported, identity orientation. No ICC description/device/creation/serial fields recorded.
- Exact existing `v4._managed` conversion in RAM: generated standard sRGB, **intent 1, flags 0**, no black-point compensation, unchanged geometry. No alternative production transform or export was attempted.
- Existing QA transforms, finite checks and bounded distribution code were reused in **256×256 tiles, maximum 65,536 pixels per intermediate tile**. All **551 tiles** covered. Source/managed PIL images stay in RAM; full-image floating intermediate arrays were not retained. Runtime: Pillow 12.3.0, NumPy 2.3.5, LittleCMS 2.19; numerical pass **54.6183 seconds**.
- Prior attempt reproduced: mean residual **1.6653×10⁻¹⁶**, maximum/excursion residuals **0**, identical P99.9 bounds and gamut count. Tile layout changed only aggregation order, not policy settings.

## Frozen conditions and extent

| Condition | Measured | Frozen rule | Result |
|---|---:|---|---|
| Mean ΔE76 | 0.2782854788739307 | mean +0.01 ≤0.50 | PASS |
| P99.9 enclosing upper | 0.605, interval [0.604,0.605] | upper +0.01 ≤1.00 | PASS |
| Maximum ΔE76 | **3.016736865277825** | maximum +0.01 ≤2.00 | **FAIL** |
| Out-of-gamut pixels | **28,616 /35,431,818** | count ≤35,431 | PASS |
| Out-of-gamut fraction | 0.0008076356680314852 =0.0807635668% | ≤0.001 | PASS |
| Maximum normalized excursion | **0.038690466433763504** | ≤2/255 =0.00784313725490196 | **FAIL** |
| Reverse RGB maximum | 15 | Diagnostic only in v4 | Not the rejection gate |

There are **1,281 pixels (0.00361539%) with ΔE76 >1.99**, the effective maximum after the fixed 0.01 reserve. Of these, 1,257 exceed raw ΔE76 2.0; **one** exceeds 3.0 and reaches the maximum. There are **5,658 pixels (0.01596870%)** exceeding the excursion cap; **one** reaches the maximum excursion. The failure is concentrated, but not just one affected pixel. A rare maximum is still a failure under the frozen all-pixel rule.

All 1,281 maximum-condition failures are also out of gamut **and** above the excursion cap. All have an actual output channel clamped to zero; none has an output channel of 255. The 28,616 out-of-gamut pixels all have below-zero excursions; none exceeds the upper boundary. **Blue accounts for all above-epsilon gamut excursions**. R has zero excursion; the G maximum is only **1.9854×10⁻⁷**, below the unchanged reporting epsilon 10⁻⁶. Maximum negative blue excursion is −0.0386904664, approximately **9.866 destination eight-bit code levels below zero**, beyond the permitted two levels.

## Descriptive colour/spatial concentration — no anatomical inference

Categories were fixed for diagnosis, not clinical labels: source-profile D50 Lab lightness below20 /20–<80 /≥80; chroma C* below20 /20–<40 /≥40. Dominance is the uniquely largest managed-sRGB channel, not a dental/tissue classification. These three categorisations overlap and their counts must not be added together.

- All **1,281 ΔE failures** lie at **20≤L*<80**, **C*≥40**, and are red-dominant. There are zero such failures in L*<20 or L*≥80. All **5,658 severe excursions** are also mid-lightness/red-dominant; **5,657** have C*≥40 and one has20≤C*<40.
- Mild gamut flags differ: **19,910** are dark (L*<20);8,706 are mid-lightness. Therefore the large-error failure should not be described as the earlier image's predominantly dark quantisation pattern.
- ΔE failures occur in **9/551 tiles**; **1,167/1,281 (91.10%)** are in one tile and **99.14%** in the five highest-count tiles. The maximum local failed fraction is **1.7807%** of a tile.
- Severe excursions occur in **16/551 tiles**; **66.22%** are in the highest-count tile, **88.64%** in the five highest-count tiles. Maximum local fraction **5.7175%**.
- Any gamut flags occur in109/551 tiles. Thus mild numerical gamut excursions are more dispersed than the concentrated severe failures. Tile aggregates do not establish connected components, an anatomical location or clinical importance; no coordinates/per-tile maps were retained.

## Independent references and mechanism controls

The independent reference reads only functional ICC XYZ colourants and single-gamma TRCs into RAM. NumPy independently computes source matrix/TRC→XYZ→D50 Lab, destination inverse-matrix/extended sRGB transfer and actual output sRGB→Lab. Destination colourants come from directly generated sRGB, avoiding the previously documented serialized-profile precision mismatch. This independently checks equations/implementation **against the assigned profile**, not camera-profile truth.

| Cross-check over the complete image | Actual result |
|---|---:|
| Independent source Lab versus CMS, maximum ΔE residual | **0.0000237043** |
| Independent output Lab versus CMS, maximum ΔE residual | **0.0000223841** |
| Independent forward ΔE versus measured ΔE, maximum absolute residual | **0.0000315881** |
| Independent extended RGB versus CMS, maximum channel residual | **8.7492×10⁻⁸** |
| Independent out-of-gamut /severe /ΔE-failure counts | **28,616 /5,658 /1,281**, all identical |
| Existing C packed RGB versus actual Pillow forward output | **0 differing pixels**, maximum channel error0 |
| Source-profile→same-source-profile eight-bit identity control | Maximum channel error **0** |

These discrepancies are far too small to explain the observed policy overruns. Every measured transform value was finite. The same-profile/source identity and full C/Pillow agreement give no evidence of channel-layout, wrong-intent or malformed-transform defects.

Same-profile, same-intent **in-memory floating controls** separate representability from eight-bit encoding; they are diagnostics, not alternative production transforms:

- Leave extended sRGB **unclamped/unquantised**: maximum source-to-output Lab error **0.0000345051**; maximum floating inverse discrepancy **0.00931973 source-code-equivalent levels**. Numerical round-trip is close without bounding the destination.
- **Clamp to[0,1] but do not quantise to eight-bit**: maximum forward ΔE76 **2.98406331**; **1,319 pixels** exceed the effective1.99 limit. Therefore removing eight-bit rounding alone would not solve this source under this mapping.
- Among the actual1,281 failures, continuous clipping contributes mean ΔE **2.27460003**, maximum **2.98406331**; actual-versus-continuously-clipped encoding difference has mean **0.20777652**, maximum **0.47581865**. Their unclamped floating residual is at most **0.0000214949**. **1,234** of these actual failures also fail the continuous-clipping control. These distances are not additive causal percentages; rounding can raise or lower the final distance near a boundary.
- All in-gamut pixels have actual forward maximum **0.73561156**, below the frozen maximum condition. Actual maximum over the out-of-gamut subset is **3.01673687**.
- Independently clamp/nearest-round the floating output, then invert: maximum source-code-equivalent discrepancy **15.26665550**, consistent in magnitude with production reverse15. That control is **not bit-identical** to the optimized RGB8 production path: its maximum Lab difference from actual output is **1.27232375**. It is not substituted for production or asserted as an exact fixed-point oracle. The exact C/Pillow production comparison and separate analytic reference above are the stronger implementation checks.

**Conclusion:** clipping is established as the primary mechanism of the large errors, with encoding/quantisation contributing. This is a real bounded-destination loss in the **current** relative-colourimetric conversion, not just a misleading reverse-RGB error or floating-precision artefact. It does **not** prove that no alternative sRGB gamut mapping could reduce the error; alternative mappings or minimum-achievable-error searches were neither authorized nor performed.

## Uncertainty and safe options — neither implemented

Actual acquisition calibration, lighting and whether the assigned source ICC accurately represents photographed colours are unverified. No clinical tolerance, observer judgment or diagnostic-information preservation was measured. Concentrated numerical clipping does not establish clinical harm, and rarity does not establish acceptability. Current safeguards correctly stop; original/profile bytes must not be edited to make this case pass.

| Proposed separately authorized next step | Trade-off |
|---|---|
| **A. Generated-image-only feasibility study of an explicitly specified gamut-mapping approach under unchanged frozen error budgets.** Use independent standard-profile fixtures, not failed-image-derived thresholds; make no production/real-image changes. | Could retain the sRGB model interface, but changes colour rendering and may still be unable to meet all budgets. Requires a new documented method, regression evidence and approval before any activation. |
| **B. Plan a metadata-safe canonical/wider-gamut RGB representation with consistent colour-aware preprocessing and CAM/display handling.** | Avoids treating simple profile stripping as colour preservation, but is not a drop-in fix; requires privacy/profile validation, loader/runtime/protocol work and does not guarantee whole-cohort feasibility. |

**ONE recommended next action:** separately authorize **Option A's generated-image-only feasibility study**, keeping current production settings, frozen budgets, failed attempt and all data/approval gates untouched. No packaging retry is recommended at this stage.

Aggregate evidence: `data/vision/colour_diagnostic_00004_v1_20261015/aggregate.json`. It contains only source ID/hash, safe profile characteristics, numerical/region/tile summaries, runtime and preservation checks. Existing task/AI logs were deliberately not appended because this request permits only a new report and aggregate log.

Teaching: (1) all1,281 severe ΔE pixels also being out of gamut links the failure to clipping; (2) continuous-clamp failure proves rounding alone is not the explanation; (3) independent-equation/CMS agreement supports the implementation without proving clinical fidelity. Viva: **Does a tiny affected fraction mean we can ignore the maximum?** இல்லை. Frozen policy ஒவ்வொரு pixel-க்கும் maximum/severity limit விதிக்கிறது; அதை மீறினால், average pass ஆனாலும் package நிற்க வேண்டும்.
