# Owner-authorized final-bottleneck exploratory stage v3

## Actual Colab qualification verified — 2026-10-15

Owner completed **33 passed, 0 failed/errors/skipped in13.58s on Tesla T4**. All five backend cases executed. Verified actual4825-byte ZIP SHA `c580566ca9c9729415f48d90c5346f2acdb1b04e62773371aeff3dbe611a0d0f`, CRC, five evidence payload hashes,33unique exact JUnit IDs/log/summary, and22source hashes before/after/archive/current. Environment Python3.13.15,torch2.11.0+cu130,torchvision0.26.0+cu130,NumPy2.1.3,Pillow11.3.0,pytest8.4.2. Sources unchanged;no dental-image access/training or weights in this generated verification. No tests repeated during evidence review. [Factual record](vision_b1_lastblock_runtime_verification_v3.json);[original-byte evidence copy](vision_b1_lastblock_runtime_evidence_v3.zip).

**Next:** owner executes the [existing single-stage cell](vision_b1_lastblock_run_colab_cell_v3.txt) in the same completed GPU notebook, reusing existing data and pinned v2best. Exact owner approval already recorded;no further permission needed within that scope. Maximum5additional stage epochs,patience2;all181holds/NP015/protected/Test excluded. Any missing state or failed safety check STOPs;no old-run replay or automatic retry. **No actual v3 dental result yet.** Historical preparation/pending-qualification wording below is superseded by this actual evidence, not rewritten into a claimed earlier success. Clinical/label/participant/final-research approvals remain absent.

2026-10-15 · branch `vinuthan`. Preparation completed; **actual Colab qualification and v3 dental training remain unexecuted**. Owner's YES approves the exact prospective plan and ONE bounded real stage only after actual generated backend PASS. No promised performance improvement or final-model promotion.

## Actual preparation evidence

- New isolated runner reuses existing Dataset, B1 normalization, weighted epoch objective, metrics, early-stop helper, checkpoint writer and Grad-CAM. Historical v1/v2 implementation and results are unchanged.
- Local focused suite: **28 passed, 0 failed/errors, 5 skipped** (Torch unavailable). Fresh code-only extraction: **28 passed, 0 failed/errors, 5 skipped**. All 33 unique case IDs match; all 22 payload hashes unchanged. Colab must execute all five backend cases, producing **33 passed / zero failures, errors or skips** before a real run.
- ZIP: `vision_b1_lastblock_code_v3.zip`, 99320 bytes, SHA-256 `c88c791d4e562012b44fad7095eaf814be7f442a303a53310da50a38caf26f2b`. Contains 22 code/test/aggregate-reference/owner-record payloads plus its full SHA-256 manifest. No images, model weights or checkpoint included.
- Old v1 archive's 20 payloads and old v2 archive's 19 payloads still match current files byte-for-byte. No dependency installations, old training replay, new dental-image access or dataset packaging during preparation.
- New notebook's two Python cells parse successfully. This is preparation evidence, not a Colab PASS. Details: [preparation JSON](vision_b1_lastblock_handoff_preparation_v3.json).

## Exact approved recipe

| Choice | Bound value |
|---|---|
| Initialization | Verified v2 **best epoch 1**; SHA `c84936ad7af7366e44e4ae2456c00ba748bae47b983ef9e0df204ce80c386dbf` |
| Trainable parameters | `fc.weight`, `fc.bias`, `layer4.2.conv1.weight`, `layer4.2.conv2.weight`, `layer4.2.conv3.weight` |
| All other tensors | Frozen, including every BatchNorm affine parameter and running statistic |
| Fresh optimizer | Adam: head LR 0.001, selected convolutions LR 0.00001; weight decay 0; never restore old optimizer |
| Objective | Same Training-only balanced cross-entropy, sum(w*CE)/sum(w) |
| Bounds | Seed 42, batch 16, maximum 5 **additional** epochs, patience 2; Validation four-grade macro-F1 selection |
| Data | Same 680 Training / 53 Validation; 181 holds, NP015/protected groups and Test remain excluded |
| Outputs | Best/last checkpoints, exact starting/selected tensor hashes, 53 best Validation probabilities, three fixed Grad-CAM triplets, parameter counts and measured GPU time/peak allocation |

Selected-layer fine-tuning is consistent with signed proposal §3.3 p.21. The precise block, two learning rates, checkpoint initialization and bounds are owner-approved engineering choices, not claims that the proposal prescribed them. Separate four-output exploratory MGI1–4 stage only; original five MGI definitions/model and final research approval gate stay unchanged.

## One practical Colab handoff

**Keep the existing completed weighted-v2 GPU runtime open.** Do not rerun historical cells or start a fresh runtime. It must still contain `data_root`, `balanced_output`, the verified development payload and pinned v2 best checkpoint. Missing state causes STOP; this handoff does not authorize old-run replay, new upload of images or weight downloads.

1. Open [verification cell](vision_b1_lastblock_verify_colab_cell_v3.txt), copy its complete text into ONE new code cell at the bottom of the existing Colab notebook, and run it. When prompted upload only [99 KB code ZIP](vision_b1_lastblock_code_v3.zip). The cell verifies archive/source hashes and runs the 33 generated cases in a subprocess; save the downloaded synthetic evidence ZIP.
2. If and only if the actual first cell passes 33/33, run [single-stage cell](vision_b1_lastblock_run_colab_cell_v3.txt) in a second new cell. The owner YES already covers this exact stage. It binds the actual proof hash and a fresh UTC output ID to the fixed owner/code/protocol/manifest/initial checkpoint record, consumes one exclusive attempt marker, then trains once and downloads the complete results ZIP. Any failure stops; no automatic retry or recipe change.

[Two-cell notebook reference](vision_b1_lastblock_existing_runtime_v3.ipynb): copy its cells into the existing notebook; opening it as a new runtime loses required data/globals.

The five required backend checks are initial-checkpoint restore/hash/provenance; real ResNet50 generated selected-layer optimization and all-frozen tensor checks; generated two-run fit/checkpoint/probability reproducibility; trainable-group/BatchNorm rejection checks; and existing Grad-CAM alignment/hook cleanup without weight updates. Generated models use `weights=None`; only the subsequent authorized real stage loads the pinned previous checkpoint.

## Three lines to understand

- `parameter.requires_grad_(name in allowed)`: ஐந்து அனுமதித்த parameter tensors மட்டும் கற்கும்; மற்ற weights மாறாது.
- `module.eval()` plus BatchNorm `requires_grad_(False)`: BatchNorm statistics மற்றும் affine weights இரண்டையும் உறைய வைக்கிறது; `eval()` மட்டும் போதாது.
- Two Adam groups: head learns at 0.001, final convolution block at 0.00001. Small block updates adapt features conservatively; they do not guarantee better Validation results.

Viva: Why fine-tune only one final bottleneck? தமிழ்: பழைய பொதுவான image features-ஐ பாதுகாத்து, கடைசி features மட்டும் நம் development task-க்கு சிறிது மாற்றிப் பார்க்கிறோம்; overfitting அபாயத்தைக் குறைக்க இந்த bounded experiment.

## Limitations and remaining evidence

Repeated use of the same Validation set and its selected v2 checkpoint introduces selection optimism. This is not a single-factor causal experiment, final model choice, participant-independent assessment or clinical validation. V2 classification remains weak; no grade-1 recall and poor grade-3 recall. No supported whole-image MGI0 examples; grade1 has only 12 Training / 1 Validation examples. Qualified labels, participant independence and final frozen research manifest remain pending. Grad-CAM shows model attention, not clinical boundaries. No v3 metric or runtime estimate is fabricated; report actual outcomes even if worse.

**Next single action:** run the new generated-only verification cell in the still-existing Colab GPU runtime and upload only the new code ZIP.

## Actual authorized stage completed — superseding pending-training notes above

2026-10-15:5additionalepochs,best5,27/53correct,macroF1.325872,macroAUROC.627264,Brier.659312. ActualresultsZIPandbindingsverified;315savedfrozentensorhashesunchanged,only5allowedchanged. Grade2recallworsenedwhile3/4improved;notafinalmodelorclinicalsuccess. [Completeactualresult](vision_b1_lastblock_results_v3.md). **ONEstageauthorizationconsumed;do not rerun training cells.** Nextrecommendationisfocusedexisting-evidenceerroranalysis,notautomaticfurthertraining.
