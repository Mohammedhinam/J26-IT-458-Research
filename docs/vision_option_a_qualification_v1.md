# Option A — isolated synthetic qualification v1

2026-10-15; branch **vinuthan**. Owner authorized **generated-image qualification and isolated implementation only**. **71 passed, 0 failed, 0 errors, 0 skipped in 0.74 s.** No production activation, dental image/header access, real export/package/upload, model operation, Test payload access, installation/download, commit or push. No prior dataset audit, Colab workflow, completed helper suite or real Training/00001 diagnosis repeated.

## Implementation and frozen scope

New pure-Python `src/vision/colour_policy.py` provides `evaluate_option_a(measurements, evidence=None)`. It consumes the existing tiled colour-QA aggregate schema; it does not open files/images, invoke QA itself, export, package, approve labels or call training. New `tests/test_colour_policy.py` provides the focused qualification. Existing helper/exporter/model/trainer/tests and historical reports remain byte-identical; only new code/tests/report and append-only diary/AI log are task changes.

Policy ID: `pp1-option-a-isolated-v1-20261015`. Frozen checks are **all ANDed**:

- Mean ΔE76 +0.01 ≤0.50; nearest-rank P99.9 **enclosing upper bound** +0.01 ≤1.00; maximum +0.01 ≤2.00.
- Gamut count `C ≤ N//1000`; exact fraction `1000*C ≤ N`; maximum normalized sRGB excursion ≤`2/255`. Count uses the existing epsilon `1e-6`; no new exception or epsilon is added to the budgets.
- Geometry/coverage/settings/finite summary checks must pass. Missing, unsupported, inconsistent or non-finite measurements return no passing conditions; no private input values are echoed.
- Mandatory caller-verified prerequisites must all be explicitly true, have nonempty evidence references and be bound to the exact QA JSON SHA-256. Required names: source hash, unchanged source, geometry, metadata allowlist, supported profile, runtime reference qualification, development-only scope, holds excluded, NP015 excluded, content-group isolation, Test isolation, owner scope, unchanged labels/splits.

**Important trust boundary:** the evaluator checks completeness, status and digest binding of supplied evidence, not the truth of caller assertions. It does not audit the 733-source plan or certify 181 holds from a boolean. Future production integration must run the actual existing guards and generate references from their results. Test references are explicitly `generated-test-only:*`, not real owner/clinical approvals.

Output separates `isolated_policy_pass` from fixed false values `production_policy_active`, `export_authorized`, and `clinical_approved`. A passing output is rejected if misused as the existing packaging authorization record. There is no default passing evidence and no export hook.

## Exact boundaries and logical constraints

Forward checks compare decimal representations directly with the algebraically equivalent effective limits **0.49, 0.99, 1.99**. This avoids binary `value+0.01` rounding the immediate next float above a boundary back onto it. Tests independently evaluate the original nominal-budget expression in Decimal and check below/equal/above cases. Tail decisions use the enclosing upper bound, never a midpoint/lower edge.

For nonnegative integer `C,N`, `C ≤ floor(N/1000)` and `C/N ≤0.001` are mathematically equivalent. Both are evaluated and reported, but an honestly consistent case cannot fail exactly one of them. Tests require the two extent checks to fail together; this is redundancy in the frozen policy, not a budget conflict. Mean, tail, maximum and excursion each have separate single-failure tests.

Reported gamut percentages must agree with counts within a serialization-consistency check (`1e-12` absolute/relative in percentage units); **policy fraction acceptance never uses that tolerance**, only exact integer arithmetic. The severity test compares against the frozen float expression `2/255`; its immediately adjacent float above fails. No limit was selected/adjusted using Training/00001.

## Independent generated-fixture evidence

New fixtures use 10,000 generated RGB pixels with one analytically specified saturated-green spot and an otherwise neutral background. Source ICC matrices are expanded using fixed binary strengths, quantized to ICC fixed-point precision, and use an explicit linear TRC. NumPy independently calculates source matrix/TRC→XYZ→destination inverse matrix/transfer equations and D50 Lab comparisons. No real photo, clinical annotation or Test statistic is used.

The independent gamut calculation reads functional colourants from the **directly generated destination profile**, not a serialized approximation; it does not call a CMS pixel transform for the expected answer. The first reference version used serialized destination matrix values and had ~0.0002 excursion disagreement. The reference input was corrected to match the helper's generated destination; **budgets and production code were not changed**. Across the final six-point grid, maximum measured/reference excursion discrepancy is **7.538570657×10⁻⁹**, within the predefined reporting epsilon. The generated reference assertion was tightened from the older fixture allowance 0.002 to **1e-6**; it was not loosened to pass.

| Generated matrix expansion | Gamut pixels / N | Max excursion | Max forward ΔE76 | Isolated result |
|---|---:|---:|---:|---|
| `2^-14` | 1 / 10,000 | 0.000421539 | 0.056641140 | Pass |
| `2^-12` | 1 / 10,000 | 0.003049094 | 0.056641140 | Pass |
| `2^-11` | 1 / 10,000 | 0.006411032 | 0.060601308 | Pass |
| `2^-10` | 1 / 10,000 | 0.012323549 | 0.118301299 | Reject: excursion only |
| `2^-9` | 1 / 10,000 | 0.025259003 | 0.238445921 | Reject: excursion only |
| `0.1` | 1 / 10,000 | 1.291863441 | 11.990539534 | Reject: maximum ΔE and excursion |

The independent analytic oracle gives the same pass/fail classifications. Source-Lab/output-Lab reference agreement retains the independently defined **0.01 ΔE fixture precision allowance**, not a clinical tolerance. A weak-expansion fixture with **11 spots/10,000** fails **both extent checks**, despite low severity/colour difference. A wrong-profile fixture is rejected. A generated quantisation-only shadow ramp passes the isolated composite while the **unchanged exporter still rejects its reverse error >2 before file creation**. It cannot use the isolated verdict as permission.

The initial 69-case suite passed (0.72 s), followed by an unchanged-logic confirmation (0.67 s). Matching the independent reference's destination matrix and adding two binary-grid fixtures gave the final **71/71** run (0.74 s). No failed test result is hidden; no frozen-budget conflict was found on these fixtures. Exact numeric boundary tests use known synthetic measurement distributions; they are distinguished from the six actual generated-ICC/image tests above.

Other focused checks: all 13 mandatory prerequisites, missing/empty/truthy evidence, stale measurement binding, NaN/±Inf in forward/tail/gamut/reverse evidence, partial pixel coverage, altered geometry/settings, boolean counts, inconsistent count/percentage/severity, missing tail, exact excursion/epsilon boundaries, N<1000 cases, deterministic/no-write behaviour and source bytes/metadata preservation. Existing complete suites are not included in the count. The 71 result is **not** a full repository test run or new Colab result.

Runtime: existing CPU Python **3.12.14**, Pillow **12.3.0**, NumPy **2.3.5**, pytest **9.1.1**, LittleCMS **2.19**. The existing pytest package was imported after bundled dependencies; nothing installed. Ignored evidence folder: `data/vision/option_a_qualification_v1_20261015/` with stage logs/JUnit XML, `qualification_verified.json`, `generated_grid_qualified.json` and preservation verification. Earlier four-point aggregates remain historical; final six-point, matching-destination evidence is authoritative.

## Production preservation and remaining requirements

`exploratory_bundle.py`, `colour_qa.py`, model/trainer/pilot, existing tests, code-only bundles, frozen manifests and old approval records were not edited. `ROUNDTRIP_LIMIT=2`, the v3 manifest verifier and real packaging authorization gate remain active. No data/label/split status is cleared and no real prerequisite/clinical approval is manufactured. Preservation is verified against the starting tracked/untracked file hashes and original log prefixes.

Before safe real packaging, a **separately authorized production-integration task** must explicitly:

1. Integrate the composite into the actual pre-write export and post-write verification path under a new version/policy ID. Keep reverse statistics but replace their hard-stop role only in that authorized version; no catch-and-continue fallback, automatic old/new policy selection or per-image exception.
2. Generate prerequisite evidence from the real unchanged source hash, metadata, geometry, runtime, owner, held/NP015/content/Test-isolation checks; bind QA/policy/source/export hashes to the manifest. Caller assertions in this isolated prototype are insufficient as production proof.
3. Add scoped generated integration tests proving both export and verifier enforce every frozen condition, tampered/stale/old authorizations fail, invalid outputs cannot become packages, and no protected data or clinical approval enters the pathway. Refresh code-only verification artifacts/source bindings as needed; do not infer Colab portability from this Mac run.
4. Preserve provisional/non-clinical/non-final wording, participant-independence warning, CC BY attribution, metadata allowlist, source files, fixed cohort and final research-training gate. No actual export is authorized by integration alone.

After that verification, a **fresh explicit packaging-only owner decision**, actual current code/policy/source hash bindings and fresh output ID are required. Upload, weights, training and final research approvals remain separate. No fresh readiness claim is made for Training/00001 or the other 732 sources.

Numerical correctness on these fixtures does not establish clinical colour fidelity. A small clipped region can matter despite global count/ΔE bounds; source profile accuracy, camera lighting, display calibration, labels and participant independence remain unresolved. The frozen budgets are transparent exploratory engineering choices, not medical safety limits or universal guarantees. The code's pass only means the supplied valid measurements/evidence satisfy that isolated rule.

**ONE next action:** owner authorization for the narrowly scoped **production integration and generated integration verification**, still excluding real packaging/export/upload/training.

## Teaching notes

1. Decimal effective-limit checks: boundary-க்கு சற்று மேலே இருக்கும் value rounding காரணமாக pass ஆகாமல் தடுக்கிறது; output தனித்தனி criterion results.
2. `c*1000 <= n`: displayed percentage-ஐ round செய்யாமல் extent limit-ஐ exact-ஆகச் சோதிக்கிறது; count/fraction முடிவுகள் ஒன்றாக இருக்கும்.
3. `export_authorized=False`: isolated pass இருந்தாலும் உண்மையான packaging permission கிடையாது; பழைய guard இன்னும் தடுக்கிறது.

Viva: **Does 71 passed mean dental colours are clinically validated?** இல்லை. Generated cases-ல் frozen engineering rule சரியாகச் செயல்படுவதைத்தான் காட்டுகிறது; real-image export, clinical correctness அல்லது model accuracy நிரூபிக்கவில்லை.
