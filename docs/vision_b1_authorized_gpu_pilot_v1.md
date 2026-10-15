# Owner-authorized B1 exploratory GPU pilot — execution handoff v1

2026-10-15, branch `vinuthan`. The owner explicitly answered YES to cloud upload of the verified733-source development bundle/3CAMs, official ResNet50 V2 weights download, and at most5epochs of the separate MGI1–4 head-only GPU pilot with Validation/3CAM outputs. This supersedes the earlier permission-pending restart. No clinical, institutional or final-research approval is asserted; no paid-resource purchase or automatic retry.

Owner record: [authorization](vision_b1_pilot_owner_authorization_20261015.json).
New execution notebook: [vision_b1_authorized_gpu_pilot_v1.ipynb](vision_b1_authorized_gpu_pilot_v1.ipynb).
Old disabled notebook, original code ZIP, verified implementations, packaging guards and research gates remain unchanged.

## Next practical steps

1. Open the NEW notebook in Colab. Choose Runtime → Change runtime type → T4 GPU (if freely available), then Save/Connect. If no compatible GPU is available, stop; do not install packages or purchase compute.
2. Run the first code cell and upload ONLY `vision_b1_pilot_code_v1.zip`. Run the next GPU preflight cell. It checks actual CUDA/torchvision, generated four-logit execution, head update, frozen backbone/BatchNorm and Grad-CAM geometry/hook cleanup before any dental upload. Previous verified71-case CPU evidence is reused, not rerun.
3. After PASS, run the owner-binding cell, then the dataset-upload cell. Upload ONLY `pp1_b1_dev_v1_20261015T085436527238Z.zip` from the project's ignored `data/vision/` folder. Exact737entry archive, membership/hash/NPY/provenance verification precedes training. No Drive mount or Test access.
4. The weights cell uses only the authorized official `https://download.pytorch.org/models/resnet50-11ad3fa6.pth`, verifies its published hash prefix and records its measured full SHA. No hash is invented before download. Invalid cached files fail closed; one download-attempt marker prevents automatic retries.
5. Training cell binds the actual current code/protocol/manifest/weights SHA and fresh run ID to the real owner decision, records provenance and starts ONE bounded run. Seed42,batch16,lr0.001,max5epochs,patience2,frozen backbone/BatchNorm; early stopping may finish before5epochs. A fresh exclusive attempt directory prevents rerunning the cell after failure. Do not press Run all blindly or retry a failed operation; retain the exact error.
6. Final cell downloads actual results: best/last checkpoints, epoch/Validation metrics, Training-derived majority baseline, nine PNGs for the three CAM triplets, owner/runtime/source/weights provenance and result-file hashes. Return the downloaded ZIP for factual review. No PASS or learned results are claimed in advance.

## Fixed scope and limitations

680Training +53Validation =733 provisional candidates;181holds,NP015/protected groups and Test stay excluded. Original five-grade research model/proposal is unchanged; this opt-in four-output pilot covers original grades1–4 only. Training grade support12/84/223/361;Validation1/13/22/17. No MGI0/healthy prediction, clinical performance or verified participant independence. Validation is used for early stopping and is not an unbiased final test. Display previews may clip; B1 model inputs stay unclipped.

**Provisional labels; non-clinical; non-final; participant independence unverified.**

## Checks actually performed during preparation

- Local branch verified `vinuthan`; all existing dirty work preserved.
-20/20 code ZIP payload hashes agree with current source; original code ZIP CRC/hash pass.
-733-source local archive rehashed,732575501bytes,SHA256 `a8a4f7f339c589f81335d7afb663f4cf62d30e217f65bc480683d0a770afed70`.
- New notebook:7 code cells syntax checked;7 targeted authorization checks passed,0 failures, including badscope/status/hash/missing safeguard rejection and the exact owner-binding cell with local safe stubs. These are preparation checks, not a new pytest/GPU/training run.
- Actual GPU compatibility checks, upload, weights download, dental training and result generation have NOT yet executed. Existing ColabCPU71/71 remains historical verified evidence; no repeated suite.

Viva: **Why freeze the backbone first?** Pretrained visual features-ஐ வைத்துக்கொண்டு final classification head மட்டும் கற்றுக்கொள்வதால், இந்த சிறிய provisional cohort-ல் குறைந்த compute-உடன் முதல் bounded experiment செய்யலாம்; நல்ல clinical performance உறுதி கிடையாது.
