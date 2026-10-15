# Owner-run read-only B1 checkpoint diagnostic — actual evidence v1

2026-10-15, branch `vinuthan`. Original `/Users/vinuthanvinuthan/Downloads/pp1_b1_checkpoint_diagnostic_v1.json` preserved. Byte-identical copy: [owner JSON](vision_b1_checkpoint_diagnostic_owner_v1.json), 1414bytes, SHA256 `b5526b6a662cb961352eb9210981ceb91a2c94e886dac88f854e78bfa6429de8`.

Owner uploaded the unchanged9294-byte helper,SHA256 `a31d37dd7cf84b49a9b66b9f471fcd45883935ccf223fdb6709ae732076cffca`,and returned its successful Colab JSON. Local review parsed its schema/finite values/expected counts and compared helper hash;no local tensor/model execution or rerun. This is owner-executed checkpoint evidence,not a new pytest suite or clinical performance validation.

|Checkpoint|Epoch|Frozen-backbone tensors compared with official cache|Changed backbone keys|Adam steps for head weight/bias|
|---|---:|---:|---|---|
|best.pt|1|318|None|43 /43|
|last.pt|3|318|None|129 /129|

43=ceil(680/16);129=3×43. Both head optimizer states progressed exactly as expected. All4head row norms and biases are finite;every row norm differs between epochs1and3,so head weights did change during the run. Bothsavedbackbones match theofficialcachedweights,includingBNstateunderthischeck. No initial-head snapshot exists,soinitial-to-best differences cannot be measured directly.

The unchanged helper validates pinned checkpoint/result-index hashes,configuration/protocol/context,officialweightSHA,and20source hashes before computing these results. The returned JSON itself contains only aggregate outcomes,not embedded tensor bytes or a full independently replayable environment transcript;local review relies on the owner-run helper for tensor comparisons. Historical18aggregate tests remain unchanged;no new tests were run for this file review.

**Conclusion:** evidence rules against an optimizer that never stepped or accidental backbone/BNupdates at the two saved checkpoints. It does not establish classimbalance as thecausal explanation for all53Validation predictions beinggrade4. Label quality,feature/domain suitability andlimiteddevelopmentclasssupportremainunresolved. Original Validation metrics remainaccuracy0.320755,macroF1.121429,macroAUROC.659734,Brier.688751;none were rerun or modified. No finalTestuse.

**Next decision:** authorize preparation and ONE separatelyversionedTraining-only balanced-loss ResNet50head-onlycomparison under theexact proposedplan in [diagnosis](vision_b1_prediction_collapse_diagnosis_v1.md). Same680/53cohort,seed42,officialcachedweights,lr.001,batch16,max5epochs,patience2,frozenbackbone/BN,B1inputs,noextraaugmentation/sampling;weightsN/(4*n)=[14.1666667,2.0238095,.7623318,.4709141]. Implementexplicitweightedloss with generatedbackendverificationbeforeactualexecution;theoldrunner ignoresconfig.class_weight and mustremainhistorical. Preserveunweightedbaseline andreportevenworseoutcomes;noimprovementguarantee. ThepreviousONE-runpermissionisconsumed;noadditionalrealtrainingwasinitiated.

**Provisional labels; non-clinical; non-final; participant independence unverified.** JSONreportsnoimageaccess,inference,trainingordownloadsduringthisdiagnostic. No labels/splits,181holds,NP015,Test,researchgates,implementation,sourcefilesororiginalevidencechanged;noinstall,commit/push.

Viva:**Optimizersteps43என்றால்என்ன?**680படங்களை16படங்கள் கொண்ட batches-ஆகப் பிரித்தால்43batches. ஒருepoch-ல்head43முறைupdateஆகியுள்ளது. அதுமட்டும்நல்லValidationperformance-ஐஉறுதிசெய்யாது.
