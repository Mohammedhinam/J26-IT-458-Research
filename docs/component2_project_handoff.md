# Component 2 project handoff

## Version control snapshot — 19 October 2026

Owner explicitly requested commit and push on the existing `vinuthan` branch.
This snapshot packages 99 source/report files in 14 logical commits, including
the current four-model proposal demo, bounded experiments, notebooks and the
31-page beginner guide. Earlier statements that this work is only uncommitted
describe historical snapshots. Git transport confirmation is reported after
this final log/handoff commit.

Data, trained weights, photos, temporary artifacts and the three photo-bearing
PPTX packages remain local and ignored. Both committed Word reports were checked
to contain no embedded media or embedded files. A remote clone therefore still
needs the separately preserved local model/data artifacts to run the full demo;
do not upload those to make a checkout appear self-contained.

Pre-push checks: 41 changed/new Python files parsed; 33 ordinary Python notebook
cells parsed and one Colab shell-magic cell retained as Colab-only; all five
notebooks have no saved outputs or attachments. Nine JSON reports parsed, no
secret-shaped credential hits were found, and the frontend rebuilt byte-for-byte
with the existing bundle using cached dependencies. Markdown hard breaks and
one existing test EOF blank line were preserved to retain verified source bytes.
No training, final Test rerun, dependency installation or running-demo restart.

## Latest: EfficientNet main candidate now integrated — 18 October 2026

Owner explicitly requested adding the trained proposal candidate. **Open
http://127.0.0.1:8773/**, launch `zsh scripts/run_pp1_proposal_demo.sh`.
[Verified integration/runbook](vision_efficientnet_live_integration_v1.md).
The earlier8771process was preserved. Use8773for the new candidate runtime.

One photo now runs EfficientNet-B0 first (proposal main candidate), ResNet50v3
second (baseline), followed by ROIv1 and CORALv2 as additional experiments.
Four individual statuses, results and feedback records, with Doctor/Developer
modes and local-only consent/export/privacy preserved. Existing XGBoost,
Questionnaire/SHAP/what-if/reset remain unchanged and working.

Actual pinned EfficientNet checkpoint is existing `fold0_last_block/final.pt`
under `data/efficientnet_adaptation_v1_20261017_1792202682936988000/`, SHA
`b557f52e358ca88329391e01e3f2c6f77123d14bbbe1027dd38391a27ea96353`.
360/360training tensor hashes match. Shared B1 input/decoding, predicted-class
Grad-CAM at `features.8`, original geometry and honest attention. No retraining.
Its **neural680OOFaccuracy46.76%,Macro-F1.3416,G1=1/12,G2=33/84** is distinct
from52.21%frozenfeatures+Logistic. Fold0is illustrative, not an all680refit or
clinical model. Main-candidate role does not mean best demonstrated accuracy.

**40focused tests +40browser checks passed,0failed**. Permitted photo genuine
gradesEfficientNet3/ResNet3/ROIv1max3with12boxes/CORALmax2with12boxes. Same bytes
verified for all four. Three initial numerical checks failed at an overly strict
1e-7ordinary-vs-gradient tolerance; final independent gradient parity and shared
1e-6float32bound passed without model/pixel/heatmap modification. Initial failure
XML preserved.39protected artifacts unchanged;4intended API/UI files changed
with before snapshots. No originalcheckpoint/research/data/labels/splits/Test,
oldprocess, cloud upload or commit/push/reset changes.

New10-slide editable/render-verified deck:
`docs/pp1_final_20261018/PP1_Proposal_Doctor_Demo_v3.pptx`. Desktop convenience
folder: `/Users/vinuthanvinuthan/Desktop/PP1_Proposal_Demo_20261018/`.
Evidence: `data/vision/efficientnet_live_integration_20261018_v1/`.
Earlier three-model delivery below is historical. Clinical review and Grade1/2
reliability remain pending, and Grad-CAM still has irrelevant-region attention.

## PP1 final local rehearsal delivery — 18 October 2026

Owner authorized completing the local demo, ROI coverage investigation, fair
comparison and presentation while away. [Final runbook](pp1_final_delivery_20261018.md),
[ROI results](vision_roi_context_diagnostic_20261018.md),
[data/review preparation](grade12_data_review_next_steps_20261018.md).
Open **http://127.0.0.1:8771/**. Restart with
`zsh scripts/run_pp1_doctor_demo.sh` from this repository. Desktop convenience
folder: `/Users/vinuthanvinuthan/Desktop/PP1_Final_Demo_20261018/`.
The 10-slide editable deck is `docs/pp1_final_20261018/PP1_Doctor_Demo.pptx`.

Fresh verification: **31 API/decoding tests + 37 browser checks passed, 0 failed**.
Actual permitted photo outputs remain ResNet3, ROIv1max3/12boxes, CORALmax2/12boxes.
Questionnaire/SHAP/what-if/reset work independently. Existing React/API, models
and research were preserved: **29/29 protected hashes unchanged**.

Four fit-only Grade1/2 coverage sheets reproduced **48/48 exact training crops**.
Visible gum margins already appear in current crops; clinical sufficiency remains
unverified. One predeclared frozen-weight padding15%vs30% inference ablation on
the same136scorephotos yielded accuracy61.76%vs62.50%,Macro-F1.3347vs.2980,
Grade1both0/3,Grade2 1/17vs0/17. Shared detector boxes and unchanged fold-00 weights.
**Do not promote the expanded context.** Local baseline matches128/136historical
CUDApredictions; cause of8disagreements unisolated, no680OOFimprovement claim.
Twelve generated geometry and76independent saved-result assertions passed.

The76-case fit review queue is9Grade1+67Grade2, with blank qualified reviewer/grade
fields. Zero new verified photos/clinical labels. Qualified review and any future
matched training study remain pending. No new training, Test payload, held-record
release, external upload, commit/push/reset or process disruption. Original demo
continues using the original three checkpoints. Private evidence:
`data/vision/pp1_final_local_20261018_v1/`. Engineering/demo rehearsal preparation
is complete; clinical readiness and Grade1/2 accuracy are not established.

## Latest controlled ResNet50 fold-0 return — 18 October 2026

Owner explicitly approved and ran the bounded shared1epoch+5A+5B Colab experiment, then
returned `resnet50_fold0_return_v1.zip` (SHA `e169edc135e5f6786bf510bd81d5cb3b77125d08edfa944ac5f121f4f694de8c`).
[Actual results and CAM review](vision_resnet50_fold0_colab_results_v1.md). The unchanged
544fit/136score Training fold has grades1–4 support9/67/179/289 and3/17/44/72.
A last-bottleneck:55/136=40.44%,Macro-F1.2341; B full-layer4:62/136=45.59%,Macro-F1.3175.
Grade2recall1/17→5/17, Grade1both0/3; majority accuracy52.94%. These are single-fold
results and must not be compared directly to680OOF or53Validation metrics.

All154return file hashes,11checkpoints/3520tensor hashes, official320/320initializer hashes,
shared warm-up, frozen BN, optimizer/batch-order provenance and independently recomputed
metrics passed.8matched cases/16predictions/32CAMs reproduced on CPU (probability error≤1.91e-6,
RGB differences≤1/255). Qualitative AI review still sees peripheral/lip/retractor attention;
consistent gingival focus and clinical localization are not established.29protected artifact
hashes remain unchanged. Return preserved separately under
`data/vision/resnet50_fold0_pilot_v1_20261018_r2/colab_return_v1_20261018/`.
**No replacement of PP1 models/demo and no further training or promotion.** Next meaningful
research step requires qualified review and a separately approved protocol. Existing UI below
continues to use its original three models.

Last reconciled: **2026-10-18 (Asia/Kolkata)**. Owner: Vinuthan T, IT23311022.
Workspace: `/Users/vinuthanvinuthan/Desktop/RP-J26-IT-458`; branch **`vinuthan`**.
Remote: `https://github.com/Mohammedhinam/J26-IT-458-Research.git`.

## Latest UI reference update (18 October 2026)

Owner requested the blue/teal dashboard reference. Implemented dark sidebar and teal header, drag/drop upload, aligned three model cards, real class-score bars, compact Grad-CAM triptych, ROI probability tables and model-specific feedback below. Doctor independent assessment still precedes AI inference. All sidebar links work; Vision is now the default tab. Refresh **http://127.0.0.1:8771**. See [UI update and verification](pp1_doctor_demo_ui_v2.md).

Final verification: **37 browser checks / 21 API tests passed**, **15/15 protected hashes matched**. Backend, checkpoint loaders, trained weights, scientific model code and research results were not changed by this UI task. Real same-photo outputs remain MGI3 / max3+12ROIs / max2+12ROIs. Original attention is preserved, including the upper-lip hotspot. New evidence/screenshots are in ignored `data/vision/doctor_demo_ui_v2_20261018/`. No training/Test access/external images/commit/push/reset.

## Latest approved PP1 Doctor Demo implementation (18 October 2026)

The approved three-model workspace is implemented and verified. Read [run instructions, exact changes and verification](pp1_three_model_doctor_demo_v1.md). The current service was started at **http://127.0.0.1:8771** with the same pinned ResNet50 v3, ROI v1 fold00 and ROI v2 CORAL fold00. No training or replacement checkpoints.

Doctor Review Mode records an independent assessment before inference; Developer Demo Mode explicitly marks outputs not clinically reviewed. One JPG/PNG, consent and Run All dispatch the same bytes sequentially to existing endpoints. Responses verify source SHA; per-model status/results survive another model's failure; stale responses are invalidated. Feedback stays separate and only explicit JSON/CSV download persists an allowlist without source photo data, filename, input hash or patient-ID fields. Free-text notes must omit identifiers. Reset/navigation/reload discards case state.

V2 local uploads now use shared ICC/EXIF/alpha-validated sRGB pixels as lossless temporary PNG, matching v1; trained transforms/weights are unchanged. Predicted ROI numbers match table rows. Grad-CAM was not altered to focus on gums. Its 7×7 final-block feature map and independent CAM algebra parity were checked on the permitted non-study photo (max difference 1.79e-7); attention still includes upper lip. This is not clinical localisation proof.

Verification: 102 focused Python/API tests, final 32 browser acceptance checks, 6 real CAM checks, 4 independent missing-checkpoint startup checks; zero final failures; 12/12 protected hashes match. Three genuine outputs on the owner-permitted photo remain ResNet3, v1 max3/12 ROIs, CORAL max2/12 ROIs. Browser fault cases are explicitly synthetic fixtures. Screenshots/receipts are in ignored `data/vision/doctor_demo_20261018_v1/`. Actual clinician review remains pending. No Test access, training, external image uploads, commit/push/reset. Existing dirty changes preserved.

## Latest local photo-model comparison (2026-10-18)

The owner wants to run the same newly uploaded photo through each saved, runnable Vision model and compare their outputs. The React demo now keeps three runs visible together: the existing ResNet50 B1 v3 checkpoint with Grad-CAM, YOLO ROI v1 weighted-CE fold 00, and YOLO ROI v2 CORAL fold 00. Their grades remain independent; the page does not combine them.

On the owner's 540×360 RGB photo with no embedded ICC, ResNet50 predicted MGI 3 and output scores 0.1293, 0.2825, 0.3508, 0.2374 for grades 1–4. Its Grad-CAM hotspot fell on the upper lip rather than the teeth. ROI v1 returned 12 boxes (11 crop grades 1, one grade 3; maximum 3). ROI v2 returned 12 boxes (9 crop grades 1, 3 grade 2; maximum 2). The ROI detector confidence range was 0.5322–0.7285; it describes boxes, not MGI confidence. All these are one-photo research outputs, not accuracy measures or diagnosis. Both ROI models use fold 00, not final all-development refits. The ResNet50 B1 demo checkpoint is separate from the frozen ResNet + Logistic OOF row.

The same-680-Training-image OOF comparison is documented in [machine-readable comparison evidence](vision_photo_model_comparison_v1.json): ResNet + balanced Logistic is 47.50% accuracy / .2951 Macro-F1; EfficientNet + Logistic is 52.21% / .3464; ROI v1 is 60.74% / .3384; ROI v2 CORAL is 59.71% / .3279. ROI v1 has highest accuracy in that table but lower Macro-F1 than EfficientNet and lower Grade 2 recall (8/84 versus 27/84); every row has Grade 1 recall 0/12. The EfficientNet 52.21% model has saved OOF predictions but no fitted Logistic checkpoint/full-development refit, so it cannot currently run on a new photo. Accuracy alone does not establish the best model or fix Grades 1–2.

Start the local service using the command in [local upload setup and output guide](vision_local_photo_upload_demo_v1.md), which loads all three available model runtimes. Open `http://127.0.0.1:8770`, choose **Vision · exploratory evidence**, select a photo, check the permission box, then run **ResNet50 + Grad-CAM**, **Run YOLO v1 · 60.74% OOF**, and **Run YOLO v2 CORAL · 59.71% OOF**. Outputs stay together until the photo is reset or replaced. The UI also shows the four-row aggregate comparison. The source image is processed on loopback and is not saved; the ROI helper's temporary file is removed after inference. The questionnaire branch stays separate. See the [prior four-panel ROI v2 output](../data/vision/user_photo_demo_v1_20261018/demo_comparison.png) and [numbered v2 ROI boxes](../data/vision/user_photo_demo_v1_20261018/roi_boxes_mgi.png).

Final verification: all three runtimes reported ready on MPS and returned HTTP 200 on the same photo with `photo_saved: false`; omission of the consent header returned HTTP 403. The verified four-row evidence loaded from `/api/vision/evidence`. Fifty-seven focused tests passed. Photo, ResNet checkpoint, v1 ZIP, and v2 ZIP hashes matched their verified values. No training, data, labels, splits, protected Test payloads, or old PP1 models/results were changed. The updated React bundle passed `git diff --check`; no commit or push.

## Current next step — v2 ordinal result returned and verified (2026-10-17)

The owner ran [the v2 Colab notebook](../notebooks/roi_tooth_v2_ordinal_colab.ipynb) on a Tesla T4 and returned the archive. Read [actual v2 results and limitations](vision_roi_ordinal_v2_colab_results.md) and the [protocol and implementation handoff](vision_roi_ordinal_v2_plan.md). The run used 680 Training photos, five fixed folds (544 fit / 136 score per fold), 8,160 crop rows, and 12 epochs per arm. It did not use Validation for model selection or access protected Test payloads. All 21 return-manifest entries passed size/SHA checks; 680 OOF records, labels and folds matched the frozen protocol; metrics and the paired bootstrap were independently recomputed.

Matched weighted CE: 59.85% accuracy / .3241 Macro-F1; recall by grades 1–4 is 0/12, 5/84, 97/223, 305/361. CORAL: 59.71% / .3279; recall 0/12, 15/84, 46/223, 345/361. CORAL recovered ten more Grade 2 photos than matched CE but one fewer correct photo overall; Grade 1 remains zero. Compared with earlier v1 ROI (60.74% / .3384; Grade 2 8/84), accuracy and Macro-F1 are lower while Grade 2 recall is descriptively higher. Compared with historical EfficientNet (52.21% / .3464; Grade 2 27/84), overall accuracy is higher but Grade 2 remains lower. Do not claim that the weak-grade accuracy problem is fixed.

The 8,160 annotated tooth-crop diagnostic is separate: weighted CE 46.59% accuracy/.4031 Macro-F1/.3923 balanced accuracy; CORAL 40.78%/.3738/.4192. Crop scores bypass predicted localization and do not equal image-level MGI accuracy or detector mAP.

The return ZIP is preserved at `data/vision/roi_tooth_v1_20261017/ordinal_v2/colab_return_v1_20261017/roi_tooth_v2_coral_return.zip`, SHA-256 `e78240b01a1b039e091be0d2e31881ce96c1b1e47388e99f8f49b2541094771b`; its adjacent `verification.json` records the input hashes and 10/10 unchanged protected artifact checks. A separate v2 CLI adapter loads a selected fold only after checking the local receipt and ZIP manifest. Fold 00 ran on MPS for `Training/00002`: 12 ROIs, image grade 4, matching its OOF prediction; provisional target grade 3. Its clarified, watermarked ROI preview is [here](../data/vision/roi_tooth_v1_20261017/ordinal_v2/demo_outputs_v2/Training_00002_fold00_mps_research_only_final/roi_overlay.png). It is an isolated research preview, not a final all-development refit.

An optional local PP1 integration now adds a separate `/api/vision/roi-photo` route and React action, **Run YOLO tooth boxes + CORAL**. It loads verified fold 00 on MPS when available, uses the same source-registered photo gate as the existing ResNet50/Grad-CAM path, and returns predicted tooth boxes, crop grades, and the maximum-grade aggregation. The existing PP1 ResNet50 checkpoint and Grad-CAM route remain unchanged. The React source and bundle were rebuilt; 76 focused tests passed. The real v2 weights passed an API smoke test using only the generated colour fixture: HTTP 200, no detections, and no grade, as expected for a non-dental image. No source-confirmed non-study dental photo is registered yet, so real live tooth-box display still awaits an eligible photo. See [ROI v2 live-demo setup](vision_roi_v2_live_demo.md). No commit or push.

**Current state:** local Colab-return verification and optional React/API wiring are complete. Keep v2 research-only and do not run another training or promote a checkpoint based on these results. The optional runtime stays disabled by default and requires both the verified ROI return ZIP and existing photo-registration arguments; follow the linked live-demo guide. No real non-study dental sample is registered. Labels remain provisional, participant independence is unknown, Grade 1 recall is zero, and clinical/supervisor verification is still pending.

## Current Vision restart — Colab ROI result returned and checked (2026-10-17)

Read [full Colab ROI results](vision_roi_tooth_v1_colab_results.md) and [preparation/engineering record](vision_roi_tooth_v1_results.md). The five-fold YOLO26n tooth_roi detector + ResNet-18 crop classifier completed on a Tesla T4. The return archive and all 19 file hashes passed verification. The returned fold pairs are saved under the ignored `data/vision/roi_tooth_v1_20261017/colab_return/`; return ZIP SHA-256 is `ebb41badf4bd2154019dad55ba2f459ad1807c7f42b0722c13d849be2460f9bb`.

Evaluation uses one OOF prediction for each of the same 680 Training IDs and exact five-fold assignment as the historical EfficientNet result. No Validation model selection or Test data use. ROI accuracy is **60.74% (413/680)** versus historical **52.21% (355/680)** and majority **53.09%**. However, Macro-F1 is **0.3384** versus **0.3464**, balanced accuracy **0.3437** versus **0.3486**; Grade 1 remains **0/12** and Grade 2 falls to **8/84** versus **27/84**. Detector mAP50/50–95 averages 0.9598/0.4967 and must stay separate from image-level MGI metrics. Ground-truth-crop diagnostic over 8,160 crops is 46.67% accuracy/.4054 Macro-F1; this crop-only score does not replace photo-level evaluation. Do not claim the Grade 1–2 problem is fixed or promote this model to the live demo.

The paired fixed-prediction content-group bootstrap (1,000 draws, seed 42) gives ROI-minus-EfficientNet intervals: accuracy +3.82 to +12.94 percentage points; Macro-F1 −5.03 to +3.35 pp; balanced accuracy −4.35 to +3.30 pp; Grade 2 recall −33.33 to −12.64 pp. All 680 known content groups are single-image groups; participant independence is unverified, so intervals are conditional only. Qualified label approval remains false and image-grade MGI 0 is unsupported.

Mac verification loaded fold 00 on MPS and ran `Training/00002` (a fold-00 score image): 12 ROIs and grade 4, matching OOF; its provisional caption grade is 3. The overlay and JSON are in ignored `data/vision/roi_tooth_v1_20261017/demo_outputs/colab_fold00_training_00002/`. This remains an isolated experimental CLI; the existing PP1 Grad-CAM demo/checkpoint/UI is unchanged. The prior preservation audit still matches all 10 protected artifacts. No commit or push.

**Current state:** the planned Colab run, return integrity check, matched OOF comparison, Mac checkpoint smoke and documentation are complete. Do not launch another full training or tune thresholds from these scores without a separately defined experiment. Keep the result provisional and do not use it as a clinical diagnosis or final Test score.

## Approved matched EfficientNet trial — actual result (17 October 2026)

Owner explicitly approved the exact10-fit plan. [Actual report](vision_efficientnet_adaptation_results_v1.md), [aggregate](vision_efficientnet_adaptation_results_v1.json), [independent verification](vision_efficientnet_adaptation_verification_v1.json). **10MPSfits/50epochs completed**, same680Training/fivefolds/B1/labels. Head-only accuracy46.3235%/macro-F1.336195; head+`features.8` accuracy46.7647%/macro-F1.341579:net3morecorrect,+0.4412pp,+.005384F1. Neither beats historical52.21%nestedLRaccuracy/.346429F1; no successful overall accuracy fix or finalmodelpromotion. No whole-imageMGI0support; Grade1only1/12correct in both; Grade2 31→33/84.

Original summary failed **after allfits andOOFsave** on wrongmetric key`brier` versus actual`multiclass_brier`. OriginalFAILED/attempt/code snapshot preserved. Reporting-onlyhelper/regressionfixed; savedOOFrecovery performed with0newfits/0inference. `recovered_results.json`/`POSTPROCESSING_COMPLETE.json` clearlymarkrecovery; no fabricatedoriginalCOMPLETE. Timing/RSSnotcaptured beforeexception, recordednull. Current27generatedtests pass; original26pre-run is historical, notadditional.135saved-outputassertions pass,maxmetricdiff1.11e-16; all10×360checkpointtensorhashes and officialinitialstate independently verified. Instrumentedloader680allowedTrainingcalls only, notOSaudit.

Ignoredoutput:`data/efficientnet_adaptation_v1_20261017_1792202682936988000/`; persistentconsumedclaim:`data/efficientnet_adaptation_once_v1/attempt.json`. Newsource:`src/vision/efficientnet_adaptation_v1.py`; tests companion. Executionbindingpoints to preserved oldrunner; currentreporting-onlypatchSHA recordedseparately. No retraining/replay to repairreporting; no extraepochs/searchautomaticrepeat. Existingdemo/checkpoint, datasets/labels/splits/181holds/NP015/Test/questionnaire/colourpolicy unchanged; noTXTdetectortraining/install/download/upload/commit/push. Earliernext-plan-preview wording below is historical and superseded for this exact completed trial, not clinical/scientific approval.

## Accuracy investigation — three owner-requested agents (17 October 2026)

[Investigation](vision_accuracy_reverse_engineering_v1.md), [proposed next trial](vision_accuracy_next_experiment_v1.md). No new dental training or improved accuracy. Source review found no demonstrated class-mapping/loss/checkpoint bug explaining performance.52.21%is frozenEfficientNetfeatures+nestedLR, not neural fine-tuning; same680majorityaccuracy53.09%, macro-F1.3464versus.1734. Do not blame all datasets or infer held52conflicts caused the680cohort errors. Generated-only checks demonstrated the frozenB1non-antialiased sampler's synthetic aliasing and identified numerical qualification limits in a candidate antialias primitive; no preprocessing change activated. Originalsource remains relevant; alternative diagnostic labels are not automaticMGI0–4.

**Correction:** seed42v3CUDA and seed43MPS changed both seed and backend/runtime; variation does not isolate seed. Erratum added to seed43report; source/code/receipts/numbers preserved. The next exact10-fit/two-arm/five-foldEfficientNet plan is a preview, not implementation or execution approval. Existing labels/splits/181holds/NP015/Test boundaries and concurrent live-demo work preserved. Owner should read/understand the bounded plan before any new runner/real execution; no automatic training/download/upload/commit/push follows.

## Latest live-demo integration — 17 October 2026

[Runbook](vision_registered_photo_live_demo_v1.md), [actual evidence](vision_registered_photo_live_verification_v1.json). **101 focused tests passed, zero failed/errors/skipped; 24 unique browser checks passed.** Existing pinned v3 checkpoint + generated JPEG ran end-to-end through React upload, exact B1 input and aligned predicted-class Grad-CAM. Questionnaire/SHAP/What-if/reset also verified; no training, dental-image inference or Test rerun. Default photo runtime remains inactive; new explicit all-or-none CLI checkpoint/registration/trusted-SHA arguments activate only a registered scope. Generated verification is separately marked on local8772; previous servers preserved.

**The user's new PNG is of uncertain internet/other provenance**, confirmed directly by the owner; it was not registered or run. Real-photo runtime remains restricted to hash-registered, source-confirmed non-study RGB JPEGs, qualified embedded ICC, identity orientation, <=8MiB/40MP. It does not accept arbitrary phone/photos/PNG or infer missing ICC. No real source decision, clinical approval, held-image release or final-research activation was invented. Next real-photo step needs one genuinely source-confirmed permitted supported original JPEG; do not use Test/held/data screenshots as substitutes. All181holds/NP015, labels/splits/colour policies/models and scientific results remain unchanged; accuracy did not improve through integration. Continue remaining review and genuine feedback/rehearsal separately. No commit/push.

## Current Vision restart — Training-52 cached-evidence triage (2026-10-17)

See [triage report](vision_training52_evidence_triage_v1.md) and the existing ignored [Training-52 viewer](../data/vision/gingivitis/staging-16669f74665ff0deca6ddd25feb0d233e52fdc2313265465bf91731af1e8956b/training_recovery_review_v1_20261015/index.html). Read-only comparison of the existing selected Training cache/decision CSV: **52/52 pending, zero newly approved/eligible**. Cached evidence records14 caption/TXT histogram disagreements,12 tooth-count reviews,one additional unsupported/count case,2 partial-caption cases,4 group companions and1 NP015 identity hold. Parsed caption max and TXT maximum agree47/49; differ2;3 have no parsed maximum. A matching maximum does not clear full-histogram, clinical-label, group, or identity issues.

Focused original-file comparison of **Training/00025** now confirms the same image maximum grade4 in captions and mapped TXT, but a one-count MGI2↔MGI0 histogram conflict (captions0/1/2/3/4=`0/1/3/1/7`; TXT=`1/1/2/1/7`), plus a malformed MGI3 tooth-position phrase. TXT boxes lack FDI IDs; no correction is assigned. The case remains pending/held. Only this one Training image and its matching caption row/TXT were opened; no other image or Test record.

No other original RGB, CSV/TXT, Test payload, held Validation record or model output was accessed. No labels, splits, held status or approvals changed. **Next:** qualified annotation review starts with the14 histogram conflicts and12 tooth-count cases in the existing Training-52 viewer; group/NP015 decisions remain separate. Do not train on or promote any case until real review provenance and all existing gates are satisfied.

## Current Vision restart — seed-43 local stability replication complete (2026-10-16)

See [actual report](vision_b1_seed43_replication_v1.md) and [local output](../data/vision/pp1_b1_lastblock_seed43_v1_20261016T234343+0530/results.json). Owner authorized local exploratory training in the latest request; the exact predeclared follow-up was the seed-43 replication from the prior Grade-2 diagnostic. **MPS run completed on the same frozen 680 Training / 53 Validation bundle; best epoch 2.** Metrics independently recomputed from saved predictions aligned by all 53 Validation IDs.

- Seed-43 result: Validation accuracy **43.40%**, macro-F1 **0.2697**, recall MGI1/2/3/4 **0/1, 1/13, 7/22, 15/17**. Versus v3 seed42 on the same records, accuracy fell 50.94%→43.40%, macro-F1 .3259→.2697; Grade2 recall stayed 1/13 and Grade1 stayed 0/1. This supports run-to-run instability, not an improvement or causal explanation.
- MPS synthetic ResNet step passed; focused wrapper tests **9 passed, 0 failed, 0 skipped**. Actual stage took32.68s; process peak RSS607.19MiB; frozen315 tensors unchanged. New checkpoint SHA `2a6381c1f920e1aada04774bab814600764eae6f4b7a281e1a3f4e3cc677516f`; no pretrained download or new Grad-CAM run.
- Four-output MGI1–4 pilot only; MGI0 is unsupported at image level, Grade1 support is one Validation case, labels remain provisional, participant independence unknown. No Test, held records, original image/annotation/label/split change, upload, commit or push.
- The existing 172-case visual screen remains pending; it covered43 Training+129 Validation held candidates and assigned no AI grades. It was not an individual visual audit of all733 model candidates. Do not treat model predictions as label corrections.

**Next:** do not start another same-53 tuning run. Keep seed42 v3 only as a provisional demo candidate (not a final model); improve evidence first through supported Grade1/2 labels and participant/content-group review or a genuinely compatible additional source. Original five-grade research scope and all181 holds stay unchanged.

This is a local continuity record, not new research approval or a replacement for signed requirements. Read root `AGENTS.md`, current user instructions and only the relevant linked evidence before continuing. Signed proposal/verified records take precedence over conversational summaries; report conflicts instead of silently resolving them. Proposal: `/Users/vinuthanvinuthan/Downloads/RP-IT23311022 (2).pdf`, especially §§3.1–3.5, pp.17–22, and explanation validation p.23. The supplied original AGENTS attachment has been retained verbatim in the new root file, with a handoff pointer appended.

## Current Vision restart — 172-source header/ICC/XMP compatibility preflight (2026-10-16)

[Read-only report](vision_gemini_sanitisation_compat_preflight_v1.md), [aggregate counts](vision_gemini_sanitisation_compat_preflight_v1.json). **172/172 candidate JPEG headers, shared ICC structure, and standard XMP packets match the tested sanitizer structure; 0 structural failures.** Reused the selected 172 hash-bound case list, Training43/Validation129 only; current source hashes and stat identities match; header parsed through SOS only; zero RGB decodes, zero source changes, zero protected Test aliases accessed. No images exported/uploaded or training started.

The single 480-byte ICC profile contains `desc`/`cprt` text fields. Values were not saved/reported; privacy non-identification is not established, and its real SHA is not in the generated-only sanitizer allowlist. Personal Gemini risk acceptance/external-processing permission remains unresolved for172/172. **Next:** owner reviews those shared ICC text values locally, then separately decides whether to allowlist the profile for local derivatives; Gemini external processing needs its own permission. The preflight is not upload/package permission.

## Current Vision restart — generated JPEG metadata qualification, local only (2026-10-16)

[Qualification report](vision_jpeg_metadata_qualification_v1.md), [actual receipts/hashes](vision_jpeg_metadata_qualification_evidence_v1.json): **35 generated tests passed, 0 failed/errors/skipped**. Narrow baseline RGB8 marker-copy workflow removes supported EXIF/XMP/comments/thumbnails without re-encoding; decoded RGB, declared ICC colour interpretation, dimensions and generated source hashes/annotation bindings unchanged. Unknown ICC/rendering schemas, nonidentity orientation, malformed or tampered inputs fail closed. Generated ICC allowlist only; real ICC privacy not approved. No real172images/profiles accessed, package/upload/training or production activation. Next separate approval: local read-only172header/ICC/XMP compatibility/privacy check, nine protected Test aliases excluded. Personal Gemini risk acceptance/external-processing rights remain unresolved.

Owner requested saving completed work first: pushed four scoped commits f1ec893 (Vision comparisons), 6b37c40 (frozen questionnaire evidence), 6ddbd7f (PP1 demo/API), 2f1535d (held review/preflight) to vinuthan. New generated JPEG qualification intentionally remains local pending next work; no automatic further push.

## Current Vision restart —172-source read-only privacy/ICC preflight complete; release blocked (2026-10-16)

Owner explicitly authorized local read-only172candidate checks only, and explicitly did not accept PersonalGemini processing risks. [Actual report](vision_gemini_readonly_preflight_v1.md), [aggregate evidence](vision_gemini_readonly_preflight_evidence_v1.json). **Do not upload, package, modify or train.** No new permission/clinical approval inferred.

- Selected43Training+129Validation=172;9protectedTestaliases excluded before source access. JPEGsourcehashes172/172matchcachedreference;all172before/afterhash/statchecksunchanged.516selectedcaptionvariants/172TXTfilenameassociation,existingparserreproduction,TXThistogram,finitein-imagegeometry/twoROIs all172pass0fail. Existingannotationconflicts/NP015/all181holdsunchanged; filematching is notclinicalapproval.
- All172JPEGheaders RGB7286×4863/orientation1;all172ICCstructuresacceptedbyexistingstrictv2parser,480bytes/commonSHA2b8daf8cabe783b17f801e6687f57016b53c775a826269e21c51313083c9fefc. D50PCS/D65white/singlegammacurvqualifiedsubset;noRGBdecode,colourtransform,newDeltaE/displayequivalence/clinicalcolourclaim.
- **Verbatimoriginalprivacyclear0pass/172fail**:EXIF/DateTime/GPSInfo/MakerNote/XMPpresentinall172. GPSIFDversiononly172;coordinatesfields0. No privatevalues/profilebytes/pixels/rawannotationtextsaved. Absenceofcheckedserial/owner tagsdoesnotproveanonymity. Existingmaster/cachedinputsunchanged.
- OfficialCCBY4.0reconfirmed;service-specificconsent/institutionalprivacypermissionnotestablishedinthefocusedreview:0confirmed/172unknown,0knowndenials. PersonalGeminihumanreview/retentionrisk remainsunacceptedbyowner;consumeraccountdoesnotinheritWorkspace/APIprotections. No externalprojectdatatransmission.
-14independentsavedchecks passed0failed;nohistoricaltests/auditsrerun. Privatehash/headerdiagnostics:`data/vision/gemini_readonly_preflight_v1_20261016T165336458230Z/`;notuploadfiles. InitialsetuphelperstoppedatValidationextraVùngcolumnbeforeimagechecks;observedschemahandledwithoutsource/policymodification,failureevidencepreserved.172livepass1.309s,notbenchmark.

**Nextsingleengineeringrecommendation:** separatelyscopegenerated-onlylosslessJPEGmetadatasanitisation/non-identifyingICCpreservationqualification;noactualsourcesexported. Externalpermission/riskacceptance/actualpackaginguploadstillneedseparatedecisionsandapplicableevidence. OriginalfullRGBgeometry/colours/filenames/splitsandallTest/traininggatespreserved. No installs,training,commit/push.

## Current Vision restart — Gemini review preparation local-only, external release pending (2026-10-16)

Owner requested181held cases for Gemini review and explicitly required privacy/licence concerns flagged before external packaging. [Report and exact local batch paths](vision_gemini_review_preparation_v1.md), [aggregate verification](vision_gemini_review_preparation_evidence_v1.json). Owner confirmed **Personal Gemini web/app**, not managed Workspace/API. No data sent to Google/Gemini.

New ignored local preparation root: `data/vision/gingivitis/staging-16669f74665ff0deca6ddd25feb0d233e52fdc2313265465bf91731af1e8956b/gemini_review_preparation_v1_20261016T164212810635Z/`. **Master181.LOCAL_ONLYtracker covers52Training+129Validation** with pending/blank decisions, conflicts/group/split/source evidence. File is `master_tracking_181.LOCAL_ONLY.csv`; do not upload it, localplan or localmanifests.

Nine Training protectedTestaliases00271/00272/00273/00275/00566/00568/00570/00571/00572 remain localonly with nobatch. Other172records have12proposed10–15image batches:43Training15/14/14;129Validation15/15/15/14/14/14/14/14/14. Each has localmanifest,threeparsedcachedcaptionvariants/TXThistogram and exactproposedfilename/subrequestlists, not originalRGB/caption/TXTcopies. GeminiAppsdocumented10filelimit respected in proposed<=9images+1evidencetext requests; noZIPgalleryassumptions.

**8focusedgeneratedtests passed0failed/errors/skipped;59saved-artifactassertions passed**.344sourcepathstatchecks exist, nooriginalRGB/header/CSV/TXT/Testpayload read/copy. Four existingreviewartifacthashes unchanged. CSVauthored/inspectedwithbundledArtifactTool,independentlyroundtripped;firstverificationboolFalse/falsecomparison correctedwithoutdatachange.Originalsources/labels/splits/181holds/NP015/traininggates preserved; no install,training,commit/push.

External release isblocked before actualpackaging perownercondition:PersonalGemini retention/humanreview risk andpermitteduse mustbe acknowledged; qualifiedmetadata-safe fullresolutioncolour/filename route needed (privateEXIF/ICC cannot blindlystrip/copy;B1arraysnotGeminiimages). CCBY4.0confirmed,notblanketprivacy/clinicalapproval. Theaccountanswerdoesnotgrantnewclinical/manifest/automaticuploadapproval. Nextinput:permittedPersonalGeminiprocessing/privacyacknowledgment andnarrowmetadata/colourqualification scopefor172only,with9excluded. Donot promote anyAIopiniontoapprovedgrade orsilentlyexpand181uploads. Actualuploadfilescurrentlynone.

## Current PP1 restart — updated live demo and eight-step delivery pack (2026-10-16)

Owner requested finishing practical PP1 work without waiting for a doctor. [Delivery v3/runbook and truthful eight-step table](component2_pp1_delivery_v3.md), [current verification](component2_pp1_delivery_verification_v3.json). **Open http://127.0.0.1:8770/**. New loopback server; previous8768server preserved. Start `.venv/bin/python -B -m src.tabular.api --port 8770` if stopped. No installation, new training, real dental inference, external AI upload, dataset/label changes or Test rerun.

- New hash-pinned aggregate-only questionnaire evidence loader/endpoint/card shows all three frozen final models, cutoffs and limitations; same current model identity required, no raw data/evaluator calls. Historical model/API provenance preserved; footer now accurately distinguishes pending Vision/clinical work from completed Tabular final evaluation. Live fictional21.41%→cleaning7scenario24.41%→reset21.41%,12SHAProws unchanged.
- Saved Vision53Validation evidence/three examples/nineviews and five680OOFrows retained; arbitrary new-photo runtime remains disabled. No promise of across-grade reliability. MGI0whole-image support absent, Grade1OOFrecall0/12,181holds unchanged, NP015 unresolved; AI advice is unverified QA evidence, not clinical approval.
- **34 focused tests passed,0failed/errors/skipped**, **17 browser checks passed** and **33 independent artifact assertions passed**. No full-repository audit/test run. Desktop screenshots inspected; mobile no document overflow. Frozen core/model/manifest/Testresults/onceclaim and previous Vision evidence hashes match. Current frontend rebuilt using existing esbuild only; no dependency install/download.
- Eight steps have engineering deliverables but are **not all scientifically complete**: review preparation and MIO metadata complete; qualified review/externalMGI0eligibility/newapprovedmanifest/finalVisiontraining-protocol/Test and human feedback remain pending. Existing authorized provisional pilot/comparison evidence is reusable. Do not clear holds, change clinical grades, claim a final validated model or infer new training/Test permission from this delivery.

**Next single practical action:** owner rehearses the five-minute sequence on8770using the runbook. Real human feedback and qualified/source decisions must be obtained truthfully; blank feedback slots are not completed users. Independent engineering scope is complete for this delivery. Further new-photo inference, dataset expansion or new real training needs concrete scope and input/protocol checks; no automatic experiment follows. No commit/push.

Earlier8768rehearsal/historical pending wording below is preserved; v3supersedes current demonstration entrypoint and footer notes, not scientific results or dataset eligibility.

## Current Vision restart — review checklist and external MGI0 metadata checked (2026-10-16)

Owner authorized steps1–2 preparation, not new datasets/training/automatic clinical approval. [Action package with52IDs](vision_review_external_mgi0_action_package_v1.md), [14cached-artifactchecks/evidence](vision_review_external_mgi0_action_evidence_v1.json). Existing seven Training52 package-file hashes match; no repeat audit or source RGB/CSV/TXT/Test payload access. Queue2partial/45annotation/4companions/1NP015; all52 remain unapproved. Held129Validation separate; all181holds intact. Conditional41sources/33contentunits is not approved recovery.

MIO current official record/API confirms765reported images, diagnosticHealthy/Gingivitis/Periodontitis schema, open access/CC BY4.0. SANO.zip is433825820bytes, not downloaded. No whole-imageMGI0rubric, actual archive contents/privacy/participant grouping or comparable approved externalcohort established. Do not mapHealthy→MGI0 orPeriodontitis→MGI4. Record DOI22047269 differs fromdescription-requestedcitation21140854; preserveprovenance. Source/camera shortcut risk is methodological, not a proved cause of current errors.

Gemini/otherAI may help organize evidence; no authenticated dental qualification, clinical groundtruth or clearance. No external AI contacted,imagesuploaded or decisionsrecorded. Human/source-supported annotation/group decisions remain needed. Independent provisional demo work can proceed within prior scope; no data-policy/training gate bypass because time is short. Next: obtain a genuine qualified/source-supported route for52Trainingdecisions, or separately scope external annotation-evidence investigation. Steps3–7data/training/Test decisions remainpending; do not autonomously download/train/activate manifests. No install/commit/push.

## Current Tabular restart — one authorized final held-out evaluation complete (2026-10-16)

**Read [actual final Test results](tabular_final_test_results_v1.md), [aggregate metrics/intervals](tabular_final_test_results_v1.json), and [109 saved-evidence checks](tabular_final_test_verification_v1.json).** Owner separately approved numerical freeze against receipt `e08073b43e89ba99982483344e2612f577f46ae8ee0988b2458e5cfc2b8c6e0c`, then one final Test evaluation. Both genuine approval records are bound to current code/fresh output; freeze recorded first. The one-run permission is consumed. Do not rerun, remove the persistent claim, tune from Test, or repeat development preparation.

- Exact frozen 1,563 held-out participants: 388 reported Yes / 1,175 No. Full XGBoost A raw primary / full Logistic C1 raw comparator / development-rate baseline; no extra calibration. Frozen statistical cutoffs 0.26 / 0.28 / 0.50. These concern **previous gum-treatment history**, not current disease or clinically approved cutoffs.
- XGBoost actual AUROC **0.760654** (conditional95%CI0.733363–0.788940), trapezoidal PR-AUC0.552356, AP0.555094, Brier0.150858. At0.26: sensitivity0.559278/specificity0.835745; TN982/FP193/FN171/TP217. At0.50: TN1122/FP53/FN284/TP104.
- Logistic actual AUROC0.756113 (CI0.727886–0.783610), PR-AUC0.553807, AP0.554765, Brier0.151364. At0.28: sensitivity0.541237/specificity0.831489; TN977/FP198/FN178/TP210. Baseline AUROC0.5/AP0.248241/Brier0.186617. Its trapezoidal PR-AUC0.624120 is a constant/tied-score endpoint-interpolation artefact, not useful ranking ability.
- Paired XGBoost-minus-Logistic AUROC95%CI[-0.005623,0.013846]; Brier[-0.002098,0.001298]. No clear overall winner established, primary remains as frozen. Overall0.80AUROC target unmet. Do not substitute age60–80 subgroup AUROC0.801691 for overall performance.
- Joint descriptive calibration intercept/slope: XGBoost0.247322/1.244086, Logistic0.121330/1.118797; constantbaseline undefined. No mapping fitted or prediction altered; coefficient intervals not estimated. Predefined age/recorded-sex diagnostics and1,000 paired participant-bootstrap draws completed; zero undefined draws. Complex-survey variance, external/clinical transportability and development-selection uncertainty are not resolved by these conditional intervals.
- One actual run12.556s/228.70MiB peakRSS, two threads (not benchmark); instrumentation observed zero predictive/preprocessing fits and two descriptive calibration regressions. Four selective XPT returns each exactly1,563 authorized IDs. 109 independent saved-result assertions passed, maximum independent metric difference1.14e-8 within declared1e-7float32/float64 tolerance; zero new inference/refits during verification. Prior16generatedtests passed0failed/errors/skipped, reused unchanged rather than rerun.
- Private results/predictions: `data/tabular_final_test_results_v1_20261016T153805043162Z/`; owner/execution records: `data/tabular_final_test_execution_v1_20261016T153805043162Z/`. Persistent `data/tabular_final_test_once_v1/evaluation_claim.json` must remain. Actual result SHA`abcc52076b7073767f4f13907e9682f5da683bc9fc31fef5000351c4e13b391c`; private predictions SHA`bea8b43941366012e5886e314b075dd643376353089a08751b72d700530e3f8a`. Frozen models/receipt/manifest/history unchanged; original demo/model metadata untouched. No installs/cloud/commit/push.

**Questionnaire demo rehearsal completed:** [Tamil five-step guide](tabular_demo_rehearsal_v1.md), [actual browser/API evidence](tabular_demo_rehearsal_verification_v1.json). Live fictional profile21.41%→cleaning7scenario24.41%→exactreset21.41%;12SHAProws/additivity/units/warnings andeditinvalidation verified.17explicitAPI/numerical assertions passed0failed;5expected422rejections,0uncaughtpageerrors. No newpytest/scientificrun orsource/frontend/modelchanges. Historicalgenericfooter/APIrolewording does not yet reflect completedTabularfreeze/evaluation; guide explicitly distinguishes it from pendingVision/clinicalapprovals. Owner must rehearse aloud; no humanusabilityfeedbackinvented. **Next single safe task:** owner opens http://127.0.0.1:8768 and practices the five-step explanation using the guide. This completes the authorized final evaluation, not clinical validation or the entire project. Vision label/group approvals,181holds and absent whole-imageMGI0 remain separate. No new model search, Test retuning or real Vision training follows automatically.

The earlier preparation/readiness "approval pending/Test not run" records below and in historical reports are historical, superseded by the two explicit decisions and this actual completion. Preserve them; do not reinterpret them as permission to repeat.

## Current Tabular restart — six-fit preparation complete; numerical freeze review pending (2026-10-16)

Owner explicitly approved [decision package](tabular_finalisation_decision_package_v1.md). Exactly one preparation completed: **6Logisticfits,0newXGBoostfits**; scopeconsumed. [Actual results](tabular_freeze_preparation_results_v1.md), [aggregate/receipt](tabular_freeze_preparation_results_v1.json), [13tests/63artifactchecks/currenthashes](tabular_freeze_verification_v1.json). Do not repeat or infer finalTestpermission.

- XGBoostFullAraw remains primary candidate; existing savedmodel/OOFreused unchanged. LogisticFullC1raw comparator now has5original-foldOOF fits+1fulldevelopmentartifact. All10historicalmetrics/counts MATCH before6thfit. Trainingratebaseline1553/6251=.24844024956007038.12inputs/47encodedfeatures;noadditionalcalibration.
- Proposedglobalstatisticalcutoffs fromeachmodel's developmentOOF: **XGBoost.26;Logistic.28** usingexistingYoudenJ/grid/tie rule,notfoldmedian.25. XGBoostAUROC.739398/Brier.157268;Logistic.736721/.157823. Atselectedcutoffs apparentOOFsensitivity/specificity .545396/.806301 and .535093/.822052 respectively. SameOOFlabelsselectedcutoffs;these are optimistic apparentoperatingresults,notindependentvalidation orclinicalcutoffs.
- Localpreparedfolder `data/tabular_final_freeze_v1_20261016T143007292661Z/`:newLogisticmodel,pairedOOF,baseline,protocol,freeze receipt. ReceiptSHA `e08073b43e89ba99982483344e2612f577f46ae8ee0988b2458e5cfc2b8c6e0c`. Existingprimaryjoblib stays at `models/questionnaire_pp1_v1/model.joblib` (QuestionnairePrototype.model),originalmetadata/demo unchanged.
- Runtimeauditsobserved6Logisticfits andonlyallowedinputs;selectiveXPTloaderreturned6251developmentrowsperfile. Sharedheaders/SEQNlinkage scanned;noheld-outpredictor/outcomepayloadsdecoded. Actualfitmedians/scalermeansmatchedfittingrowsonly.13focusedtests/63independentartifactassertionspass;0verificationrefits.0.273s/210.03MiB,notabenchmark. NoTestevaluation,source/label/split/historychange,installs/cloud/commit/push.

**Next single action:** owner reviews/approves the exact numerical freeze receipt. Finalpaired1,563Testevaluation requires separateexplicitpermission afterfreeze; never infer it from this preparation approval. Keepmodel/calibration/threshold/protocolfixed beforeTest. Probability/thresholdoutputs meanreportedprevioustreatment,notcurrentdisease/futurehealth. Clinicaltransportability,complexsurveyuncertainty andconsentedusabilitylimitations remain;AUROC.80unmet. Noautomaticdeploymentor newmodelsearch.

Earlier decision-packagepending wording below is historical; do not rerun preparation to resume.

## Current restart — authorized nested experiment complete; qualified-review blocker (2026-10-16)

[Current progress v2](vision_autonomous_progress_v2.md), [actual nested results](vision_nested_feature_probe_results_v1.md), [resumable checkpoint](vision_autonomous_checkpoint_v1.json). Owner explicitly approved one95-fit cachedTraining680experiment after the initial safe-work milestone. It completed successfully; **the permission is consumed. Do not repeat it or launch another experiment automatically.**

- Actual nested-selected EfficientNet workflow:accuracy.522059(355/680),macro-F1.346429,balancedaccuracy.348645,QWK.300275,macroAUROC.716342,Brier.613977. Recalls0/12,27/84,96/223,232/361. VersusbalancedC1:Grade2correct22→27 and Brier.753383→.613977, but accuracy358→355 andGrade3/4recall declined. Grade1remains0/12. No across-grade reliability, calibrated probability or final-model claim.
- Exactly6fixed settings inside3innerfolds/5unchangedouterfolds:95Logisticfits;4outerfolds selectedbalancedC.01,onebalancedC.1. No full680deployment refit,encoder/image execution or neural optimizer steps. Only3hash-pinned existingcacheinputsopened; allotherVisiondatareadswereblocked. Runtime8.422s,peakRSS212.47MiB,twoCPUthreads.57independent actualsaved-result assertions passed with0refits.1000conditionalcontentbootstrapdraws,0undefined; priorselection/participantuncertainty remains.
- Held181review workflow remains52Training+129Validation, all pending,zero new labels/eligibility. Disjoint121partial(2/119),54otherreferrals(45/9),4companions,2NP015. Existing52package preserved. [Review handoff](vision_held_development_review_v2.md). The54near-pairhumanreview is already recorded; do not request its repetition.
- Current React/FastAPI [demo](http://127.0.0.1:8768):historical53Validationpilot50.94% and680OOF are separate;5OOFtable rows now include newnestedworkflow. NineexistingCAMviews/questionnaireSHAP/reset preserved; new-photo runtime inactive. Start `.venv/bin/python -B -m src.tabular.api --port 8768`. Earlier8766server untouched. [Current hashes/verification](vision_evidence_demo_verification_v2.json).
- Softwareverification:58unique selectedtests passed,0failed/errors/skipped;8directlyaffectedevidencetestsrerun afternewresult,not8additionalunique cases.9reviewartifact checks;12initialbrowser+3post-hint+5post-resultchecks passed.16historicalVisioncore/model/colour/trainerhashes unchanged. No fullrepositorytest or clinicalvalidation claim.

**Next single practical action:** obtain documented qualified annotation/group decisions for the existing52heldTrainingcases; use prepared evidence, never modelerrors as replacementlabels. Whole-imageMGI0absent,MGI1scarce,clinicalapproval/participantidentity/finalcohort/protocol unresolved. All181holds/NP015/Test/researchgates unchanged. No new data/labels/manifest activation, installs/downloads, cloud,commit/push. Safe authorized work is complete; further realtraining or data-policy changes require specific scope. No Colabhelp needed now.

Earlier pending95-fit plan statements in v1reports below are historical and superseded by this actualcompletion. Do not rank historical53Validationaccuracy directly against680TrainingOOF. Checkpoint is local continuity, not a background scheduler or automatic cross-session resumption.

## Current restart — cached EfficientNet class-weight comparison completed (2026-10-16)

Owner explicitly accepted the proposed cached balanced-versus-unweighted comparison. One five-fit run completed; its permission is consumed. [Actual report and remaining Vision tasks](vision_efficientnet_head_results_v1.md), [aggregate evidence](vision_efficientnet_head_results_v1.json), [prospective plan](vision_efficientnet_head_plan_v1.md).

- Exact same 680 Training records/labels/groups/folds and 1,280 cached EfficientNet features. Only class_weight changed to None; C=1/scaler/solver/seed unchanged. Five new fits; zero balanced refits, encoder/image access, downloads or installs. Only three old cache inputs opened; all other Vision data access blocked.
- Unweighted versus balanced: accuracy 0.532353 vs0.526471 (362 vs358 correct), macro-F1 0.337377 vs0.341037, balanced accuracy0.336938 vs0.340590, AUROC0.715040 vs0.711806, Brier0.750812 vs0.753383, QWK0.256634 vs0.267839. Grade2 correct22→19; Grade1 remains0/12. Majority361correct, only one fewer than unweighted.
- All five prespecified conditional paired intervals against balanced include zero. No clear winner, reliable probability improvement, learning-code bug or final model established. Do not optimize solely for the small accuracy gain; keep the trade-off evidence and avoid blind sweeps.
- 22 generated tests passed,0failed/errors/skipped;81 independent saved-result checks passed, including actual fold-local scaler means and hash/membership/baseline consistency. Runtime5.21s, peak RSS191.97MiB. Exact current code/protocol/cache bindings preserved.

Remaining Vision work: qualified label/group decisions and181holds(52Training/129Validation); missing whole-imageMGI0/scarceMGI1; approved frozen cohort/protocol/final scientific training and protected evaluation; approved new-photo runtime/Grad-CAM integration; PP1 usability/evidence/rehearsal. The54human near-pair decisions are already recorded, not awaiting repetition. NP015 remains unresolved. Existing model/trainer/Grad-CAM/code/demo and data preserved; no commit/push or final gate activation.

Next practical priority: obtain qualified review/group decisions and progress the explicitly provisional demo integration, not another automatic hyperparameter experiment. Earlier next-run suggestions below are historical.

## Current restart — same-fold EfficientNet comparison completed (2026-10-16)

Owner approved continuing the bounded comparison and separately approved official EfficientNet-B0 weights download. One local run completed; its permission is consumed. [Actual report](vision_efficientnet_probe_results_v1.md), [aggregate evidence](vision_efficientnet_probe_results_v1.json), [prospective plan](vision_efficientnet_probe_plan_v1.md).

- Same 680 Training IDs/provisional labels/content groups and exact five folds; 224×224 B1 inputs and normalization unchanged. New fixed EfficientNet ImageNet V1 encoder, 1,280 features; same fold-local C=1 balanced Logistic head. Five classifier + ten Dummy fits; zero neural optimizer steps. ResNet evidence reused, not rerun.
- EfficientNet versus ResNet: accuracy 0.526471 vs 0.475000; macro-F1 0.341037 vs 0.295114; balanced accuracy 0.340590 vs 0.293791; macro-AUROC 0.711806 vs 0.633569; Brier 0.753383 vs 0.831294; QWK 0.267839 vs 0.214752. Accuracy still below majority 0.530882, Brier worse than prior 0.595072; within-one accuracy worsens. Recalls 0/12,22/84,99/223,237/361.
- Conditional 1,000-draw paired macro-F1 difference CI vs ResNet [+0.000363,+0.092263] is borderline; balanced-accuracy [+0.003308,+0.091316], QWK [-0.047026,+0.161460]. No refit/participant/selection correction. Two fixed encoders compared, no final winner or clinical claim.
- 46 focused generated/regression tests passed, zero failed/errors/skipped (30 new +16 existing). 79 independent saved-result checks passed. Runtime 48.26s CPU/two threads, peak RSS 1130.66 MiB; no controlled speed benchmark claim.
- Exactly680Training model-array hashes verified/read; no53Validation/181held/NP015/Test/CAM payloads, original JPEG decoding, relabeling or new export. Frozen encoder/BatchNorm unchanged. Official TLS/filename SHA prefix and measured full hash bound before execution; no implicit downloads/retries.

No learning-code bug established. Representation choice improved several metrics under this setup; labels, resolution, imbalance and optimization are unproven explanations of remaining errors. Missing MGI0/scarceMGI1, qualified approvals and participant evidence remain unresolved. Existing demo/research trainer unchanged; no commit/push.

Next single recommendation: predeclare a cached-feature head-only comparison of balanced C=1 versus unweighted C=1 on the same folds, measuring calibration/discrimination/recall trade-offs. Not implemented/run or automatically approved by the consumed encoder-run scope. Do not start another real experiment without its scope.

## Current restart — actual Training-only frozen-feature probe completed (2026-10-16)

Owner explicitly approved the bounded 680-image probe and separately permitted one official ResNet50 V2 weights download. The new one-run authorization is consumed. Read [actual probe results](vision_frozen_feature_signal_results_v1.md) and [aggregate evidence](vision_frozen_feature_signal_results_v1.json). Earlier statements below that no real probe has run are historical.

- Exactly 680 Training arrays verified/read, support 12/84/223/361; no 53 Validation, 181 holds, NP015, CAM or Test payloads. Five unchanged seed-42 grouped folds; 544 fitting / 136 scoring per fold. Known content grouping does not prove participant independence.
- Fixed official ImageNet encoder and BatchNorm unchanged; five fold-local scaled/balanced Logistic Regression fits and ten Dummy fits; zero neural optimizer steps. CPU, two threads, 98.69 seconds, peak RSS 1125.09 MiB. Official weight SHA matches; no alternate weights, retry, cloud or additional experiment.
- Mixed result: macro-F1 0.295114 vs baseline 0.173391; balanced accuracy 0.293791 vs 0.250000; QWK 0.214752 vs 0. Accuracy is worse, 0.475000 vs 0.530882; Brier is worse than fold prior, 0.831294 vs 0.595072. Recalls: 0/12, 17/84, 73/223, 233/361. Limited within-source signal, no overall win/final model or clinical claim.
- 1,000 conditional paired group-bootstrap draws, no undefined draws; positive baseline-difference intervals omit refitting, unknown participant overlap and selection uncertainty. Historical 53-record pilot metrics are not directly comparable with these 680-record OOF scores.
- 65 saved-result assertions passed; independent reviewer metrics match. Prior 16 generated tests reused with unchanged code, not rerun. Initial ad-hoc probability-sum assertion was overstrict (1e-12); observed 1.76e-7 passes the existing 1e-6 metric tolerance. No probabilities or implementation were modified.

Next single recommendation: prepare a bounded EfficientNet-B0 fixed-feature comparison on these same 680 records/folds, with prospective settings and fresh execution scope. Not run or automatically approved. Label/group approvals, missing whole-image MGI 0, scarce MGI 1, all 181 holds and final research/Test gates remain unresolved. Existing demo is unchanged; no commit/push.

## Current restart — React/FastAPI and Mac generated Vision verified (2026-10-16)

Owner authorized necessary installations and autonomous local tabular/integration work. **Read [PP1 delivery v2](component2_pp1_delivery_v2.md) first.** This supersedes the prior "stdlib-only / torch unavailable" current-state statements without rewriting historical evidence.

- Working React19.2 + FastAPI local demo: `.venv/bin/python -B -m src.tabular.api`, http://127.0.0.1:8766. Existing verified XGBoost A / TreeSHAP / constrained What-if/reset reused. Fictional default21.41%, cleaning7 scenario24.41%, reset21.41%; 12 SHAP inputs. Nine saved v3 Vision views available separately.
- Owner-approved .venv installs: torch2.11.0, torchvision0.26.0, Pillow11.3.0, FastAPI0.143.2, uvicorn0.54.0. Mac MPS confirmed available; generated ResNet50 forward/Grad-CAM tests passed on CPU and MPS. No pretrained-weight download or real dental inference.
- Optional photo adapter and complete browser/API/generated-model flow verified. Default real runtime inactive; qualified ICC/identity orientation and explicit registered non-study inputs required. Ordinary arbitrary-phone-photo support is NOT established. [Adapter limits](vision_photo_adapter_verification_v1.md).
- [680-only frozen-feature probe implementation](vision_frozen_feature_probe_implementation_v1.md) ready; 16 focused generated tests pass. No real feature extraction/CV run, no new run authorization record. Keep53Validation/181holds/NP015/Test outside; fixed ImageNet encoder, fresh fold-local scaler/LR. Next real execution requires fresh scoped owner authorization, current hashes and an available official weights file; prior pilots consumed.
- Added [development-only subgroup reporting](tabular_subgroup_evidence_v1.md) and consolidated metrics from saved OOF evidence, no new model fits. Final model/calibration/threshold choices and untouched1563Test evaluation remain pending; survey-design/domain uncertainty still unfinished.
- **98 focused tests passed, zero failed/errors/skipped** (not full repository). Browser prediction/SHAP/reset/saved views/mobile/generated-photo tested and screenshots inspected. [Verification/hashes](component2_integration_verification_v2.json). All original research and held/Test boundaries preserved; no commit/push.

Current next human action: open local demo and rehearse it. No Colab help is needed now. Do not repeat completed audits or generated qualifications. The full scientific project is not complete: qualified labels, participant grouping, absentMGI0/scarceMGI1 and actual performance limits remain. Dirty/new files remain uncommitted.

## Next Vision experiment design — external advice assessed (2026-10-16)

Owner delegated routine technical recommendation choices. Selected [680-Training-only frozen-feature probe plan](vision_frozen_feature_signal_plan_v1.md), rather than blindly adopting new733-CV, deleting captions or repeating Grade2analysis. Cached metadata feasibility:680distinct known content groups,12/84/223/361grade support;proposed5folds544fit/136score,grade1 scoring3/2/2/2/3. No participant-independence inference. Use fixed official ImageNet encoder, never v2/v3dental-fine-tuned features for this CV;fit scaler/weights/classifier within each training fold. No images/feature extraction/model fit, activated folds, clinical approval or new real-run/cloud permission. **Next engineering task: separate synthetic-tested probe runner/handoff;current working demo below remains available.**

## Current restart — working questionnaire/SHAP/What-if demo; saved Vision evidence (2026-10-16)

Owner requested autonomous, efficient progress on both branches and deferred email contact. The current executable handoff is [Working PP1 demo](component2_pp1_working_demo_v1.md). Earlier restart sections below are historical; do not repeat their completed audits, qualifications or experiments.

- **Working local demonstration:** `src/tabular/local_demo.py` serves `http://127.0.0.1:8765`. Live 12-input questionnaire → previous-treatment probability → verified log-odds TreeSHAP → constrained smoking/cleaning What-if/reset. The separate Vision tab displays nine already saved v3 images for three examples; no new-photo inference or branch fusion. Exact launch command is in the handoff; no Colab needed to open it.
- **Actual new development experiment:** six prospectively fixed XGBoost settings, same 6,251 participants/five folds, 30 fold fits plus one reference fit. Historical A reproduced: AUROC 0.739398/Brier 0.157268. Balanced A reached 0.740041 but AUROC-difference interval includes zero and Brier worsened to 0.201243. No reliable improvement, final winner or 0.80 claim. Existing A remains the raw demonstration reference. All 6,251 OOF TreeSHAP rows passed additive/probability/native checks. [Results](tabular_pp1_completion_results_v1.md).
- **Further evidence without retraining:** [survey-weight point sensitivity](tabular_survey_sensitivity_v1.md) and [saved Vision conditional intervals](vision_saved_prediction_uncertainty_v1.md). Complex-survey variance, repeated selection and unverified image independence are not resolved by these calculations.
- **Verification:** 76 focused/directly affected regression tests passed, zero failures/skips; 15 browser checks passed. Local prediction+SHAP median 11.14 ms/p95 12.22 ms over 30 post-warmup fictional requests; not a production/usability benchmark. [Machine-readable verification](component2_local_demo_verification_v1.json).
- **Preserved boundaries:** 181 Vision holds/NP015/provisional labels, Test and questionnaire held-out payload isolation, original data, existing implementations/results and all research gates. Only ignored local model/OOF outputs and byte-identical copies of saved Vision previews created. No new Vision training, installs, cloud uploads, commits or pushes. Prior dirty work retained.

**Next single practical action:** owner opens the local demo, rehearses one explanation/What-if/reset and one saved Vision case. Full research is not complete: qualified labels/participant grouping, absent MGI0/scarce MGI1, weak Vision Grade2 recall, final tabular model/calibration/threshold freeze and untouched final evaluation remain. Do not automatically add held images, run another Vision experiment or advertise clinically validated performance. No email was sent; the clarification route is deferred, not replaced by invented approvals.

## Current restart — Training52recoverypackagecompleted;humanreviewpending (2026-10-15)

OwnerYESapprovedcachedrecoverypackage/researchonly;thenrestedandaskedforhuman/Colabhelponlywhenneeded. Newignored`training_recovery_review_v1_20261015/index.html`,52decisionCSV,121developmentpartialqueue,cachedTrainingQAand9artifactchecksPASS. All52pending;zerolabels/eligibilityapproved.52=2partialflags(01100/01101)+45otherQA+4companions+1NP015.11boundaryholdscannotreturnbylabelreviewalone;remaining41sourcesmapto33proposedcontentgroups,conditionalupperboundonlynotindependentparticipants. [Aggregatehandoff](vision_training52_recovery_package_v1.md),[UNSENTsourcerequestdrafts](vision_reviewer_source_requests_draft_v1.md). Nooriginalimages/annotations/Testlabels/modelread,nodata/manifestschanged,nonewtraining/Colab/commit/push.

MIOv2publicAPIlicenceCCBY4.0/openverified,butHealthy/Gingivitis/PeriodontitislabelsarenotMGI0–4. Nosuitableexternalwhole-imageMGI0cohortqualified. Nextneededhumanhelpisqualifiedannotation/sourcecustodian/supervisordecisionroute,notanother54-pairreview. NoColabneedednow. Noautomaticscience/clinicalapprovalortraining,includingseed43. Original5-gradearchitecture,independentNHANES,gatesandall181holdspreserved.

## Current restart — focused Grade-2 saved-prediction diagnosis complete (2026-10-15)

**Broader PP1 recommendation (2026-10-15; advice only):** owner requested research-backed dataset solutions. Verified181helddevelopment=52Training+129Validation,separate182Test;121developmentpartial-policycasesincludeonly2Training/119Validation. Prioritisecached52Traininghold-recoverydecisions and required qualified/source/group approvals,whilequestionnaireSHAP/What-if/demoimplementationcanprogressindependently. Optionalseed43replicationisastabilityproposal,notadatasetfix,andisnotapproved. No automaticrecovery/newdata/training. [Recovery/search recommendation](component2_pp1_dataset_recovery_recommendation_20261015.md). Priorworkwaspublishedin10commitsending`b4b2e5e`;newGrade2analysisandthisadvicearelocaluncommittedwork.



Read-only v2/v3 comparison confirmed identical53ValidationIDs/provisionallabels/gradeorder. Grade2v2→v3 transitions:2→2=1,2→3=10,2→4=1,4→4=1. Meanp2.368161→.194547;12/13decrease;Grade2top2coverage13/13→2/13. Precision12/45→1/1,recall12/13→1/13;overallnet+9correctfromGrades3/4gains. MosterrorshaveGrade2rank3/4,nottinymarginflips. No causal mechanismestablished. [Reviewerreport](vision_grade2_v2_v3_diagnostic_v1.md),[exactnumericrecord](vision_grade2_v2_v3_diagnostic_v1.json).

**ONE proposed next action:**ownerreviewofapredeclaredrun-seed43replicationwithallotherv3settingsandpinnedv2bestunchanged,toassesstrade-offstability;notalearning-rate/weight/thresholdfixorguarantee. Newrealexperimentrequiresfreshboundedapproval;notimplementedorrun. Nooriginalimages/checkpoints/Training/Test/181holdsopened,noexistingmetrics/labels/splitschanged,nocommit/push. Priorv1/v2/v3one-runpermissionsremainconsumed;qualified/finalresearchapprovalsunchanged.

## Current restart — ONE v3 real stage completed and verified (2026-10-15)

Owner's bounded v3authorization is **consumed**:5additional epochs,best5,on680Training/53Validation. Actual252199944-byte ZIP SHA c79f16cf59b268f86a5a4c4b6a3482636e374cb67629895f38e55dbb1eaf0d70;CRC/26payloadhashes/22sourcehashes,owner/protocol/initial-checkpoint/weights/manifest/runtime-proof/outputbindings and embeddedactual33/33qualificationverified. All53savedIDs/labelsmatchpinneddevelopmentmanifest;independentmetricsreproduceaccuracy27/53=.509434,macroF1=.325872,macroAUROC=.627264,Brier=.659312,MAE=.584906,kappa=.254985. MacroAUROCworsenedversusv2;grade2correct12/13→1/13,grade3 1/22→15/22,grade4 5/17→11/17. No validated success/final modelclaim.

Saved320tensorhashes:315unchanged,onlyapproved5changed;checkpointpayload/internalCRCchecked,butnolocaltensordeserialization.3CAMtripletsvalid,probabilitiesmatch,originalpreviewsbyte-identicaltov2. Measuredfit+CAM41.78685s/peakGPUallocated377.2285MiB. [Actualresults](vision_b1_lastblock_results_v3.md),[verification](vision_b1_lastblock_results_verification_v3.json). No newtestsortrainingduringreview;originaldatasets/labels/181holds/NP015/Test/five-grade/finalresearchgates preserved.

**Next single recommended task:** focused development-only grade2↔3/4erroranalysis fromexisting53probabilities/cachedannotationevidence,then predefine a further experiment ifneeded. Noautomaticextraepochs/retry;freshboundedownerauthorizationneededforanotherrealrun. Existingthreepilotrecordsremainhistorical;actualColabqualificationandstage-pendingnotesbelowaresuperseded. Clinical labels/participant independence and whole-imageMGI0support remain unresolved.

## Current restart — v3 actual Colab33/33 verified; ONE authorized stage next (2026-10-15)

Owner supplied actual generated-only v3 qualification:33passed/0failed/errors/skipped,all5backend cases,13.58s,TeslaT4. Verified4825-byte evidenceZIP SHA c580566ca9c9729415f48d90c5346f2acdb1b04e62773371aeff3dbe611a0d0f,CRC/5payloadhashes/33unique exactJUnitIDs/log/summary/22before-after-archive-current sourcehashes;[record](vision_b1_lastblock_runtime_verification_v3.json). No rerun or real images/training during review. Historical local5skips are resolved by this actual separate Colab run, not changed into passes retroactively.

**Next human action:** paste/run [the prepared single-stage cell](vision_b1_lastblock_run_colab_cell_v3.txt) in the SAME existing completed GPU runtime. Existing owner YES already authorizes ONE max5additional-epoch/patience2 final-bottleneck+head stage from pinned weighted-v2best;allBatchNorm/earlierlayers frozen. Reuse680/53B1data/checkpoint,no newdatasetupload orweightsdownload. Missing state/safetyfailure STOP,noautomaticretry/old-runreplay. **Actual v3 training/performance still pending.** Labels,181holds/NP015/protected/Test/five-grade research/final approvals unchanged. Earlier preparation/qualification-pending notes below are historical.

## Current restart — owner-approved v3 prepared; Colab qualification next (2026-10-15)

Owner YES approved the exact [last-bottleneck plan](vision_b1_last_block_plan_v3.md): generated qualification followed by ONE bounded additional stage from verified v2 best epoch1. New separate runner uses only final `layer4.2` convolution weights plus existing head; ALL BatchNorm affine/statistics and earlier tensors frozen; fresh Adam head0.001/block0.00001, seed42,batch16,max5additional epochs,patience2. Existing680/53/B1/objective/181holds/NP015/Test remain unchanged. Original five-grade research pipeline/gates and v1/v2 results preserved. Repeated Validation selection optimism remains.

[Current v3 handoff](vision_b1_lastblock_handoff_v3.md): local and fresh-code-extraction **28passed/0failed/errors/5backend skips**;22bundled payload hashes and33case IDs verified,oldv1's20/oldv2's19files unchanged. **No v3 Colab PASS or real training claimed.** Next human action: append [new verification cell](vision_b1_lastblock_verify_colab_cell_v3.txt) to the existing completed weighted-v2 GPU notebook;upload only [code ZIP](vision_b1_lastblock_code_v3.zip). Require actual33/33including all5backends before the separate already-authorized ONE stage cell. Reuse existing data/checkpoint;lost runtime STOP, no old-run replay or extra downloads/uploads. Owner decision/hashes truthfully recorded;clinical/labels/participant/final approvals still false. Historical pending statements below are superseded by this owner YES and preparation, not rewritten.

## Current restart — two real head-only pilots verified; next fine-tuning plan pending (2026-10-15)

**Latestactualweightedv2result:** ownercompleted3epochs,best1,on680Training/53Validation. Verified185389594-byteZIP SHAab9d61f3d59c807b9181e6937f1099364f3cc06dda6607745bdf5fc11cae8a82,25payloadhashes,19sourcehashes,owner/protocol/checkpoint/weights/runtimebindingsandembeddedactual27/27qualification. All53predictionIDs/labelsagreetohash-pinnedmanifest;independentprobability-basedmetricsreproduceaccuracy.339623(18/53),macroF1.229354,macroAUROC.670016,Brier.700495. Predictions0/45/1/7forgrades1–4;notasolvingclassifier,Brierworsethanunweighted.3CAMtripletsvalid. [Results](vision_b1_balanced_results_v2.md),[verification](vision_b1_balanced_results_verification_v2.json). **Nextsingledecision:prospectivelast-bottleneckstageplanv3** perproposal§3.3;notimplemented/activated/authorized. BothpreviousONE-runauthorizationsconsumed;noautomaticfurthertraining. [Exactplan](vision_b1_last_block_plan_v3.md). Historicalweighted-runtime/runpendingnotesbelowaresuperseded. Originalsources/labels/181holds/NP015/Test/five-grade/finalresearchgatesstayunchanged.

**Latest weighted qualification milestone:** owner ColabT4new27/27passed,0failed/errors/skipped,8.89s;all4weightedbackendchecks passed. Actual4375-byte evidenceZIP SHA c0f249b67b58f0c408579d02162f0c963dfba12cdad64ee2c83c433527180cda verified againstCRC/5payload hashes/27JUnitIDs/log/summary/19current+archive+before+after sourcehashes. [Record](vision_b1_balanced_runtime_verification_v2.json). **Next: execute the already owner-authorized ONE weighted run cell in SAMEruntime**,reuse existing733development bundle and officialcache. No further YES needed for exactscope;real weighted results still pending,no newtraining during evidence review. Earlier local4skips/qualification-pending notes are historical.

**Latest owner-approved next experiment:** YES received for implementing/qualifying and ONE Training-balanced comparison with the exact existing680/53,frozenResNet50/BN,seed42,batch16,lr.001,max5epochs/patience2. [New handoff](vision_b1_balanced_comparison_v2.md). New isolated runner/runtime/builder/tests and code-onlyZIP ready;fresh-isolation23passed/0failed/errors/4backend skips,19payload hashes and27case IDs verified;original20files unchanged. **Next human action: paste the new verification cell into the EXISTING Colab runtime,upload only the89KBweightedcode ZIP,and require27/27before its second authorized training cell.** No new approval needed within this exact scope;no real weighted results yet. Existing cache/data reused;lost runtime/cache STOP. No data packaging/downloads,Test,labels/splits or research gates changed. Historical pending-decision/checkpoint notes below are superseded by the actual owner evidence and YES.

**Latest checkpoint milestone:** owner completed read-only tensor inspection in Colab. Both bestepoch1/lastepoch3 show318officialbackbone tensors unchanged;headAdamsteps43/129 andall4row norms change. Original JSONSHA `b5526b6a662cb961352eb9210981ceb91a2c94e886dac88f854e78bfa6429de8` retained in [actual record](vision_b1_checkpoint_diagnostic_results_v1.md). No newimages,inference,training or downloads. No evidenceofnon-steppingoptimizer/accidentalbackboneupdateatthosecheckpoints;collapsecauseunproven. **Next pending owner decision: implement/verify andexecuteONETraining-balancedhead-onlycomparison withsamecohort/bounds;originalone-runpermissionconsumed.** Previous checkpoint-pending notes below are historical.

**Focused diagnosis now completed from existing aggregates/source:** no confirmed run-explaining mapping/normalization/optimizer defect;18new synthetic diagnosis tests pass. Training/Validation loss diverges;all53Validation argmax grade4. Additional Training-prior baselineBrier0.730868,versus modelreported0.688751. Current class_weight=none is consistent,but togglingbalanced alone in the old runner would be ignored;do not change it blindly. [Diagnosis/one-variable pending plan](vision_b1_prediction_collapse_diagnosis_v1.md),[aggregate evidence](vision_b1_prediction_collapse_diagnosis_v1.json). **Next human action: one read-only checkpoint cell in the still-existing completed Colab runtime**;helper compares savedbackbone/Adamsteps without images/inference/training/downloads. Actualtensorchecks remain unexecuted;lost runtime/cache STOPs. Further real training remains separately bounded and unapproved.

**Latest verified result:** owner completed the authorized real ColabT4 pilot.680Training/53Validation,3epochs,early-stopping bestepoch1. All53Validation predictions grade4;accuracy0.320755,macroF1=0.121429 (same majority classification),reported macroAUROC0.659734,Brier0.688751.3CAMtriplets generated. Actual185285944-byte resultZIP SHA4aa51bc52b3f313363dd88c3e56a299fb8c48a9c27f53bb1ae5114cf7f3181c4;18payloadhashes and20sourcehashes plus authorization/protocol bindings verified. No local tensor loading or rerun. [Actual results and limitations](vision_b1_exploratory_pilot_results_v1.md). **Next: focused collapse diagnosis and predefined next-comparison plan; no automatic additional training.** Historical preparation/permission-pending statements below describe earlier milestones and are superseded by this actual result. Original labels,181holds,NP015,Test,five-grade research/final approvals stay unchanged.

Latest owner YES supersedes the historical permission-pending notes below: **verified local B1 package + Colab CPU71/71 → explicitly authorised development-bundle Colab upload, official ResNet50V2 download and ONE max5epoch MGI1–4 head-only GPU pilot → actual evidence review**. Authorization is recorded truthfully in [owner record](vision_b1_pilot_owner_authorization_20261015.json). Use the [NEW execution notebook/instructions](vision_b1_authorized_gpu_pilot_v1.md), preserving the old disabled notebook and20verified source hashes. No cloud upload, weights download, GPU execution or dental training has occurred during preparation. The181holds,NP015,Test and all clinical/final-research gates remain unchanged.

- Strict development DRAFT remains680 Training +53 Validation candidates,181 holds; labels provisional, zero final qualified approvals. NP015/group/Test protections unchanged. Missing whole-image MGI0 and scarce MGI1 remain; duplicate review is completed, do not repeat it.
- Option A remains failed at Training/00004 (confirmed bounded-sRGB clipping, not established code bug). One consumed local attempt left incomplete output, no final ZIP. The later generated study passed34 tests but rescued0/6 failing cases. Frozen A limits and legacy guard stay unchanged.
- Owner approved **B1 as a generated-only candidate**, not real-data activation. New isolated matrix/TRC float32 prototype, bounded secure NPY loader, deterministic bilinear letterbox, unclipped ImageNet input and separate disclosed display preview: [contract/results](vision_option_b1_generated_prototype_v1.md), `src/vision/colour_b1_prototype.py`, `tests/test_colour_b1_prototype.py`.
- Original local B1 results75 passed/2 backend skips are now supplemented by **verified owner-run Colab77 passed,0 failures/errors/skips**. Both ResNet extended-float forward/Grad-CAM cases executed. Actual evidence `docs/vision_b1_runtime_evidence_v1.zip`, SHA256 `5e9b8f6e1e35f370455fc90250bd1fe2d8bcf5d7afa14317d487a218ddb06845`; eleven source hashes agree before/after,current code and archived manifest. CPU/Python3.13.16/torch2.11.0+cpu/torchvision0.26.0+cpu. No dental training. Preserve old preparation reports as historical snapshots; do not repeat completed77 tests.
- Separately versioned **generated-only full-resolution B1 v2** now qualified: [report](vision_b1_full_resolution_qualification_v2.md), [numeric evidence](vision_b1_full_resolution_evidence_v2.json), `src/vision/colour_b1_streaming.py`. New57 tests passed,0 failed/errors/skips. Sequential≤65536-pixel conversion and streamed NPY verification; two-row224 sampling. Generated4096×3072 canonical payload144MiB used57.046875MiB measured whole-process peak RSS (20.09375MiB increment over post-import high-water mark). No full-array/memmap, real decoder, dataset input or production integration. Original v1 remains unchanged/max256-side; v2 accepts fixed generated recipes only.
- B1 generated-only exporter/authorization/verifier integration now **48 passed,0 failed/errors/skipped**: [report](vision_b1_generated_export_integration_v1.md), [evidence](vision_b1_generated_export_evidence_v1.json), `src/vision/exploratory_bundle_b1.py`. Explicit separate generated B1 scope; actual synthetic680/53 selection,181 holds,NP015/protected/duplicate/Test checks and3 fixed CAMs;1469 payload files post-verified. No real DRAFT/inventory or source opened. Partial/publication failures cannot validate/retry. Prior77/57 suites reused, not rerun; all old code/limits/training gates unchanged.
- Owner now explicitly approved a **separate MGI1–4 exploratory configuration**: four logits, same680/53 provisional cohort, frozen ResNet50/BatchNorm, seed42,batch16,lr0.001,max5epochs,patience2. Original five definitions/logits and final proposal stay unchanged; MGI0/healthy detection unsupported. New runner's selected CPU backend checks now pass in actual Colab; no dental training/label approval has occurred.
- Header-only preflight completed: **0 compatible / 733 incompatible / 0 unknown under the original B1 parser**; 732 new development headers plus cached Training/00004 diagnosis. New732 share ICCv2/curv/no-chad/D65-media-white characteristics; no RGB decoding. [Coverage and support mismatches](vision_b1_real_source_compatibility_preflight_v1.md).
- Separately authorised **generated-only ICCv2 extension** now qualified: **65 new +30 directly affected existing tests passed; zero failures/errors/skips**. New explicit API supports the narrow D50-PCS matrix/curv single-gamma family, infers supported-white adaptation diagnostically and never adapts PCS colourants twice. Existing B1/Option A/exporters/trainer unchanged and no automatic real-use activation. [Contract, measurements and limitations](vision_b1_iccv2_qualification_v1.md).
- Current real B1 evidence: **733/733 hashes/headers compatible**, including00004; one profile family. Full generatedRGB8 cube16,777,216 codes under the actual supported ICC: max LittleCMS ΔE76=0.0000278802531, float32 XYZ=1.02664604e-7, Lab ΔE76=0.0000145837143, all existing B1 numerical bounds retained. New explicit adapter/export pathway; no Option A fallback or source/label/split changes. Prior ICCv2 qualification was not repeated.
- **ONE authorised real local attempt succeeded**:733 model NPYS+3full-resolution CAMs,737files; separate-process verifier and ZIP membership/hash/CRC PASS; all733 source hashes before/after match;181holds/NP015/protected/Test excluded. ZIP `data/vision/pp1_b1_dev_v1_20261015T085436527238Z.zip`,732575501bytes,SHA256 `a8a4f7f339c589f81335d7afb663f4cf62d30e217f65bc480683d0a770afed70`; manifestSHA `8e7ff195009a5e781c216795fd2a943db17a0b3ec8fd1c84760f3bf9878a4c9f`. Actual package peakRSS206.171875MiB,104.5753s. Local attempt consumed; no real retries. [Results/limitations](vision_b1_local_packaging_results_v1.md), [frozen export contract](vision_b1_local_export_contract_v1.md), [aggregate evidence](vision_b1_local_packaging_evidence_v1.json).
- **Actual owner Colab CPU verification now71passed,0failed/errors/skipped**,128.35s; all3four-grade backend cases passed. Downloaded ZIP5136bytes,SHA `8627aff3e7dfd744924aaa855661bf016e35043d407bdee99066bbb55384d11e`; original and docs copy match. Five evidence hashes,71unique JUnit names/log/summary and20before/after/current/code-ZIP source hashes verified. Python3.13.16,torch2.11.0+cpu,torchvision0.26.0+cpu;CUDA=False. RUN_PILOT=False,no dental-image access/training,no weights. [Verified actual evidence](vision_b1_pilot_runtime_results_v1.md), [aggregate](vision_b1_pilot_runtime_verification_v1.json). No rerun needed; the former local3skips are resolved by this distinct actual run, not rewritten historical results.
- **Owner scope now granted2026-10-15:** upload only the pinned733-source B1 bundle/3CAMs, official V2 weights access,ONE bounded four-grade GPU pilot. Fresh exact code/protocol/manifest/measured-weights bindings are enforced by the new execution notebook;7cell syntax and7authorization checks pass,20source files unchanged. **Next manual step: open the new notebook and select a free T4 GPU runtime.** Actual upload/download/GPU training not yet executed; no final clinical/label/participant/research approvals.

## Fixed research architecture and decisions

- **Vision:** RGB dental image → image-level maximum visible MGI grade **0–4** → class-specific Grad-CAM original/heatmap/overlay. Compare ResNet-50, EfficientNet-B0 and a majority baseline after data/protocol approval. Heatmaps are model attention, not clinical boundaries. Preserve colours, source files and grade definitions.
- Captions are the primary label evidence. TXT verifies annotations only, never model input or automatic clinical truth. Codes 0/1 are jaw ROI; codes 2–6 represent MGI 0–4. Missing, incomplete or conflicting evidence never becomes grade 0.
- **Questionnaire:** independent NHANES model → probability of self-reported **previous gum-disease treatment**, target OHQ850 → SHAP and controlled What-if. OHQ850 is a label, never a predictor. What-if changes only smoking status/interdental-cleaning days; it illustrates model sensitivity, not causal benefit or forecasting.
- No patient-level fusion, combined score, current-periodontitis diagnosis, future progression or clinical accuracy claims. Feasibility targets are not achieved results or guarantees.
- Protect final Test data from fitting, tuning, calibration, early stopping and model selection. Test-containing image groups need approved protection; identity cannot be inferred from similar photographs. Proposal §3.5 requires overlap to be resolved through an approved frozen participant-grouped split.

## Completed, with evidence

| Area | Verified/documented status | Read next only when relevant |
|---|---|---|
| Vision dataset | 1,096 extracted RGB images; published 732/182/182 memberships preserved; integrity and annotation QA complete | [Integrity audit](vision_dataset_integrity_audit.md), [caption QA](vision_caption_label_qa.md) |
| Caption policy | Strict default plus optional upper-partial check implemented; 274 candidates, no approval or clearance | [Policy check](vision_incomplete_policy_check.md), `src/vision/verify_caption_labels.py` |
| Content QA / human review | 14 exact pairs; 54 near candidates/11 cross-split; 40 review components. Owner reviewed all 54: 47 distinct, six visually same, one uncertain; no group activation | [Grouping](vision_content_grouping_v1.md), [original review artifacts](vision_near_duplicate_review_v1.md), [current human review record](vision_near_duplicate_human_review_v1.md), `src/vision/content_groups.py` |
| PROPOSED reconciliation v2 | Exact groups + six human-same edges → 1,076 content groups, eight actual cross-split groups; NP015 unresolved. Reservation scenario 714/182/180; IF both NP015 groups held 713/181/180. Not clinical eligibility or activated manifest | [Versioned reconciliation/manifest plan](vision_content_reconciliation_plan_v2.md) |
| Models/Grad-CAM | RGB preprocessing, ResNet-50/EfficientNet-B0 factories and class-specific aligned outputs implemented | [Model doc](vision_model_pipeline.md), `src/vision/model_pipeline.py` |
| Trainer | Seeds, freezing/BN modes, validation metrics, early stopping, checkpoints/resume and external approval gates implemented | [Scaffold](vision_training_scaffold.md), `src/vision/train_pipeline.py` |
| Owner-run Colab v1 | 6 backend + 2 architecture Grad-CAM cases = **8 passed**, zero failed/errors/skipped | [Runtime record](vision_runtime_verification_results.md), `vision_runtime_evidence.zip` |
| Owner-run Colab v2 | 7 trainer backend + 44 guards/metrics = **51 passed**, zero failed/errors/skipped; before/after hashes unchanged | Same runtime record, `vision_training_runtime_evidence_v2.zip` |
| NHANES audit/preprocessing | 7,817 valid audited labels; three OHQ870=9 exclusions → 7,814 cleaned; frozen **6,251 development / 1,563 held-out**; 12 inputs/47 encoded columns | [Audit](nhanes_audit.md), [preprocessing](tabular_preprocessing.md), [rules](tabular_preprocessing_rules.md) |
| Tabular development | Dummy/Logistic baseline, 12-setting Logistic comparison, eight XGBoost settings, eight nested raw/sigmoid calibration/threshold workflows documented | [Baseline](tabular_baseline.md), [Logistic](tabular_logistic_comparison.md), [XGBoost](tabular_xgboost_comparison.md), [calibration](tabular_calibration_threshold_results.md) |

The **59 selected Colab passes across two workflows** verify synthetic CPU plumbing, not the whole repository or learned dental performance. Runtime: Python 3.13.16, torch 2.11.0+cpu, torchvision 0.26.0+cpu, NumPy 2.1.3, Pillow 11.3.0, pytest 8.4.2. Actual architectures used weights=None; no pretrained downloads or dental training/inference. Both ZIPs are in docs/; untouched originals remain in Downloads. Read the existing verified record rather than rerunning unchanged tests.

Tabular baseline Logistic OOF AUROC 0.736721/Brier 0.157823 was reproduced. Example full XGBoost A OOF AUROC 0.739398 is an internal comparison, not a final winner or AUROC 0.80 achievement. Selection optimism remains; lowest calibration-workflow Brier is provisional probability-error ranking only. Youden cutoffs are statistical demonstrations, not clinical/deployment thresholds. Preserve selective development-only XPT loading and audited zero-decoding repair; never rerun preprocessing or load held-out payloads merely to resume context.

## Pending research approvals and work

- **54 owner decisions now mapped:** 47 distinct, six visually_same_content, one uncertain (NP015/RC014, possible participant overlap not verified). Latest evidence is `review_pairs_reviewed_v1_20261014.csv` plus provenance JSON in the existing ignored review directory. Original `review_pairs.csv` retains the historical all-pending snapshot. Fourteen exact pairs and six human visually-same decisions are different evidence units, not 20 independent exact groups; no clinical label/split placement approval follows automatically.
- **274 incomplete-caption candidates unapproved; 339 QA records uncleared.** These overlap and must not be added as independent exclusions. Qualified annotation adjudication includes exact-group conflicts and the historical 48 referrals; uncertain cases remain needs_review.
- Image-level MGI 0 support is absent; MGI 1 is scarce in existing provisional evidence. Neither is a final approved class distribution. Do not fabricate examples, silently switch to four classes or claim valid five-class learning/evaluation; supervisor must resolve feasibility.
- Participant identifiers/independence, representative rules, label-blind group placement, final label provenance and a frozen eligibility/split manifest remain unapproved. Hash/visual groups alone do not prove different participants. Current trainer requires verified participant IDs and external approval evidence; do not bypass its gate with synthetic IDs or blanket approval callbacks.
- Actual dental-image training, model comparison/calibration, final scientific evaluation and real-image explanation validation have not started. Exact training/augmentation/weight provenance protocol requires separate approval.
- NHANES final candidate/protocol/threshold freeze, held-out evaluation, survey sensitivity, SHAP and controlled What-if remain future work according to current reports. Do not infer implementation completion from proposal requirements. Separate development work can be authorised while Vision review waits.

## Historical restart: reviewed-content grouping approvals

**Human visual review → approved labels/groups/manifest → authorised actual Vision training.** Do not skip the approval stages. Owner makes review decisions; assistant may present comparisons and record only explicitly confirmed findings with reviewer identity, date, notes and pair/source provenance. Human content decisions do not approve clinical grades, participant identity or splits.

Reuse the existing ignored directory:

`data/vision/gingivitis/staging-16669f74665ff0deca6ddd25feb0d233e52fdc2313265465bf91731af1e8956b/near_duplicate_review_v1/`

Owner has confirmed all 54 in exact viewer order, including the first two distinct photographs. **Do not repeat the 54-pair review.** Use `review_pairs_reviewed_v1_20261014.csv` as the current human record and its provenance JSON; `index.html`/`review_pairs.csv` remain original source snapshots. The unresolved pair is **NP015: Validation/00736.jpg ↔ Training/00591.jpg**, RC014, uncertain with possible participant overlap. Next work requires owner/supervisor direction on this uncertainty and qualified group/label/manifest approvals. The confirmed cross-split review order was:

`NP005, NP007, NP015, NP023, NP025, NP030, NP033, NP034, NP036, NP044, NP048`.

Show one pair at a time without grades/outcomes. Ask the owner for `visually_same_content`, `distinct` or `uncertain`; retain `pending` without a decision. Do not treat low dHash, shared component membership, different camera angle or apparent same mouth as confirmed content/participant identity. Preserve exact aliases. Do not auto-merge, relabel, move/delete originals, alter splits or exclude components. Any alternative exclusion/group policy needs explicit supervisor approval before activation. Review of 11 cross-split pairs alone does not grant training readiness.

## Working preferences and preservation

Speak in simple conversational Tamil; one practical step at a time. Owner instruction: if a different assistant model/reasoning level becomes necessary, save progress and pause; request the exact model/level and resume after the owner switches. Do not routinely ask for model changes. Before meaningful work explain WHAT, WHY, HOW; show actual evidence and explain completed versus pending. Help the owner understand and defend work; never fill owner understanding or human/clinical decisions by assumption. Keep factual AI logs concise and accurate.

Only branch `vinuthan`. Preserve teammate files, datasets, existing tracked changes and untracked work. No commits/pushes, destructive Git operations, installs or downloads unless separately authorised. Never commit data/, .venv, model weights or private data. No broad audits/refactoring, repeated extraction/hash/QA or completed Colab reruns. Reuse code/evidence/dependencies; read only task-relevant files. Current root instructions' old setup/calendar steps are history, not a reason to redo completed work. Obtain explicit approval for clinical/review/policy decisions.

Current HEAD at handoff: `fe52e01`; substantial completed implementations/reports are **local uncommitted files**. Remote cloning does not reproduce this workspace. This handoff is also saved locally, not committed/pushed; it supports future sessions in this checkout and does not imply global memory outside the project. Do not advance automatically from recorded content decisions to group merges, label/split approval, manifest activation or training; wait for explicit next instructions and required scientific approvals.


## Current Vision restart — AI-assisted visual screen of held development images (2026-10-16)

Report: [vision_ai_assisted_visual_review_172_v1.md](vision_ai_assisted_visual_review_172_v1.md). Local per-image CSV: `data/vision/gingivitis/staging-16669f74665ff0deca6ddd25feb0d233e52fdc2313265465bf91731af1e8956b/ai_assist_visual_review_v1_20261016/ai_assisted_visual_review_172_v1.LOCAL_ONLY.csv`; 43 contact sheets are in the adjacent `contact_sheets/` directory.

Screened 172 non-Test held records (43 Training +129 Validation); the nine protected Test aliases and sealed Test payloads were excluded. Rechecked image/TXT hashes:172/172 each matched. Caption evidence gives 166 pending candidates (Training 42, Validation 124) and 6 unresolved; MGI0 remains 0, MGI1 has one Validation candidate, and MGI2 has seven candidates. No visual grade was suggested because reduced, uncalibrated contact sheets cannot support clinical MGI adjudication. All 172 remain `needs_qualified_dental_review`; no labels, split, holds, or sources changed. Flags:121 partial-caption patterns,16 caption/TXT histogram conflicts,12 annotation-count reviews,4 exact repeated TXT rows. These categories overlap; report gives details.

Next: qualified dental/annotation review must record reviewer credentials, date, evidence and decision. Supervisor decision is separately needed before any partial-caption policy or manifest change. No training/upload/commit/push.

## Current review continuation — Training/00052

The held-image triage includes focused read-only comparisons of all14 explicit histogram-conflict cases in [the case report](vision_training52_evidence_triage_v1.md); none were cleared or relabeled. In the separate tooth-count queue, `00060`, `00085`, `00484`, and `00537` each have12 captioned positions but13 TXT tooth boxes; `00557` has12 captioned positions but11 TXT tooth boxes. `00484` also shows apparent hard seams at image edges; cause is unknown, so it remains an image-integrity review flag. `00537` has a broader caption/TXT histogram mismatch despite matching maximum grade. `00557` has one fewer TXT tooth box and one fewer MGI-3 box than its captions; both maxima are 4. `00568` has one additional TXT tooth box/MGI-4 count and remains in its protected cross-split content-group hold; only the Training alias was inspected. `00602` has12 captioned positions versus13 TXT boxes, with one extra MGI-3 box. All cases remain pending/held. `00657` also has12 captioned positions versus13 TXT boxes, with one extra MGI-3 count. `00667` also has12 captioned positions versus13 TXT boxes, with one extra MGI-3 count. `00673` has12 captioned positions versus11 TXT boxes, with one fewer MGI-2 count. `00676` has12 captioned positions versus11 TXT boxes, with one fewer MGI-3 count. `00702` has12 captioned positions versus13 TXT boxes, one extra MGI-3 count. The current 12-ID tooth-count review queue is complete; all cases remain pending/held pending qualified review. `00162` remains unresolved: captions have 12 positioned MGI-3 sites plus unlocated non-inflamed/MGI1/2/4 counts, while TXT has12 MGI-3 boxes. No max grade assigned. Next: continue the duplicate/group cases one Training alias at a time, never opening protected Test companions. Training/00271 and `00272` have within-record caption/TXT histogram agreement but remain held due to protected cross-split grouping and unapproved labels. `00272` counts are MGI0–4 0/2/2/5/3. Training/00273 also has within-record caption/TXT agreement (MGI0–4 0/1/3/4/4) but remains held in its Test-crossing group. Training/00275 also has within-record caption/TXT agreement (MGI0–4 3/2/4/3/0) but remains held in its protected Test-crossing group. Training/00562 has within-record caption/TXT agreement (MGI0–4 0/0/2/4/6) but remains pending in a multi-image Training group. Next: Training/00564. No Test access, training, label change, or split change.
