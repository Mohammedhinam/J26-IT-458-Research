# Proposed next experiment — cached EfficientNet nested head v1

2026-10-16. **PREPARED; generated tests only. Not authorized or run on real features.**

Provisional labels; non-clinical; non-final; participant independence unverified.

## Decision and rationale

The completed comparisons favour EfficientNet over ResNet on several balanced metrics, but C=1 heads produce many confident errors; removing balanced weights loses Grade2 recall. This supports a bounded **regularisation hypothesis**, not a proven defect or promised improvement. Reuse existing fixed ImageNet features; do not repeat extraction, neural fine-tuning, colour audits or historical experiments.

Select head settings using inner folds and score the selected workflow on untouched outer-fold rows. Model-selection overfitting can bias ordinary reused validation estimates: [Cawley & Talbot](https://jmlr.org/papers/v11/cawley10a.html), [scikit-learn nested-CV example](https://scikit-learn.org/stable/auto_examples/model_selection/plot_nested_cross_validation_iris.html). These sources justify the validation structure, **not the specific C grid or clinical efficacy**. The six settings below are proposed engineering choices requiring owner authorization.

## Frozen proposed protocol

| Item | Exact proposal |
|---|---|
| Inputs | Existing hash-pinned680Training EfficientNet1280-feature cache only;12/84/223/361 provisional grades1/2/3/4 |
| Encoder/preprocessing | No encoder or image execution; existing B1-derived feature cache, no resolution/colour changes |
| Outer folds | Exact existing5folds, SHA `e202132b8b7ee38ec4041ea399bccb0b538ef75ce1861faec044292c11cf90d4` |
| Inner folds | StratifiedGroupKFold(3,shuffle=True,random_state=42), created separately in each outer-fitting subset; all fitting/scoring subsets require four grades |
| Six configurations | C=.01/.1/1 × class_weight=None/"balanced"; L2 default,lbfgs,max_iter2000,seed42 |
| Preprocessing/weights | Fresh StandardScaler and LogisticRegression each inner/outer fit; balanced weights computed solely from that fit's labels |
| Selection | Highest unweighted mean3inner-fold macro-F1; exact ties → highest meanQWK → smallerC → unweighted |
| Fit bound | 5×(6×3+1)=**95 Logistic fits**, no repeated search/seed, no final all680 refit |
| Prediction | Fixed argmax grade1–4, ties lowest grade; no decision-threshold tuning or calibration |
| Comparators | Saved EfficientNet balancedC1, majority/prior OOF; existing unweightedC1 available descriptively, no reference refit |
| Report | All6inner candidates perouterfold, selected settings, pooled680OOF accuracy,macro-F1,balancedaccuracy,pergrade recall/support,confusion,QWK,ordinalMAE,withinone,AUROC,Brier/predicted counts |
| Uncertainty | 1000seed42paired content-group bootstrap draws vsmajority/prior using savedOOF; report undefined draws and conditional scope. No refit/participant/selection correction |
| Failure | Stop on membership/hash/group/class/finite/convergence failure; no fallback, settings expansion or retries |

Training groups are680singletons. They prevent known content leakage but do **not** establish participant independence. NestedCV handles selection inside this search; it cannot erase earlier encoder/analysis decisions based on these development data. Grade1 support12 remains insufficient, MGI0 absent. Do not market a statistical result as reliable four-grade or clinical performance.

## Execution boundary

Prepared source: `src/vision/nested_feature_probe.py`;10generated tests passed,0failed/errors/skipped. Tests cover all95synthetic fits, deterministic OOF coverage, outer isolation, inner/final scaler fitting, class-weight scope, tie order, group/member rejection, metric reference and convergence stops. This is software verification, not a real experiment result.

The real wrapper requires **new** scope `run_training680_nested_efficientnet_head_v1`, current code/config/cache/fold/path hashes, explicit owner acknowledgements, and a fresh ignored output path. No real permission record has been created. Prior one-run permissions are consumed. Existing production/training/colour/label gates are unchanged.

Owner authorization needed: one95-fit cached-feature nested experiment as frozen here; no original images,53Validation,181held,NP015,Test,CAM,uploads,downloads,neural training,labels,final-model deployment,commit/push. If authorized, save the prospective protocol before fitting and report all selections/failures truthfully.

## Independent actions that do not wait for this experiment

Use the already prepared181-case reviewer workflow. Qualified reviewers resolve annotation evidence, supervisor/source custodian resolves methodological/identity limitations. Never replace human grades with model errors. Do not add external Healthy/Gingivitis/Periodontitis labels as MGI0–4 without an approved compatible annotation design. Higher resolution, ordinal losses and further fine-tuning remain future hypotheses, not automatically queued experiments.
