# B1 generated-only full-resolution qualification v2

2026-10-15 · vinuthan · Generated-only engineering scope. No real image/profile/dataset access, packaging, activation or training authorised. Preserve frozen B1 v1 and Option A exactly.

## Prospective qualification contract (before implementation)

- Same v1 primaries, D50 matrix/TRC interpretation, odd extended transfer, `<f4` HWC/C-order NPY v1, finite[-16,16] bounds, half-pixel bilinear/round-even letterbox, ImageNet normalization and separate disclosed display interpretation. Same numerical maxima: XYZ2e-6 and reconstructed Lab DeltaE76 .002; independent float64 reference1e-10, float32 half-ULP+1e-14. These are numerical engineering checks, not clinical tolerances.
- New explicit `b1-generated-full-v2` schema; no v1/A fallback. Generated-source descriptor only: fixed patterns/profiles, width/height≤16384 and total≤40000000 pixels (480MB float payload). No source path, image decoder, real ICC input or training loader. Limits bound this prototype, not cohort acceptance or a permission to ingest dental data.
- Sequential row-major source/float chunks≤65536 pixels (reshape≤256×256); call unchanged qualified v1 conversion on each chunk. Incremental real RGB-byte and NPY hashes; no full array/memmap/byte-string allocation. Retain full-resolution canonical NPY as generated CAM data; source geometry stays unchanged.
- Model224 is sampled from verified float32 canonical data with exactly the frozen half-pixel arithmetic and mean padding. Same original size/inverse valid box. Full-resolution data remain canonical; display preview can clip and never becomes model data.
- Strict versioned header/length/dtype/shape/finite/range/hash checking in streaming equivalent of the v1 bounded loader. The original bytes-only v1 loader cannot accept larger geometry and is not modified. All model arrays pass its existing array/normalization checks. New format carries no ICC/EXIF/GPS/XMP/MakerNote or arbitrary metadata.
- New output directory only, private permissions, exclusive regular files, no symlinks/overwrite, receipt digest trusted externally. Verify hashes/streamed values and same-file identity before sampling. Final receipt written only after verification. Fail leaves an incomplete generated output, no success receipt. No approval claims or dataset labels in receipts.
- Required evidence: independent generated matrix/TRC references; v1 bitwise equivalence at small sizes; independent larger-geometry samples; negative/above-one persistence; finite/precision failures; deterministic bytes; corruption, headers, metadata and hash tampering; source/Option A preservation; full-resolution geometry. Fresh-worker peak RSS for1024×768 and4096×3072 generated cases, measured not inferred. Prospective absolute RSS ceiling512MiB for these two engineering stress cases; no claim about real-image decoder RAM or full cohort runtime.

## Results

**PASS — generated-only full-resolution engineering qualification at the tested sizes. Not ready for real733-image packaging.** New focused suite: **57 passed,0 failed/errors/skipped**,0.73s. Earlier77-case Colab suite was not rerun.

| Check | Verified evidence |
|---|---|
| Existing Colab milestone | Actual supplied ZIP SHA256 `5e9b8f6e1e35f370455fc90250bd1fe2d8bcf5d7afa14317d487a218ddb06845`,7759bytes,CRC valid;77 unique JUnit cases agree with collection/log,0 failures/errors/skips. Forward .872s,Grad-CAM1.080s; total77 passed3.02s. |
| Colab integrity/runtime | Ten evidence payload hashes valid;11/11 source/test hashes equal before/after,current source and code ZIP manifest. Eight project imports isolated. Python3.13.16,torch2.11.0+cpu,torchvision0.26.0+cpu,NumPy2.1.3,Pillow11.3.0,pytest8.4.2,LCMS2.17. Weights=None,RUN_PILOT=false,no dental training. Owner executed; saved evidence verified here. |
| Full canonical stress precision | XYZ max8.3300942588e-8; reconstructed Lab max DeltaE76 5.3569252728e-6. All inherited engineering tolerances unchanged. |
| Full canonical values | -0.1315616518 to1.0068404675 survived stored NPY and streaming verifier. On the12.58MP mixed fixture:634433 negative samples,317217 above-one samples. |
| Model geometry | Deterministic224×224, valid box[0,28,224,168] for4:3 stress sources. Exact v1 bitwise model/normalization equivalence across12 small generated pattern/profile combinations; independent large-image sample/reference check passes. Full NPY shape matches original H,W,3 for future CAM data. |
| Model range nuance | Dedicated primary fixtures retain negative AND above-one model values. Mixed stress resizing averages peaks: its model max .8750, not a clipping failure; source negatives and above-one remain in full data. |
| Failure/security | Corrupt/trailing/truncated NPY,wrong dtype/endian/order,extra metadata,stale hashes/contracts,NaN/range/precision faults,wrong model content,symlinks,overwrite and malformed/duplicate/nested receipt keys rejected. Same-FD identity binds hash scan to sampling/reread; simulated mutations rejected. |

Frozen v1 mathematics/loader/adapter and Option A/trainer/exporter source bytes were preserved. New verifier uses equivalent strict NPY header rules but streams larger arrays; original v1 loader's256-side boundary is unchanged. Tests prove no PIL decoder/save,np.load(full),memmap or production packaging call occurs. Final receipt is written only after real file checks; incomplete generated outputs are not successful artifacts. Output paths remain mutable: reverify on every later consumption, not once forever. Hashes require an externally trusted receipt digest and do not grant approval.

### Measured memory, separate fresh CPU processes

| Generated dimensions | Full float payload | Post-import baseline peak | Whole-process peak | Peak increment | Wall time |
|---|---:|---:|---:|---:|---:|
|1024×768|9MiB|37.109375MiB|55.546875MiB|18.4375MiB|0.1208s|
|4096×3072|144MiB|36.953125MiB|57.046875MiB|20.09375MiB|1.6348s|

Actual large-case peak: **59,817,984 bytes**. Both pass the prospectively declared512MiB stress ceiling. Measurements use `resource.ru_maxrss`, macOS bytes (Linux branch converts KiB), include Python/imports, conversion, streaming verification and model-view construction. Baseline is the **post-import high-water mark**, not instantaneous RSS. These are local one-run CPU measurements, not benchmarks for all hardware, decoded real JPEGs or733-image runtime. A16× output-payload increase raised observed peak by1.5MiB; allocator/OS variability still exists. Each conversion chunk≤65536pixels; model sampling holds at most two rows. Synthetic scratch outputs were removed only after aggregate evidence was retained. No full-resolution memmap or full-array allocation.

Local runtime: Python3.12.14,NumPy2.3.5,Pillow12.3.0. Full machine/runtime,source hashes,exact byte measurements and array hashes are saved in [qualification evidence](vision_b1_full_resolution_evidence_v2.json). Verified prior Colab ZIP is preserved byte-identically as `docs/vision_b1_runtime_evidence_v1.zip`; original remains in Downloads. Transient new-suite JUnit `/tmp/rp_b1_streaming_v2_tests.xml`. New contract SHA256: `5396d9aa77989dedba702e28ba1fa1ee3970d073da1b226bb6a35c3b1855d761`.

## Files and remaining gates

New code: `src/vision/colour_b1_streaming.py`, `src/vision/measure_b1_streaming.py`; new tests: `tests/test_colour_b1_streaming.py`. New report/evidence JSON and byte-identical supplied Colab evidence copy; current handoff and append-only diary/AI log updated. Existing tests,code,earlier reports,source datasets,policies and approval gates preserved. No new code ZIP/cloud workflow is needed to record the earlier Colab result.

| Before a real local packaging attempt | Status / required authority |
|---|---|
| Generated full-resolution numerical/storage proof | PASS at the tested12.58MP maximum. Configured40MP/16384-side limits are bounds, not a claim of stress-testing every allowed geometry or real source. |
| Real ICC/decoder/orientation/colour provenance support | **Unverified.** Current interface accepts fixed generated recipes only. No real ICC was inspected; support for the actual cohort cannot be inferred. Reconcile cached evidence first; any real read/decode needs separate permission. |
| Explicit B1 exploratory exporter and verifier | **Not integrated/activated.** Need separately versioned source-hash,metadata/orientation,geometry,attribution,disk/memory and full-CAM/display handling; preserve733 selection,181 holds,NP015,duplicate groups and Test isolation. No new manifest or approval is created here. |
| Owner decision for actual B1 representation/export contract | **Pending for real use.** Generated-only approval does not approve extended model inputs/visible preview losses for a real pilot or replace failed A limits. Approve the B1 contract/version and fresh source/code/DRAFT/policy/output bindings separately. |
| Local packaging/cloud/training permissions | **Absent.** A separate single-use real packaging decision is needed only after integration qualification; cloud/weights/pilot require their own scopes. Zero qualified-approved final labels; missing image-levelMGI0/scarceMGI1 and participant uncertainty remain. |

**ONE next action:** separately authorise **generated-only B1 exploratory exporter/authorization integration**, including the unchanged733/181/NP015/group/Test protections and source/metadata/CAM interface checks. Do not authorise or run a real packaging attempt yet. No frozen limit has been widened and no scientific approval is fabricated.

Teaching: `_chunks()` presents row-major pixels in bounded blocks; unchanged v1 conversion remains the colour authority. `_inspect()` verifies file bytes/finite values without loading the image. `_model_view()` samples verified float32 data with the same resize arithmetic. Viva: **Does low RAM prove clinical colour fidelity?** இல்லை—இது generated software resource evidence மட்டும்; real-source interpretation, clinical truth மற்றும் model evaluation தனி வேலை.
