# Component 2 — practical PP1 delivery v3

16 October 2026 · branch `vinuthan` · Non-clinical research prototype.

**Working demonstration and current evidence are available. Qualified Vision label/group decisions, real-photo deployment readiness and final Vision scientific evaluation are not complete.** The owner requested progress without waiting for a doctor; this delivery uses existing authorized provisional artifacts and does not invent a doctor's decision, clear held records or activate final research training.

## Open and rehearse

Open **http://127.0.0.1:8770/**. A new server is running on loopback only; the previous8768server was preserved. If8770is stopped, from the repository root run:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m src.tabular.api --port 8770
```

The existing installed frontend dependencies were used directly to rebuild; no install/download. Main startup reads hash-verified saved models/aggregate reports/saved display views, not raw participant/image datasets or an evaluator. No public deployment, tracking or cloud service is required. This is not a production-authenticated medical service.

## Actual eight-step disposition

| Step | Technical work completed | Remaining scientific/human decision |
|---|---|---|
| 1: Label/group review checklist | Existing52TrainingIDs, issues and decision roles consolidated; source evidence preserved | Checklist preparation is not clinical approval |
| 2: External whole-imageMGI0suitability | MIO officialmetadata/licence/schema checked; recordopen/CCBY4.0 | Healthy/Gingivitis/Periodontitis is not establishedMGI0–4; no qualified externalcohort, download or automaticmapping |
| 3: Held181review | Prepared52Training+129Validation review workflow; prior54pairhuman decisions preserved | All181remainheld; clinical/source-supported decisions unresolved; NP015remainsuncertain |
| 4: Manifest/protocol | Existing733provisional development pilot and strict-clean DRAFT retained, originalmembershipprotected | No new approved research manifest or expandedcohort; no fabricated approvals |
| 5: Bounded experiments | ExistingResNet/EfficientNet andnestedcached-feature comparisons complete; no reruns | No new realtraining authorized here; auxiliarytoothlearning requires a separately frozen supplementarymethod |
| 6: Prediction/Grad-CAM demonstration | Three savedv3examples/nineoriginal–heatmap–overlay views render; model/trainer/adapter software previously qualified | Arbitrarynewphoto runtime inactive; no new realimage inference or clinical deployment claim |
| 7: Final frozenVisionTest | OriginalVisionTest remainssealed; engineering/Test isolation guards preserved | FinalVisionmodel/protocol not approved; no finalVisionevaluationperformed |
| 8: Demo/evidence/viva | Newaccuratequestionnaire final-results card, refreshedstatuswording,34focusedtests and17browserchecks; thisrunbook | Owner oralrehearsal, genuineconsentedfeedback and expertvalidation are not supplied by software |

There is no defensible numeric percent-complete from these unequal tasks. Do not claim “all eight scientific steps completed.” Original fiveMGIdefinitions and signed primary architecture remain: RGB→maximumvisibleMGI0–4→Grad-CAM; questionnaire remains independent. ExploratoryMGI1–4 outputs do not silently replace or validate the five-grade research objective.

## Five-minute demonstration script (Tamil)

1. **Scope:** “இரண்டு independent branches. Photo branch visible gingival inflammation பற்றியது; questionnaire branch reported previous treatment பற்றியது. இரண்டையும் சேர்த்து ஒரே score உருவாக்கவில்லை.”
2. **Questionnaire evidence:** Show the completed final-results card:1,563participants, XGBoostAUROC0.7607/Brier0.1509, LogisticAUROC0.7561/Brier0.1514. “AUROC percent accuracy அல்ல.0.80targetஅடையவில்லை; pairedintervals தெளிவான winner நிரூபிக்கவில்லை. Cutoffs0.26/0.28statisticaldemonstrations,clinicalcutoffsஅல்ல.” No newevaluation runs from the card.
3. **Live fictional profile:** Explain default21.41%; show12TreeSHAProws andbase+contribution check. “Log-odds unit; causal effects அல்லது calibrated-probability percentage contributions அல்ல.” Changecleaningdays2→7:24.41%;reset21.41%. “Model sensitivity மட்டும்; cleaning harms/improves health என்று நிரூபிக்கவில்லை.”
4. **Vision evidence:** OpenVision. Explain historical53Validationpilot50.94%accuracy/macro-F1.325872 separately from680TrainingOOF. CurrentnestedEfficientNet accuracy52.21%,macro-F1.346429;Grade1recall0/12. “வேறு populations-ன் accuracy-ஐ நேரடியாக compare செய்யக்கூடாது. Gradesஅனைத்துக்கும் reliability கிடைக்கவில்லை.”
5. **Grad-CAM and honest error:** Show00733/00734/00766saved examples. For00766modelpredicts4whileprovisionalreference3;retainthiserror. “Heatmap modelattention;clinicalboundary/proof அல்ல. Whole-imageMGI0supportஇல்லை;181holdsஇன்னும்வெளியே. Newphoto runtime இப்போது inactive.”

Use fictional questionnaire profiles only. Existing saved dental views are local authorized evidence; do not upload them toGemini/cloud or publish this local service. ExternalAIopinion can be recorded as unverified QA commentary, never clinical groundtruth. Training00025's captions/TXT shareannotationmaximum4butdisagree ongrade0/2counts; itsneeds_review/holdisunchanged.

## Doctor/source review after the prototype

Bring [the52-IDactionpackage](vision_review_external_mgi0_action_package_v1.md) and existing localreviewer artifacts. Obtain actual reviewer identity/qualification/date, source evidence and supported decisions; retain uncertainty. Record new decisions in a new version, preserve originals. Contentgroup/participant decisions and partial-caption methodology need source-custodian/supervisor input; a label decision alone does not clear evaluation-boundary aliases. Do not represent the owner or anAI as a qualified dentist.

No newimage or clinicalgrade should be inferred from the text of this delivery. MGI0toothboxes do not establish whole-imageMGI0. Missingclass0 andscarceclass1requireappropriate evidence, not fabricated healthy samples or tuninguntilaccuracylooksbetter. Keepallcrops/aliaseswithinparentgroupsifasupplementarytaskisapprovedlater.

## Minimum genuine feedback record — blank until used

Ask permission to observe the fictional/saved demonstration; do not collect patient images or real clinical profiles. Record only what is needed under applicable course/local requirements.

| Record | Participant code | Consent/date | Could explain the two outcomes? | Understood What-if limitation? | Navigation issue / suggestion |
|---|---|---|---|---|---|
| Pending1 | | | | | |
| Pending2 | | | | | |
| Pending3 | | | | | |

These are blank collection slots, not three completed users or invented feedback. Do not use software/browser checks as a substitute for actual human understanding or expert assessment.

## Evidence and verification from this task

- **34passed,0failed,0errors,0skipped**: focusedquestionnaire evidence/API/Visionaggregate tests, not a full repository run. Testfixtures generated; no realtraining. JUnit [component2_pp1_delivery_tests_v3.xml](component2_pp1_delivery_tests_v3.xml).
- **17browserchecks passed,0failed** on8770: finalthree-modelcard, fixedcutoffs/limits,fictionalprediction,12SHAProws,scenario/reset,distinct53/680evidence,ninesavedviews,inactivephoto,mobileoverflow andzero pageerrors. [Exactchecks](component2_pp1_browser_checks_v3.json). Desktop screenshots visually inspected and stored only in ignoreddata.
- New `questionnaire_evidence.py` reads only one hash-pinned aggregate report and filters fields; mismatchedmodel/report,symlink,unsafe size,nonfinite metrics/status failclosed. ItsAPIroute cannot train, loadrawdata or callthefinalevaluator.
- Frozen source/models, finalTestresults/onceclaim and Visionhistoricalevidence remain unchanged. No clinical/institutional approvals, dataexpansion,Testactivation,automaticweightdownload,installation,commit orpush. [Currenthashes](component2_pp1_delivery_verification_v3.json).
- Thehistorical API/model metadata were not rewritten; newcard accurately records completedTabularfreeze/evaluation externally. Genericfooter now clearly statespendingVision/clinicalstatus. Historicalreadiness/rehearsalreports are preserved.

## Three important code blocks and one viva answer

1. `questionnaire_evidence.load_evidence`: reportSHAமற்றும்ரன்னிங்modelIDபொருந்தினால்மட்டும் பழைய aggregate metricsகாட்டும். PrivateIDs/pathsexposeஆகாது;Testமீண்டும்ஓடாது.
2. `/api/questionnaire/evidence`: predictionendpoint-இலிருந்து தனியானread-onlyresult. Presentationupdateக்காகmodelஐமீண்டும்fitசெய்யவில்லை.
3. `QuestionnaireEvidence`: மூன்றுமாடல்களையும்limitations-உடன்காட்டும்;சிறந்தஎண்ணைமட்டும்தேர்ந்தெடுத்துக்காட்டவில்லை. Visionpanelஇன்னும்தனியாகஇருக்கும்.

Viva: **Why is a working heatmap insufficient to claim a reliable clinical model?** “Heatmap output-ஐ விளக்க உதவும். அது labels சரி, participantindependenceஉண்டு, unseenpatients-ல்அனைத்துகிரேடுகளும் சரியாகவரும் என்று நிரூபிக்காது. அதற்குத் தனி scientific/clinical validationதேவை.”

**Next single practical action:** owner opens8770and rehearses the five-minute sequence. FurtherVisiontraining/datachanges or finalVisionTest need separately concrete scope and the appropriate evidence; there is no automaticbackgroundtraining after thisdelivery. Keep the preparedreviewpackage for genuine qualifieddecisions later. WhetherPP1assessmentcriteriaaresatisfiedmustbeconfirmedwiththecourse/supervisor;thisreportdoesnotguaranteemarks.

What I understood (my own words):
