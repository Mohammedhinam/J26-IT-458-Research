# Focused B1 prediction-collapse diagnosis v1

2026-10-15 · branch vinuthan · no new real-image processing/training/inference.
Reuse: verified owner-run resultZIP, cached bundle manifest fields only, unchanged runner/preprocessing/factory and relevant tests. This is not another dataset audit. Original source JPEGs, NPY image payloads, Test data and checkpoint tensors were not opened locally.

## Findings and confidence

|Check|Verified finding|Limit|
|---|---|---|
|Output/label order|Original grades1,2,3,4→training indices0,1,2,3→reported grades+1. Exactly4logits; no MGI0 fabrication.|Source-path review; no new individual-label adjudication.|
|Input loading|Float32 HWC canonical array→one ImageNet mean/std normalization→CHW→torch.float32; no /255 again or BGR swap in the runner.|Actual runtime input tensors were not saved; no real arrays inspected now.|
|Geometry|Cached manifest:678Training+53Validation use[0,37,224,150];2Training use[0,37,224,149]. Zero-normalized mean-colour padding.|Same defined policy across splits; this does not prove absence of domain shift.|
|Loss/optimizer|Unweighted CE sum divided by actual batch length before backward,Adam head-only; zero_grad/backward/step present. Validation eval/no_grad.|Historical class_weight=none,so no weighting bug in this run. Changing config to balanced alone would NOT weight this runner; its criterion currently ignores that field.|
|Learning curves|Training loss1.069945→0.984904→0.940768;Validation1.173950→1.204403→1.226434.|Consistent with poor generalization/overfitting,not a proved mechanism.|
|Training argmax counts|Online counts per epoch:11/1/10/658,0/1/62/617,0/2/99/579.|These are accumulated during updates,not a final-checkpoint Training evaluation.|
|Validation argmax|0/0/0/53 at every epoch; best1/tie-based patience2 stop at3.|Confirmed majority-like classification at argmax; cause remains unresolved.|
|Support shift|Training12/84/223/361 versus Validation1/13/22/17;Training majority53.09%,Validation majority32.08%.|A plausible contributor,not proof that imbalance alone caused the collapse.|
|Frozen backbone/BN|Source and earlier synthetic tests enforce freezing.|Actual saved-tensor comparison against official weights still pending; prepared read-only Colab helper.|

**No confirmed implementation defect explaining this run was established.** Also,no evidence supports declaring colour conversion a failure or silently switching/clipping B1. Data quality/provisional labels,small sample,scarce1,frozen ImageNet features and input-domain differences remain limitations/hypotheses.

Torchvision V2's official inference recipe is resize232→centre crop224 plus ImageNet mean/std. Our approved B1 deliberately uses224letterbox and extended floats; matching normalization does not mean identical pretrained input distribution. This is a recorded design difference,not a verified bug. Do not modify it together with weighting in a one-variable comparison. [Official Torchvision0.26 recipe](https://docs.pytorch.org/vision/0.26/models/generated/torchvision.models.resnet50.html).

## Additional Training-only probability reference

Existing hard majority evidence stays unchanged. A post-hoc descriptive reference assigns every Validation case the four Training proportions;no labels/protocol/thresholds trained or changed.

|Probability baseline|AUROC|Brier|Macro-F1|
|---|---:|---:|---:|
|Historical one-hot majority|0.500000|1.358491|0.121429|
|Training-proportion reference|0.500000|0.730868|0.121429|
|Best epoch1 measured runner|0.659734|0.688751|0.121429|

Training priors:[0.0176470588,0.1235294118,0.3279411765,0.5308823529]. The additional reference's Brier was computed from counts/probabilities and independently scalar-tested. Original model AUROC/Brier remain reported runner values,not recomputed without per-image probabilities. Probability ordering carries some signal,while current argmax outputs remain unusable for distinguishing four grades. One provisional MGI1Validation record makes its AUROC particularly unstable.

## Next read-only checkpoint check — prepared, not yet executed

New helper: `src/vision/diagnose_b1_pilot_v1.py`.
Copy the complete cell from `docs/vision_b1_checkpoint_readonly_colab_v1.txt` into ONE new code cell at the bottom of the original completed Colab notebook. Upload only the helper.py when requested. Do NOT rerun training or reset/reconnect a lost runtime. If the original runtime or verified official cache is gone,the cell STOPs;no automatic download/install.

It verifies pinned result-index/checkpoint/source/official-weight hashes;loads best/last with torch.load(weights_only=True,map_location=cpu);checks schema/protocol/context;compares every non-head tensor against the existing official cache;checks exactly2Adam states and expected43/129steps;reports four row norms/biases as numerical diagnostics. No model construction,forward pass,images,Test,training,downloads or modifications to checkpoint/cache. Numeric head/bias differences alone do not establish causal explanations. Initial-head snapshot was not saved.

Returns `pp1_b1_checkpoint_diagnostic_v1.json` for inspection. **Real checkpoint tensor checks have NOT been run locally.** No local torch installation was performed.18focused synthetic aggregate/guard tests passed,0failed,0skipped;new cell compiles;20historical code hashes unchanged. The checkpoint backend needs actual Colab execution and must not be called validated from these18tests.

## Proposed next controlled experiment — PENDING, not implemented/activated

After checkpoint evidence is reconciled,propose ONE Training-derived balanced-loss head-only run,fresh initialization matching baseline seed42,officialV2weights,identical680/53membership,letterbox/B1,lr.001,batch16,max5epochs,patience2,frozenBN/backbone,no augmentation/sampling/unfreezing changes. Reuse historical unweighted reference;do not rerun it unnecessarily.

Weights from existing trainer formula N/(K*n):grades1..4→14.1666667,2.0238095,0.7623318,0.4709141. No Validation-derived weight tuning,caps or invented support. Implement the loss explicitly in a new version:current runner ignores config.class_weight. Use weighted mean normalization by batch target-weight sum;report separate unweighted CE for comparable losses. [PyTorch2.11 weighted CrossEntropyLoss definition](https://docs.pytorch.org/docs/2.11/generated/torch.nn.CrossEntropyLoss.html). Class weighting is supported as a first imbalance approach by AGENTS§4;this exact further experiment still requires a separately scoped owner execution decision because the first ONE-run permission was consumed.

Required tests before executing:all-one weights recover original loss;hand-calculated weighted numerator/denominator;Training-only weight provenance;four-grade order;no missing-grade fabrication;frozen/backbone/BN andactual weighted-head optimizer check;strict owner/code/protocol/weights/bundle bindings;no181holds/NP015/Test;save per-record Validation probabilities/IDs only in ignored result storage for metric reconciliation. No metric target guarantees. This is one-variable hypothesis testing,not an automatic improvement or final model selection.

Report macroF1,per-grade recall,confusion/prediction counts,AUROC,Brier,MAE,kappa andclass supports even if worse;no posthoc threshold change or furtherautomatic search. Preserve original majority/unweighted results andprovisional warnings. Repeated Validation selection is optimistic;finalTest stays sealed. Class1weight14.17 may increase instability/overfitting with only12Training/1Validation;success cannot be promised.

## Three lines to understand / viva

- `GRADES.index(provisional_mgi_grade)` maps original grades1–4 into indices0–3 without changing clinical grades.
- `((extended-MEAN)/STD).transpose(2,0,1)` does one normalization and changes layout;it does not clip,divide by255 again or swap RGB.
- `(loss/len(target)).backward()` is correct mean gradient for the CURRENT unweighted summed loss;future weighted CE needsits correct target-weight denominator.

Viva:**Why not just train more epochs?** Training loss குறைந்தாலும் Validation loss உயர்ந்துள்ளது. முதலில் imbalance மற்றும் saved weights checks-ஐ பிரித்து பார்க்க வேண்டும்;epochs அதிகரித்தால் நல்ல generalization உறுதி கிடையாது.

**Provisional labels; non-clinical; non-final; participant independence unverified.** No label/split/approval/source modifications,real-image processing,training,inference,install/download,commit or push in this task.
