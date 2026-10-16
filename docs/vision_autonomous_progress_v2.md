# Current Vision checkpoint after the authorized nested experiment

2026-10-16 · `vinuthan` · local work remains uncommitted.

**Owner subsequently approved exactly one95-fit cached-head experiment. It completed; its permission is consumed.** The earlier [v1 checkpoint](vision_autonomous_progress_v1.md) and verification remain historical pre-authorization evidence, not current pending-run instructions.

## Completed work

- Existing ResNet/EfficientNet/class-weight comparisons reused, not repeated. Saved680Grade1/2probability analysis established error direction/confidence, without causal claims or label changes.
- Held181review workflow prepared from cached evidence:52Training+129Validation;121partial-policy,54otherreferrals,4companions,2NP015 disjoint queues. **Every decision remains pending;zero recovered/approved.** Prior52package preserved. [Review handoff](vision_held_development_review_v2.md).
- New nestedheadworkflow completed on cached680Trainingfeatures only:6fixed settings×3innerfolds×5outerfolds plus5outerrefits=95Logisticfits. No image/encoder execution or neural optimizer step. [Full actual report](vision_nested_feature_probe_results_v1.md), [all30inner results/hashes](vision_nested_feature_probe_results_v1.json).
- Current local demo separates historical53Validationpilot from680TrainingOOF, now showing the new nestedworkflow as a fifth table row alongside3fixedlearnedheads andmajority. Historical9GradCAMviews and questionnaireSHAP/reset preserved; new-photo inference remains inactive. Open `http://127.0.0.1:8768` or restart `.venv/bin/python -B -m src.tabular.api --port 8768`.

## Measured trade-off

| Same680TrainingOOF | Accuracy | Macro-F1 | Balanced accuracy | Correct MGI1/2/3/4 | Brier |
|---|---:|---:|---:|---|---:|
| EfficientNet balancedC1 |52.65%|.341037|.340590|0/12;22/84;99/223;237/361|.753383|
| EfficientNet unweightedC1 |53.24%|.337377|.336938|0/12;19/84;100/223;243/361|.750812|
| New nested-selected head |52.21%|.346429|.348645|0/12;27/84;96/223;232/361|.613977|
| Majority |53.09%|.173391|.250000|0/12;0/84;0/223;361/361|.938235|

NewQWK.300275,macroAUROC.716342,ordinalMAE.601471. Fourouterfolds selectedbalancedC.01,onebalancedC.1. This is a selection workflow, not a final fitted/deployed model. Grade2recall improved26.19%→32.14%; accuracy andGrade3/4recall declined slightly. Grade1still0/12; lowerBrier still worse thanprior.595072. Meanmaximumprobabilitywhenwrong fell.810040→.618236;≥.8wrongpredictions185→48. No clinical calibration/reliability or statistically confirmed superiority over the oldhead is claimed.

Historical53Validationpilotaccuracy50.94% remains a separate result. Repeateddevelopment/backbone decisions, unverified participants, provisionallabels, absentwhole-imageMGI0 and scarceMGI1 remain. The newnesteddesign reduces this headsearch's selection leakage; it cannot erase earlier choices or create clinical groundtruth.

## Verification

- 58distinctselected focused tests passed in four safe-work suites,0failed/errors/skipped. After adding the real nestedresult to the aggregateviewer,8directly affected evidence tests were rerun andpassed; these are **repeat checks, not8additional unique cases**.
- 57independent actualsaved-result assertions passed with0refits:exact680membership/folds,baselinepredictions,scalermeans,all6innerconfigs/selection,convergence,independentmetrics/confusion,source/OOFhashes,1000bootstrapdraws.
- Runtime8.422s,peakRSS212.47MiB,twoCPUthreads;only3allowedcacheinputfilesopened. AllotherVisiondatareadswereblocked duringrun. No53Validation/181held/NP015/Test/CAM payloads.
- 12initialbrowser+3post-hintchecks passed. Afteractualresultintegration,5additionalbrowserchecks passed for5rows,newmetrics,populationseparation,limits andinactivephoto gate. Desktop/mobile aggregate screenshots inspected. [Current source/hash verification](vision_evidence_demo_verification_v2.json).
- Existing16Visioncore/model/colour/training sourcehashes unchanged. No dataset/label/split/manifest/policy modification, installs/downloads, cloud, commit/push.

## What genuinely blocks the next stage

1. Qualified annotation decisions and identity/group decisions for held/review cases. Code cannot substitute for a dental reviewer. Existing181viewer and52Trainingpackage are ready; no more duplicate54-pairhumanreview is requested.
2. Whole-imageMGI0 support is absent;MGI1support12Training/1Validation is insufficient for reliable class assessment. AuxiliarytoothMGI0 cannot establish whole-imageMGI0performance.
3. Final qualified cohort, participant-independence limitations, frozen scientificprotocol and finalmodel/held-out evaluation remain unapproved. Original5gradeproposal/questionnaireindependence/researchgates preserved.

**One next action:** obtain documented qualified review for the existing52heldTrainingcases, starting with annotation evidence rather than model errors. No automatic inclusion, grade rewriting, deleted originals, Test development or further experiment starts. This is the real remaining human blocker, not a request for another Colab run.

## Viva handoff

What changed? We tested stronger regularisation using only innerfolds, and scored the whole selection procedure on outerfolds. Why? To avoid choosing the settings on the answers used to report performance. What was learned? Grade2andprobabilityerror improved modestly;accuracy/otherrecalls traded off,Grade1remains unresolved. It is evidence of a limited engineering improvement, not clinical validation.

Resume from `docs/vision_autonomous_checkpoint_v1.json` and current handoff. Do not repeat completed95fits or infer background continuation/further permission from this checkpoint.
