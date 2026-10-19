# Vision accuracy investigation with three parallel reviewers

17 October 2026 · Branch `vinuthan` · **Investigation completed; no improved dental accuracy result has been produced.**

The owner explicitly requested multiple agents to work backwards from poor image accuracy. Three read-only reviews covered training/preprocessing code, saved error/class evidence, and primary dataset metadata. One reviewer additionally executed generated-only numerical checks. No source dental images, raw annotations, model tensors, held/Test payloads, real training, external AI uploads or downloads were used. Current concurrent demo/UI work was preserved.

## Main finding

There is no basis to say every dataset is bad, or that label issues alone caused the current scores. The evidence supports a combination of task/class-support limitations, weak minority-grade recognition, limited adaptation experiments, and a preprocessing hypothesis worth testing. No reviewed class mapping, optimizer, loss or checkpoint defect has yet been demonstrated to explain poor learned accuracy.

## What the saved results actually establish

| Finding | Evidence | Meaning |
|---|---|---|
| Nested EfficientNet head52.21%=355/680; same-cohort majority53.09%=361/680 | [Nested results](vision_nested_feature_probe_results_v1.md) | Accuracy alone does not show an improvement over constantGrade4 |
| Macro-F1.346429 versus majority.173391; balanced accuracy.348645 versus.25 | Same nested results | There is some balanced grade signal, with substantial remaining errors |
| MGI1/2/3/4 support12/84/223/361; correct0/27/96/232 | Same nested results | Grade1 is not recognized; no whole-imageMGI0 support in this cohort |
|52.21% used frozen ImageNet features and95Logisticfits; zero neural optimizer steps | Same nested results | This is not a completed end-to-end EfficientNet fine-tuning comparison |
| ResNetv3 trained head plus last bottleneck only; five additional epochs;315tensors frozen | [v3 results](vision_b1_lastblock_results_v3.md) | Do not assume all plausible adaptation has been exhausted |
| v2→v3 Grade2correct12/13→1/13 while total correct increased | [Grade2 diagnosis](vision_grade2_v2_v3_diagnostic_v1.md) | The accuracy increase traded away minority-grade recall |
| v3CUDA50.94% versus seed43MPS43.40% on53Validation records | [v3](vision_b1_lastblock_results_v3.md), [replication](vision_b1_seed43_replication_v1.md) | Run-to-run variation is real; seed alone was not isolated |
| Training52queue has14histogram conflicts and12tooth-count referrals; all52pending | [Triage](vision_training52_evidence_triage_v1.md) | These held records need review. Their conflicts do not prove the included680labels caused the model errors |

These historical53Validation and680TrainingOOF populations must not be ranked directly against each other. Four-output experiments do not validate the five-grade research objective. Qualified labels/group decisions and participant identity remain unresolved.

## Code review and a concrete preprocessing hypothesis

Reviewed source paths include `exploratory_pilot_b1_v1.py`, `exploratory_pilot_b1_balanced_v2.py`, `exploratory_pilot_b1_lastblock_v3.py`, `exploratory_pilot_b1_seed43_v1.py`, `model_pipeline.py`, `colour_b1_prototype.py` and `colour_b1_streaming.py`.

Source review found internally consistent RGB→CHW/ImageNet normalization, provisional grade→index mapping, weighted cross-entropy normalization, optimizer steps, declared selective unfreezing/frozenBatchNorm and best-checkpoint restoration. This is a focused review, not a new comprehensive test suite or proof of clinical correctness.

**Demonstrated mechanism:** existing B1 `_model_view` downsamples with half-pixel bilinear interpolation and no antialias filter. The frozen [export contract](vision_b1_local_export_contract_v1.md) explicitly declares this. A roughly7286×4863 source becomes224×150 content in a224square; each output sample uses four source neighbors. High-frequency information can alias in this sampling process. This is a documented design choice, not an accidental regression.

The reviewer called the existing streaming sampler on an in-memory generated7286-wide, two-pixel alternating stripe. Only OS-file identity checking was temporarily substituted for an in-memory sentinel and restored in a `finally` block; interpolation code was unchanged. An area-average reference used installed Pillow BOX resizing. No dental source or model was involved.

| Generated stripe result | Minimum | Maximum | Standard deviation |
|---|---:|---:|---:|
| Existing B1 bilinear |0|1|.4081931710|
| Area-average reference |.4848484993|.5151515007|.0109033668|

This demonstrates aliasing on the synthetic fixture. It does **not** prove that dental-grade information was lost or that a different filter improves classification. The fixture is a deliberately high-frequency example, not a clinical image simulation.

A separate candidate primitive check used installed `torch.nn.functional.interpolate`, bilinear/`align_corners=False`/`antialias=True`, on generated signed stripes, a[-16,16]ramp and constants. CPU outputs were finite with expected shapes. Float32 constant errors reached9.536743e-7 at-3.25 and1.907349e-6 at+4.75; the latter failed a1e-6range assertion. Do not claim bit-exact constants, strict range preservation, full B1/ICC qualification, streaming-memory compatibility or successful clinical colour validation. Nothing was activated.

Generated-check environment: Python3.13.5, NumPy2.5.3, Torch2.11.0, Pillow11.3.0, CPU. See [aggregate numerical receipt](vision_accuracy_generated_diagnostic_v1.json). No pytest pass count is created from these numerical observations.

## Interpretation correction made

The seed43report previously attributed variation to seed/loader RNG while describing a fixed recipe. In fact v3ran on TeslaT4/CUDA/Python3.13.15/NumPy2.1.3, while the follow-up ran on AppleMPS/Python3.13.5/NumPy2.5.3. Seed **and** backend/runtime changed. An explicit correction has been added to the report. Numerical results and historical hash-bound source/receipts remain unchanged; no new fit is needed to correct the interpretation.

## Dataset compatibility: relevance is different from readiness

- **Original Mendeley source:** official metadata lists1,096images with captions/labels andCCBY4.0. It remains relevant to this project. Image-maximum MGI is our derived target; the available whole-image class support needs to be reported honestly. [Official record](https://data.mendeley.com/datasets/3253gj88rr/1).
- **MIOv2:** official metadata lists765adult intraoral photographs with image-level Healthy/Gingivitis/Periodontitis categories. It does not establish this project's maximum-visibleMGI0–4 labels or participant grouping. Do not automatically mapHealthy→MGI0 orPeriodontitis→MGI4. Archive contents were not inspected or downloaded. [Official record](https://zenodo.org/records/22047269).
- **Related2024MGIgrading study:** a reviewer verified a related826-photo study, but its patient images are not publicly available according to its data-availability statement. Related methodology is not an immediately available replacement dataset; exact target compatibility remains unverified. [Publisher article](https://www.nature.com/articles/s41598-024-70311-y).

The primary original dataset paper was checked by the dataset reviewer; a subsequent root fetch encountered a browser challenge. Its publication assertion about different persons does not settle locally identified duplicate/NP015 questions. Existing approved source evidence remains authoritative; no new participant IDs or clinical grades were inferred.

## Next concrete improvement trial

The prepared [matched EfficientNet adaptation plan](vision_accuracy_next_experiment_v1.md) compares a frozen neural-head control with head+final-block adaptation on the same680Training records/five folds, unchanged B1inputs/labels, one backend, fixed five epochs, exactly10fits. It is not implemented, authorized for execution, or run by this report. A matched control helps isolate adaptation; the historical52.21%LRworkflow cannot isolate that effect by itself.

This is preferable to silently replacing the colour/resizer contract or searching the same53Validation images again. Any antialias pathway remains separately versioned generated-only engineering work until properly qualified and prospectively compared; do not feed changed derivatives into historical checkpoints and call the result a model improvement.

Parallel scientific work remains qualified review of the existing Training52queue and source-supported whole-imageMGI0/rareGrade1evidence. No training trick manufactures that evidence. A separate TXT-supervised detector can be considered under a supplementary protocol; its mAP is not the current classifier's accuracy and it does not retroactively improve52.21%.

## Teaching notes

1. **Why check the majority baseline?** Always predicting the commonest grade gets53.09%here, so52.21%alone cannot defend balanced recognition. Macro-F1and per-grade recall expose failures hidden by accuracy.
2. **What does frozen mean?** EfficientNet converted images to features without updating its neural weights. Only the downstream classifier was fitted. Fine-tuning is a distinct experiment, not an already-proved solution.
3. **Why not switch antialias on immediately?** Model inputs would change. We must preserve colour/numerical contracts and compare newly trained models under a declared protocol; the generated stripe result is not a dental accuracy measurement.

Viva: **Is the dataset the proven cause?** No. We found sparse/absent image classes and unresolved evidence, plus limited adaptation and a sampling hypothesis. The review separates observations from causes and proposes a controlled comparison.

What I understood (owner): pending.
