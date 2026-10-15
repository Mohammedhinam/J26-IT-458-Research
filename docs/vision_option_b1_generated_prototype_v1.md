# B1 generated-only colour/input prototype v1

2026-10-15 · branch vinuthan. Owner authorised generated-only prototyping. No real-data permission, exporter integration or research approval. Option A remains unchanged/failed. Results will be recorded after focused execution below.

## Contract frozen before implementation

- **Colour:** IEC sRGB primaries (R .64/.33, G .30/.60, B .15/.06), D65 reference white; relative-colorimetric D50 ICC PCS. Canonical D50 matrix is the full-precision LittleCMS generated-sRGB matrix already independently used by the prior study, pinned as literal constants in the prototype. No repeated adaptation: source matrix colourants are already D50-adapted.
- **Extension:** explicitly choose an odd/symmetric extended transfer: `E(L)=12.92*L` when `abs(L)<=.0031308`; otherwise `sign(L)*(1.055*abs(L)**(1/2.4)-.055)`. Inverse threshold .04045. This defines B1's negative encoding; it is NOT an assumption about Pillow/LCMS negative encoding. The standard rounded sRGB breakpoints have a tiny discontinuity; inverse error allowance is declared below. Negative and >1 values are retained. RGB8 CMS output is never used as canonical extended data.
- **Support:** generated RGB8 arrays only, max256×256; required embedded matrix/TRC ICC v4 `mntr`, RGB→XYZ D50. Support gamma parametric type0 and monotonic sRGB-shaped type3 only, plus validated matrix/white/chad tags. Reject LUT, other tag/curve/class types, malformed/overlapping tags, non-finite/unstable matrices and absent/ambiguous profiles. No real-image/path ingestion entry point. The limited prototype proves no arbitrary camera profile support.
- **Numerics:** float64 matrix/TRC arithmetic. Independent scalar reference max component error <=1e-10; independent LCMS source-Lab comparison <=.01 DeltaE76 (existing generated-reference engineering tolerance). Float32 storage error <=half an adjacent float32 step +1e-14; recovered linear XYZ max absolute error <=2e-6 and reconstructed D50 Lab max error <=.002 on the generated qualification fixtures. Extended-transfer inverse error <=5e-9, accounting for rounded breakpoints. These are numerical checks, not clinical thresholds and not replacements for frozen Option A budgets.
- **Range/resources:** generated source uint8 RGB only; canonical float channels finite in [-16,16]. This broad, prospective arithmetic envelope bounds storage/normalization; it grants no real-source acceptance. Reject outside, never clip. Fixed model views224×224×3, original generated views bounded256×256. Real full-resolution/memory-mapped support is future qualification.
- **Geometry:** aspect-preserving fit to224; Python round-to-even dimension rounding, minimum1. Centre letterbox, extra odd pixel on bottom/right; ImageNet mean padding. Half-pixel bilinear sampling with edge replication, float64 sums then float32; no antialiasing, hidden clipping or Lanczos overshoot. This differs from historical uint8 Lanczos and requires later model/protocol validation. Store inverse valid box/original dimensions.
- **Storage/security:** NPY v1 only, `<f4`, HWC, C order, exactly three header fields and exactly one array with no trailing bytes; header<=512 bytes, bounded dimensions/payload. Bytes-only loader: no filesystem paths, object/structured dtype, pickle, arbitrary metadata or links. SHA-256 binds trusted receipt, payload, contract, source RGB bytes, original in-memory profile hash and geometry. Receipt hash is trusted out-of-band; hashes are integrity bindings, not approval/authentication. Source ICC/EXIF are not copied.
- **Model:** use `(extended_rgb-MEAN)/STD` directly, CHW float32; no `/255`, uint8 conversion, clipping or per-image scaling. Existing model factories, five-output MGI schema and Grad-CAM math remain unchanged. The adapter gives existing rendering an explicitly separate display preview, while model input stays extended float.
- **Display:** canonical extended sRGB → explicit [0,1] clipping → round-even RGB8 preview; preview is display-only, not training input. State “unoverlaid display preview; gamut conversion may lose colour”. Numeric preview assumes an sRGB-aware display; no monitor calibration/clinical equivalence claim. Record clipped-pixel count; never call preview colour-identical original. Original generated geometry is retained for CAM alignment.
- **Isolation:** no production imports are changed, no packaging/authorization fallback, no labels/cohort/splits/manifests touched. Generic arithmetic accepts caller-owned generated arrays only; top-level smoke uses fixed generated fixtures. Code cannot authenticate pixel origin, so real use remains prohibited by scope and absent production integration.

## Verification results

**PASS for generated colour/storage/model-input preprocessing; actual ResNet-50 backend verification remains pending.** Focused final run: **75 passed, 0 failed, 0 errors, 2 skipped**, 77 selected cases, 0.31s. Both skips are explicit torch-unavailable cases: ResNet-50 five-logit forward and frozen-backbone class-Grad-CAM/hook/alignment compatibility. Historical 59 Colab checks do not verify this new B1 adapter.

Runtime: Python3.12.14, NumPy2.3.5, Pillow12.3.0, LCMS2.19, pytest9.1.1. No torch/torchvision installed; none installed/downloaded for this task. Existing pytest was reused with plugin autoload disabled, cache disabled and Python bytecode writes disabled.

| Generated measurement | Actual result |
|---|---:|
| Independent scalar matrix/TRC float64 max RGB residual, ten generated profiles | 7.255209887729874e-16 |
| Float32 reconstruction max absolute XYZ error across those fixtures | 9.342544449175705e-8 |
| Float32 reconstruction max D50 DeltaE76 across those fixtures | 6.058465224057274e-6 |
| Red/blue primary stress canonical min / max | -0.13156165182590485 / 1.006840467453003 |
| After NPY encode/load min / max | -0.13156165182590485 / 1.006840467453003 |
| Normalized CHW min / max | -2.6915693283081055 / 2.6704020500183105 |
| Generated 224-square NPY bytes, including header | 602240 |

The primary fixture contains **negative red and negative blue**, not only dark in-gamut values. Independent references use scalar summation/linear solve, generated fixed-point ICC matrices/TRCs and separately queried LCMS canonical colourants; ten source-Lab comparisons against LCMS pass the predeclared .01 bound. Float32 errors satisfy independent half-ULP rounding tests. No RGB8 CMS output is mistaken for extended float output. The odd negative transfer is intentionally explicit; it need not match LCMS's negative encoded branch.

Security/failure coverage: non-finite/out-of-range values, unsupported/malformed ICC headers/matrices/curves/adaptation, bounds/no source-path decoding, exact letterbox and half-pixel interpolation, finite five-schema adapter geometry, display-only clipping disclosures, immutable loaded arrays, source/profile/contract/payload/receipt hashes, stale/tampered receipts, unknown metadata, object/structured/big-endian/Fortran NPY, duplicate/extra header fields, missing newline/alignment, bad versions, giant/truncated headers and trailing bytes. Fixed smoke passes with filesystem/image open/save and production packaging functions patched to fail. Existing Option A spec, legacy limit2 and seven production source hashes remain unchanged; approved-training gate still rejects unapproved metadata.

Integrity evidence:

- Contract SHA256: `bc5e3dde1dfc0baed568ab428bcc73c16c2af50270d85ec34402626a268a313b`.
- Prototype source SHA256: `d3108ea3bf7f310f1b46960174d4936299ece19d762f4ca1ee9d900572b90856`.
- Focused test SHA256: `db9fb9307b6453f0252ff9d1aef6c2541ca1ec829930e8f803818af122f63e85`.
- Fixed generated payload SHA256: `854f973b52e4bc05cfacc1be9fdd23f22b55c5ca42a4e767c7f6cc8add8c1b91`.
- Fixed generated receipt SHA256: `cd96ddc0eaf6481f9dffaa12b48ba2c67257babd69a30f51db03d06941980a8e`.
- Local transient JUnit: `/tmp/rp_b1_generated_v1_tests.xml`; aggregate numerical evidence: `/tmp/rp_b1_generated_verification_v1.json`. This report is the durable factual record; /tmp persistence is not guaranteed. Source hashes describe this run, not a signed authorization.

## Remaining blockers and one next action

1. Execute the **two new B1 ResNet-50 tests** in an already available compatible runtime using `weights=None`, generated inputs only. Existing earlier Colab passes cannot substitute. No code-only Colab package is created or cloud action performed in this task.
2. Before 733-image packaging: qualify a separately versioned full-resolution/tiled float converter/NPY verifier and approve its prospective precision/range/display contract, real profile support and memory bounds. This small generated prototype intentionally rejects >256-side inputs and provides no real-data ingestion/export gate. It must not be pointed at the dental dataset. No assurance that every real source ICC fits its narrow matrix/TRC subset.
3. Integrate B1 only into an explicitly isolated exploratory pathway with all733 membership,181 holds, NP015/content groups, Test isolation, privacy/attribution and fresh source/code/DRAFT/policy/output hash bindings. None of these protections is implemented anew or bypassed here; production code is untouched. Separate owner local packaging authorization is still necessary, then separate cloud/weight/pilot permissions. No automatic replay of consumed Option A authorization.

Missing image-level MGI0, scarce MGI1, provisional labels and unverified participant independence remain. Same five definitions and independent questionnaire architecture; no clinical colour validity, model performance or final label approval follows from these numerical tests. A valid-but-wrong ICC can produce coherent but wrong colours; arithmetic cannot authenticate camera provenance. Bilinear without antialiasing and extended ImageNet-normalized inputs still need empirical exploratory evaluation under an approved protocol. Preview clipping remains a known display limitation.

**ONE next action:** prepare/execute a code-only generated B1 runtime verification in compatible Colab for the two pending ResNet-50 tests, with source hashes and `weights=None`; obtain separate cloud execution scope before doing so. Do not package real images next.

Teaching: `encode_extended()` preserves the sign/range rather than losing it to RGB8. `load_generated_payload()` verifies the trusted receipt and bounded NPY structure before loading; hashes are not clinical approval. `normalize()` passes extended floats directly to the model and keeps display previews separate. Viva: **Does a five-logit forward pass prove five-grade accuracy?** இல்லை; அது software compatibility மட்டும். Real approved labels, class support, independent evaluation இல்லாமல் accuracy சொல்ல முடியாது.
