# Matched EfficientNet adaptation — actual result

17 October 2026 · Mac MPS · **Ten fits and50epochs completed. Summary recovered from saved predictions without retraining.**

> Provisional labels; non-clinical; non-final; participant independence unverified.

## Outcome

The final-block arm made a small improvement over its matched head-only neural control: accuracy46.32%→46.76% and macro-F1.336195→.341579. This is **not a successful overall accuracy fix**. Neither arm beat the saved52.21%nestedLogistichead workflow or53.09%majority accuracy on the same680records. No final-model or deployment change follows.

The owner explicitly approved the exact prospective10-fit plan in the current chat: “so fix panuu all persmion i alowed do it i will see good news”. The actual owner text, configuration, original planSHA, code/dependency/weights/manifest/fold/qualification bindings and fresh output are recorded in the ignored protocol. This approval is engineering permission, not clinical label or final research approval.

## What actually trained

- Same original680Training records; same five known-content-group outerfolds, each544fitting/136scoring. No53Validation,181held,NP015 or Test payloads.
- Existing224×224B1arrays and normalization, unchanged provisional MGI1–4 labels/support12/84/223/361. No source JPEG/CSV/TXT access or derivative regeneration.
- Fresh officialImageNetEfficientNetB0starting weights and identical new four-output head for each arm/fold. Exact cachedweightsSHA `7f5810bc96def8f7552d5b7e68d53c4786f81167d28291b21c0d90e1fca14934`; no downloads.
- ArmA: classifier head only,5,124parameters. ArmB: same head plus `features.8.0.weight`,414,724parameters total. This final feature block is a pointwise convolution; earlier MBConvblocks stayed frozen.
- Both arms used matching initial state and shuffle, classifier dropout, frozen backbone stochastic depth and everyBatchNormparameter/statistic. AdamW, headLR.001/blockLR.00001, weightdecay.0001, fitting-foldbalancedCE, batch16, exactly5epochs. No scheduler/augmentation/earlystopping/seedsearch.
- Exactly10real fits; only final-epoch scoring; one OOFprediction per record per arm. No final680refit or demo-model replacement.

## Same-cohort outcomes

| Workflow | Correct/680 | Accuracy | Macro-F1 | Balanced accuracy | QWK | Macro AUROC | Multiclass Brier↓ | Ordinal MAE↓ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| New head-only neural control |315|46.3235%|.336195|.354505|.246274|.687111|.634550|.697059|
| New final-block+head |318|46.7647%|.341579|.361579|.251915|.688420|.634081|.692647|
| Historical nestedEfficientNetfeatures+LR |355|52.2059%|.346429|.348645|.300275|.716342|.613977|.601471|
| Historical fold-majority |361|53.0882%|.173391|.250000|.000000|.500000|.938235|.627941|

The two new neural arms are the matched test of final-block adaptation. HistoricalLRdiffers in head/scaling/selection/training procedure, so do not attribute that entire gap to unfreezing. Historical53ValidationResNetresults are a different population and are not ranked in this table.

Primary paired difference, ArmBminusArmA: macro-F1 **+.005384**. Accuracy difference **+.004412** = **+0.4412percentage points**, net3additionalcorrect records. These point differences do not establish statistical significance or clinical reliability; no refit/participant-adjusted interval was produced for this trial.

| Provisional grade | Support | Head-only correct/recall | Final-block correct/recall |
|---|---:|---|---|
|1|12|1/12=8.33%|1/12=8.33%|
|2|84|31/84=36.90%|33/84=39.29%|
|3|223|106/223=47.53%|107/223=47.98%|
|4|361|177/361=49.03%|177/361=49.03%|

Compared with the historicalnestedhead's27/84Grade2correct, the new final-block arm has33/84, but Grade4falls232/361→177/361. This is a class trade-off, not overall recovery. Grade1remains very weak and no whole-imageMGI0support exists. Five fixed epochs and one pointwise block do not exhaust all plausible adaptation methods; they define only this completed bounded experiment.

## Reporting error and repair

All10fit checkpoints and finalOOFpredictions had been saved when the original runner attempted to build the summary. It asked for metric key `brier`, while the shared metric implementation returns `multiclass_brier`. That raised `KeyError` **after training and prediction completed**. The initial26generatedtests covered fitting/guards but missed this reporting-schema boundary.

- Original `FAILED.json`, persistent one-attempt claim, exact executed source and original test snapshot are preserved in the ignored output.
- The runner's reporting block now uses a small `metric_differences` helper with the actual schema, plus a regression test exercising real shared-metric output.
- `recovered_results.json` and `POSTPROCESSING_COMPLETE.json` explicitly identify postprocessing recovery. No `COMPLETE.json` was fabricated for the failed original entry point.
- Recovery read savedOOFpredictions and the10fit receipts only: **zero new fits, zero inference, zero changed predictions**. Numerical results retain original execution bindings; current reporting-patchSHA is separate.
- Original elapsed-training-time and peak-process-RSS fields were not saved before the exception. They are **null**, not estimated from timestamps or another run. Backend wasMPS; no CPUfallback was enabled.

This fixes the report-generation defect; it is not presented as a learned-accuracy improvement.

## Verification and saved artifacts

- Before real fitting:26focused generated tests passed and actualEfficientNetMPSgeneratedforward/backward checks passed for both arms. Independent source/architecture review found no blocker. [Original qualification](vision_efficientnet_adaptation_qualification_v1.json).
- Final reporting-fixed source: **27generatedtests passed,0failed** (1.63s). Historical26pre-runpasses are a prior version, not26additionalunique tests. An intermediate new regression test ran before its helper was added and failed withAttributeError; the complete current suite passed after implementation, without changing the expectation.
- **135independent saved-output assertions passed,0failed**; maximum independently recomputed sklearnmetric difference1.11e-16. All10checkpoints were deserialized onCPU:360tensorhashes each matched receipts and independently reconstructed official initialization;358frozenstates in head-only and357in final-block remained unchanged. [Exact verification](vision_efficientnet_adaptation_verification_v1.json).
- Instrumented model-array loader observed680calls/680unique pinnedTrainingpaths only. This is a loader audit, not an independent OSfile-read trace.
- SavedOOFmembership/folds, source/weights binding, ten5epoch histories, matching initial/order hashes and checkpoint tensor preservation were checked independently, without refitting or inference. See exact completed checks in the verificationJSON.
- Public aggregate: [results JSON](vision_efficientnet_adaptation_results_v1.json). Local ignored output: `data/efficientnet_adaptation_v1_20261017_1792202682936988000/`; includes protocol/owner evidence,10finalcheckpoints, per-fit histories/tensor hashes, original failure, source snapshots,OOF and recovery receipt.

No labels/splits/class definitions/181holds/NP015, original datasets, colour contract, finalTestboundary, questionnaire model or current demo checkpoint changed. No install, download, cloud upload, commit or push. The separately discussed TXTdetector was not trained by this experiment.

## Teaching: what each block does

1. `metadata` checks the old manifest, selects680Trainingrecords and verifies frozenfoldhash **before** reading any array. It prevents accidental Test/held inclusion.
2. `configure_model` freezes all parameters, then enables only the declared head/finalpointwiseconv. `training_mode` leavesBatchNormand backbone stochastic depth frozen; only classifier dropout is active.
3. `fit_arm` derives classweights from fittinglabels, optimizes exactly5epochs, then scores the outerfold once. It does not receive scoringlabels.
4. `execute_comparison` creates10freshmodels and verifies matched initialization/shuffle and completeOOFcoverage. Checkpoints stay local; no model is automatically promoted.
5. `metric_differences` subtracts two **saved evaluation results**, not model weights. Its reporting-only repair required no new training.

Viva: **Did fine-tuning solve the problem?** No. It improved the matched control by0.44percentage points and.00538macro-F1, but did not beat the previous workflow. We report the negative/mixed result, preserve the evaluation boundary and do not tune repeatedly until a desirable score appears.

What I understood (owner): pending.
