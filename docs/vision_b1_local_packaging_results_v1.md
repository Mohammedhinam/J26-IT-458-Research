# B1 local packaging and four-grade exploratory handoff v1

2026-10-15 · branch `vinuthan`.

**Local package PASS. Four-grade Colab handoff prepared; new PyTorch runtime verification and actual dental training remain pending.**

Owner authorised local engineering, read-only diagnosis of the pinned733 sources, a separate MGI1–4 exploratory configuration, and ONE conditional local packaging attempt. Conditions were met before that attempt. No clinical, institutional, final-research, cloud, weight-download or dental-training approval was created.

## Verified local results

| Check | Actual result |
|---|---|
| New B1 real-source structural compatibility | **733 compatible /0 incompatible /0 unknown** under the new explicit pathway; original parser's historical0/733 report preserved |
| Source SHA and JPEG/ICC headers |733/733 current matches; RGB8, orientation1, cached geometry; same qualified profile family, including Training/00004 |
| Full generated RGB8 domain using the real embedded profile, in memory |16,777,216 combinations checked; no raw ICC saved |
| Max LittleCMS relative-D50 source-Lab difference |0.000027880253137618567 ΔE76, limit0.01 |
| Float32 max XYZ reconstruction error |1.0266460404029232e-7, limit2e-6 |
| Float32 max Lab reconstruction error |0.000014583714298036063 ΔE76, limit0.002 |
| Complete profile-domain extended RGB range |-0.6639457941055298 to1.1581836938858032; not a measured per-image range |
| Real read-only decoder probe |Training/00004 decoded and model geometry checked; no derivative saved during preflight |
| Authorized actual package |680 Training +53 Validation model arrays; three full-resolution CAM arrays; **733 distinct sources,737 files including manifest** |
| Held/uncertain/Test safeguards |181 holds unchanged/excluded; NP015/protected/uncertain/multi-image groups excluded; no Test image/label payload accessed |
| Source preservation |All733 original source hashes verified before and after actual export |
| Independent post-export verifier |Separate Python process PASS, compared with internal verification |
| ZIP checks |Exact membership, streamed payload hashes and CRC checked before publication |
| Real packaging elapsed / peak RSS |104.57531945899245 seconds /206.171875 MiB (Darwin resource high-water measurement) |

The exhaustive cube is a bounded generated-code numerical proof for a byte-identical ICC and RGB8 interpretation, not a repeat of the prior generated18-profile qualification or a new image audit. Every actual NPY additionally passed finite/range/geometry/hash checks; full CAM/model sampling matches. No out-of-gamut clipping is applied to model/CAM floats. Display-only previews still clip and are explicitly disclosed. Profile arithmetic does not prove camera truth or clinical colour fidelity.

A final metadata-only binding change replaced the absolute output path with its SHA, followed by directly affected generated integration verification and a freshly bound focused real preflight before the one attempt. Earlier preflight evidence was preserved. Option A budgets/failed attempts, original B1 APIs, original five-class models/trainer, DRAFT and datasets remain unchanged.

## Exact successful artifact

- Local ZIP: `/Users/vinuthanvinuthan/Desktop/RP-J26-IT-458/data/vision/pp1_b1_dev_v1_20261015T085436527238Z.zip`
- Size: **732575501 bytes** (698.638440 MiB).
- ZIP SHA256: `a8a4f7f339c589f81335d7afb663f4cf62d30e217f65bc480683d0a770afed70`.
- Manifest SHA256: `8e7ff195009a5e781c216795fd2a943db17a0b3ec8fd1c84760f3bf9878a4c9f`.
- Source plan digest: `7f7600b03ab209995324b53926bc283e6194bd65c381db73ecb5920958bcbf59`.
- B1 export contract digest: `81c5f2179ab3827fdf543a140fa4e616a8031e76aa02882c573c5100d3e438ef`.
- Full arrays: Validation/00733,00734,00766 only.
- Ignored attempt/provenance/independent verification: `/Users/vinuthanvinuthan/Desktop/RP-J26-IT-458/data/vision/b1_local_attempt_v1_20261015T085436527238Z/`.
- Final preflight: `/Users/vinuthanvinuthan/Desktop/RP-J26-IT-458/data/vision/b1_real_preflight_final_v1_20261015T085234884382Z/`.

No real retries occurred. Training/00004 and other difficult sources were retained. No source JPG, captions, TXT, private EXIF/GPS/ICC bytes, patient identifiers or held/Test records enter the package. The allowlisted manifest contains source IDs/hashes/provisional grades/groups, qualification aggregates and attribution. Metadata removal does not establish anonymous oral-image content; the package remains local-only.

Attribution: Duy Hoang Bao, dataset v1, DOI10.17632/3253gj88rr.1, CC BY4.0 and licence/source URLs retained with explicit transformation/no-endorsement notice. Existing local-use requirements and the new owner scope were reviewed; no local-only restriction was found in reviewed project evidence. No institutional/clinical approval or external-sharing entitlement is inferred.

## Separate MGI1–4 pilot

Original research remains five definitions/logits0–4. The owner's explicit new decision authorises a separately versioned four-logit exploratory instance, target indices0..3 mapping only to **original grades1..4**; source labels are never changed. This is not the signed final five-class comparison.

| Original grade | Provisional Training | Provisional Validation |
|---|---:|---:|
|1|12|1|
|2|84|13|
|3|223|22|
|4|361|17|

Bounded protocol: ResNet50, documented ImageNet1K_V2 checkpoint, frozen backbone/BatchNorm, seed42, batch16, Adam learning rate0.001, max5epochs/patience2, no augmentation for this initial head-only pilot; early stop on four-grade Validation macro-F1. Same independent datasets/known groups/NP015 holds and frozen original membership. No Test use. Best/last checkpoints are saved and best provenance checked; this new bounded pilot does not implement mid-run resume or automatic reruns.

Report actual Validation macro-F1, per-grade F1/recall/support, confusion, ordinal MAE, QWK, per-grade/macro AUROC and multiclass Brier, plus the training-derived majority baseline. Majority is grade4; its deterministic provisional Validation accuracy0.32075471698113206 and four-grade macro-F1 0.12142857142857143 are **baseline calculations**, not a trained neural result. MGI1 has only one Validation example: no robust class1 performance/interval claim. MGI0/healthy detection is unsupported; no participant-independent/clinical/final performance claim.

Fixed development Grad-CAMs use the three eligible Validation arrays. Model input remains extended float; display previews are separately clipped and downsampled to max1200pixels, with common geometry for original-preview/heatmap/overlay and disclosed clipping. Heatmaps are model attention, not clinical boundaries.

Every result: **Provisional labels; non-clinical; non-final; participant independence unverified.**

## Focused tests and portability

- Export integration:51 generated tests passed, including complete733-source synthetic JPEG packaging, three CAMs, archive CRC/hashes, safe re-extraction, malformed input, tampering, stale bindings, holds/Test/NP015 and no-retry behaviour.
- Final **fresh code-ZIP extraction**, isolated Python imports: **68 passed,0 failed,0 errors,3 skipped;71 selected**,23.55s. This includes51 export and17 pure pilot/configuration cases. Do not add repeated runs as extra test cases.
- The three new backend cases are skipped locally because torch/torchvision are unavailable: four-logit ResNet50 optimisation/frozen-BN, four-grade Grad-CAM/hook/alignment, and synthetic checkpoint/reproducibility.
- Runtime acceptance correctly remains **INCOMPLETE**, exit3 despite pytest's exit0. Old Colab77/77 does not validate the new four-grade runner.
- Initial four malformed-plan tests exposed KeyError rather than a controlled ValueError; the new module's schema guard was fixed and all assertions retained. Code review also corrected the new CAM adapter to reuse existing `gradcam_views`' tuple/status handling; its torch execution remains one of the pending backend tests.
- No installs. Existing pure-Python pytest reused with bundled Python3.12.14/NumPy2.3.5/Pillow12.3.0/LittleCMS2.19. Previous ICCv2 95/95, B1 Colab77/77, streaming57/57 and generated-export48/48 evidence reused, not rerun.
- Code ZIP has **20 Python source/test files plus a full allowlist/hash manifest**, CRC/full hashes checked, dependency closure checked and fresh extraction tested. Notebook JSON structure and every Python cell compiled; the optional formal `nbformat` validator is unavailable and was not installed.

## Files created/updated

Created:
- `src/vision/b1_jpeg_source_v1.py`
- `src/vision/b1_development_bundle_v1.py`
- `src/vision/exploratory_pilot_b1_v1.py`
- `src/vision/verify_b1_pilot_runtime_v1.py`
- `src/vision/build_b1_pilot_handoff_v1.py`
- `tests/test_b1_local_export_v1.py`
- `tests/test_exploratory_pilot_b1_v1.py`
- `docs/vision_b1_local_export_contract_v1.md`
- `docs/vision_b1_local_packaging_results_v1.md`
- `docs/vision_b1_local_packaging_evidence_v1.json`
- `docs/vision_b1_pilot_colab_handoff_v1.md`
- `docs/vision_b1_pilot_colab_v1.ipynb`
- `docs/vision_b1_pilot_code_v1.zip`

Updated only current handoff and append-only diary/AI log. Other work preserved. Detailed actual provenance/counts/hashes: [aggregate evidence](vision_b1_local_packaging_evidence_v1.json).

## Blockers and ONE next action

The local package **really exists and passed**. Colab handoff files are prepared. Actual four-grade execution is **not yet runtime-qualified**:3 new backend cases require Colab; documented ResNet50 V2 weights are missing locally and no download is authorised. Separate explicit cloud-upload and dental-training permissions are absent. Final labels/group/participant/scientific approvals remain unchanged.

**Owner's next single action:** follow [code-only Colab instructions](vision_b1_pilot_colab_handoff_v1.md), run the71 generated checks with `RUN_PILOT=False`, and return the downloaded actual evidence ZIP. No dental-data upload is needed for this step.

Viva: **ZIP pass ஆனதால் model accuracy நிரூபிக்கப்பட்டதா?** இல்லை. அது data/engineering integrity verification மட்டும்; dental training மற்றும் scientific evaluation இன்னும் செய்யவில்லை.
