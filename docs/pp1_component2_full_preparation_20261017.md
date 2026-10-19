# Component 2 PP1 Preparation Report

**Project:** AI Integrated Dental Health Assessment, RP J26 IT 458  
**Owner:** Vinuthan T, IT23311022, BSc IT, SLIIT  
**Component title:** Dual-Branch Explainable AI & Interactive Risk Simulator for Periodontal Disease Screening  
**Evidence date:** 17 October 2026, Asia Kolkata  
**PP1 date:** 22 October 2026

This report explains what Component 2 does, what has actually been built and tested, how its code is organised, and what remains unfinished. It is a preparation reference for explaining the work; it does not replace the signed proposal or demonstrate the owner's understanding by itself.

**Current conclusion:** the questionnaire path is implemented, explained with TreeSHAP, connected to a controlled What-if interaction, and evaluated once on its frozen final Test sample. Vision has audited data preparation, provisional model experiments, saved Grad-CAM demonstrations and a restricted upload integration. Reliable five-grade Vision performance, final Vision evaluation and human understanding studies remain incomplete.

**The two outputs stay separate.** A photo produces a visible-inflammation grade. The questionnaire estimates self-reported previous gum-treatment history. They are not added or averaged into one patient risk score.

**Reading order for PP1:** start with Sections 1, 2 and 3; learn the two pipelines in Sections 5 to 9; open the important files in Sections 11 and 12; rehearse Sections 15 and 16. Sections 13, 14 and 17 provide the claims, limitations and evidence needed to defend the presentation.

**Tamil English speaking note:** “Namma component rendu independent outputs kudukkum. Photo visible gum inflammation pathi; questionnaire previous gum-treatment history pathi. Rendum serthu ore disease-risk score kudukkala.”

## 01 Project purpose and responsibility

The team project contains four components. This report concerns only Vinuthan's Component 2. Other team models or plaque, tartar, alignment and caries folders in the shared repository are not evidence of Component 2's own implementation or accuracy.

The problem is that an unexplained prediction number is difficult for a user to interpret. A photograph and a questionnaire also measure different things. Our component therefore implements separate prediction paths, explains each output in its appropriate form, and lets a user inspect selected questionnaire changes without claiming a treatment effect.

The image research target is the **maximum visible Modified Gingival Index grade in one photograph**, with the original five-grade definition 0 to 4. This is a derived image-level target from per-tooth captions. It does not diagnose periodontitis, attachment loss, bone loss or a periodontitis stage.

The questionnaire target is **OHQ850 self-reported previous gum-disease treatment**. Its label says whether a respondent reported having received gum treatment. It is neither current disease status nor a future progression label. Cross-sectional associations cannot tell us that changing a behaviour causes a future health improvement. [P, S1]

Our research questions are: how the specified image models compare under the same target and evaluation boundary; whether XGBoost improves meaningfully over regularised Logistic Regression for the treatment-history outcome; and whether users can correctly understand the separate outputs and the limitations of the explanations and What-if feature.

The component responsibility includes data audit, label rules, preprocessing, model experiments, Grad-CAM, TreeSHAP, constrained re-inference, the Component 2 API and its interface. Shared authentication, production hosting and integration with all other team components are separate team work; they are not established by the local demo.

**One sentence for the panel:** “I am developing an explainable research component that independently grades visible gingival inflammation from photographs and models reported previous gum treatment from questionnaire answers, with reproducible evaluation and a constrained model-sensitivity interface.”

## 02 What has been created

| Deliverable | Current evidence status |
|---|---|
| NHANES audit and exclusion report | Completed with join, identifier, code and count checks |
| Reusable tabular preprocessing | Implemented and fitted inside development folds |
| Logistic, XGBoost and constant-rate comparisons | Implemented; frozen final Test comparison completed |
| Questionnaire prediction and TreeSHAP | Implemented; numerical explanation checks verified |
| Smoking and cleaning What-if with reset | Implemented; protected fields and invalid scenarios checked |
| React and FastAPI local application | Implemented and previously browser/API verified |
| Image extraction, caption and TXT quality checks | Implemented; unresolved records remain held |
| Image model factories and training code | Implemented; several explicitly provisional experiments completed |
| Original display, Grad-CAM heatmap and overlay | Saved examples available; restricted upload integration also implemented |
| Matched EfficientNet adaptation trial | Ten fits completed; did not beat the earlier image workflow |
| Qualified final image labels and participant grouping | Pending |
| Final five-grade Vision model and final Vision Test | Pending |
| Formative user study and clinical explanation review | Pending; no participants or approvals invented |
| TXT supervised detector and predicted tooth-box tab | Discussed only; not trained or implemented |

“Implemented” means software exists. “Verified” identifies a specific saved check. Neither word automatically means a clinically reliable model. There is no defensible single completion percentage across these unequal tasks. [E1, E5, E6, E7]

The current local application has a generated-photo upload verification path. It is incorrect to say that no image endpoint exists anymore. It is equally incorrect to describe that endpoint as accepting and clinically validating arbitrary patient or internet photos. Its exact restrictions are explained in Section 10.

## 03 Proposal objectives and present progress

The signed proposal defines six objectives. Its feasibility targets are evaluation goals, not guarantees or achieved results. [P, pages 16 to 23]

| Objective | What it requires | Present position |
|---|---|---|
| SO1 Data preparation | Versioned sources, targets, exclusions and independent observation boundaries | Tabular audit completed; Vision preparation substantial, but final label and participant decisions pending |
| SO2 Image comparison | EfficientNet versus ResNet and majority baseline for five MGI grades; target macro-F1 at least 0.70 | Exploratory four-grade results exist; valid five-grade comparison and target not achieved |
| SO3 Questionnaire comparison | XGBoost versus Logistic and rate baseline; target AUROC at least 0.80 | Frozen Test evaluation completed; XGBoost AUROC 0.7607, target not met |
| SO4 Explanations | Grad-CAM and TreeSHAP with alignment, units, reconstruction and explanation checks | Software checks exist; clinical localisation review and user understanding remain pending |
| SO5 What-if and API | Constrained changes, protected history and versioned communication; tabular p95 target 1 second | Functions and API implemented; no claim here that a full declared-load p95 benchmark is complete |
| SO6 User evaluation | Planned 12 to 15 adults, at least 90% task completion and 80% endpoint understanding | Planned; no completed study results established |

The proposal also lists an image p95 response target of 5 seconds and a planned expert review of 30 selected images. Those targets and plans must not be presented as measured results. Three informal feedback slots in a demo runbook are not a completed 12 to 15 person study. Applicable ethics approval and actual consent must precede participant involvement.

**Important PP1 distinction:** there is enough implemented work and experimental evidence for a meaningful presentation. Full scientific completion and PP1 acceptance cannot be guaranteed by software tests or by this report. Confirm the assessment expectations with the supervisor.

## 04 Datasets and observation counts

### Image source and current cohort

The source is Mendeley's intraoral gingivitis image-captioning dataset, version 1, credited to Duy Hoang Bao and the associated study. It reports 1,096 photographs, published membership of 732 Training, 182 Validation and 182 Test, and CC BY 4.0 licensing. Source attribution and transformation records are retained. [S5, E1]

| Image evidence unit | Count and interpretation |
|---|---|
| Original published source | 1,096 images; not 1,096 approved independent training patients |
| Original Training plus Validation | 914 development images |
| Current provisional B1 bundle | 733 views: 680 original Training and 53 original Validation |
| Development records held | 181: 52 Training and 129 Validation; not automatically eligible |
| Published Test membership | 182 protected source images; final eligible Test manifest is unresolved |
| Current Training grade support | MGI 1/2/3/4 = 12/84/223/361; no supported whole-image MGI 0 |
| Current Validation support | MGI 1/2/3/4 = 1/13/22/17 |

The 680-image OOF experiments do not use the 53 Validation images. The 181 holds are outside those experiments. The records with annotation disagreements in the held queue are therefore not proof that corrupt labels caused errors in the included 680 records.

Exact and near-content audits found repeated-content questions. Human visual decisions help identify content, but neither a perceptual hash nor a visually similar mouth establishes participant identity. NP015 remains uncertain. The final participant or content-group protocol cannot be silently inferred from model predictions.

### Questionnaire source and cohort

NHANES 2017 to March 2020 pre-pandemic files P_DEMO, P_OHQ, P_SMQ and P_DIQ are linked by SEQN. The files describe US respondents. [S1 to S4]

| Preparation step | Verified count |
|---|---:|
| P_OHQ source rows | 14,986 |
| Valid OHQ850 Yes responses | 1,941 |
| Valid OHQ850 No responses | 5,876 |
| Valid outcome cohort before cleaning-day exclusions | 7,817 |
| OHQ870 value 9 excluded by the declared main-analysis rule | 3 |
| Final cleaned modelling sample | 7,814 |
| Development participants | 6,251 |
| Frozen final Test participants | 1,563 |
| Final Test Yes / No | 388 / 1,175 |

The earlier 11,137 all-inner-join count was an intermediate count, not the modelling sample. Starting with valid outcome rows and using one-to-one left joins preserves people skipped or missing in a module. Each join checks row counts and unique SEQN. Outcomes are never imputed. [E2]

## 05 Questionnaire inputs and preprocessing

Thirteen selected raw fields become twelve conceptual inputs because SMQ020 and SMQ040 are combined into one smoking-status field. The following descriptions follow the CDC codebooks and the implemented allowlist. [S1 to S4, E3]

| Input used by the model | Meaning and preparation |
|---|---|
| RIDAGEYR | Age; eligible at 30 or older; released 80 means 80 or older |
| RIAGENDR | Recorded sex category; categorical |
| DMDEDUC2 | Adult education using NHANES categories |
| DMDMARTZ | Marital status using its three released categories |
| INDFMPIR | US family income to poverty ratio, numeric; missing indicator retained |
| OHQ030 | Time since last dental visit, including never visited |
| OHQ845 | Self-rated teeth and gum health |
| OHQ860 | Previously told of bone loss around teeth; awareness-related ablation field |
| OHQ870 | Days of interdental cleaning in the previous seven days |
| OHQ835 | Respondent thinks they might have gum disease; awareness-related ablation field |
| DIQ010 | Reported diabetes category; borderline remains a separate valid category |
| SMOKING_STATUS | Derived from SMQ020 lifetime cigarettes and SMQ040 current pattern |

**Excluded from predictors:** OHQ850, SEQN, OHQ555Q, survey-design fields, review flags and the two raw smoking columns after derivation. OHQ850 is the outcome only. Survey fields WTINTPRP, SDMVSTRA and SDMVPSU remain available for sensitivity analysis, not prediction inputs.

Smoking derivation respects skip logic: SMQ020=2 gives fewer than 100 lifetime cigarettes; SMQ020=1 with SMQ040=1 or 2 gives current; SMQ040=3 gives former. Missing or inconsistent combinations remain unknown. A structural skip is not an invented smoking answer.

The codebook releases OHQ870 values through 9. Our declared main analysis admits integer 0 to 7, excludes three observed 9s, and retains them for review. This is an explicit project rule, not a claim that CDC labels 9 as a missing code. Refused and unknown codes differ between variables; we do not replace every 7 or 9 indiscriminately.

The saved sklearn Pipeline uses numeric median imputation, StandardScaler and fixed missing indicators. Categorical values use an explicit unknown category and OneHotEncoder. The full representation has 47 encoded columns from twelve inputs. A fresh ColumnTransformer is fitted inside every development fold to prevent leakage. The participant split is stratified 80/20 with seed 42 and frozen membership.

Two feature sets were compared: all inputs, and an awareness-ablated set without OHQ835 and OHQ860. This tests sensitivity to treatment-awareness-associated inputs, not causality. US income and education definitions are not automatically validated for Sri Lankan personal scoring.

## 06 Questionnaire models and actual final results

The candidate is XGBoost, compared with L2 regularised Logistic Regression and a constant training-rate baseline. Logistic provides a simpler reference; XGBoost can represent nonlinear patterns, but superiority must be measured rather than assumed.

The frozen full XGBoost A uses 200 trees, maximum depth 2, learning rate 0.05 and L2 regularisation lambda 1. The retained Logistic comparator uses C=1. Development comparisons, calibration and threshold studies preceded a numerical freeze. Final models use raw probabilities without an additional sigmoid calibration mapping. The cutoff was selected on development OOF predictions, not on the final Test. [E4]

The final held-out evaluation ran once on 16 October 2026. [E4]

| Frozen model | Test AUROC | Conditional 95% interval | AP | Brier |
|---|---:|---|---:|---:|
| XGBoost A | 0.760654 | 0.733363 to 0.788940 | 0.555094 | 0.150858 |
| Logistic C1 | 0.756113 | 0.727886 to 0.783610 | 0.554765 | 0.151364 |
| Training-rate baseline | 0.500000 | 0.500000 to 0.500000 | 0.248241 | 0.186617 |

At the frozen XGBoost cutoff 0.26, sensitivity is 55.93%, specificity 83.57%, and the confusion counts are TN=982, FP=193, FN=171, TP=217. Accuracy is 1,199/1,563 = **76.71%**. The statistical cutoff is not a clinically approved operating threshold.

Always predicting No would already achieve 75.18% accuracy because No is common. AUROC, positive-class sensitivity, AP and calibration therefore matter. AUROC 0.7607 is a ranking metric, not “76.07% accuracy”. The provisional 0.80 AUROC target was not achieved.

The paired XGBoost-minus-Logistic AUROC interval is -0.005623 to 0.013846, which includes zero. A clear overall XGBoost advantage is not established. The constant baseline's trapezoidal PR-AUC is affected by endpoint interpolation of tied scores; use AP and the full context rather than calling that baseline a better ranking model.

Reported intervals condition on fitted models and do not account for the full NHANES survey design, previous selection or external transportability. Survey-weight point sensitivity exists, but it is not nationally representative variance estimation. The final Test must not be rerun or used to choose new settings.

## 07 TreeSHAP and constrained What if

The questionnaire explanation uses `shap.TreeExplainer` on the tree model's raw output. Contributions are in **log-odds**, and 47 encoded-feature contributions are grouped back into the twelve understandable inputs. [S8, E5]

The important check is that the base value plus all contributions reproduces the model's raw margin. Applying the logistic function to that reconstructed margin must reproduce its probability. The implementation additionally compares with XGBoost's native contribution output and uses a tolerance of 0.00001. A contribution is not a percentage-point change in calibrated probability.

For example, “this feature pushes the model toward reporting previous treatment” is a model explanation. It does not mean that the feature caused gum disease or caused treatment. Similarly, global mean absolute SHAP importance describes model usage, not a clinical cause ranking.

The What-if feature copies an original profile and permits changes only to smoking status and interdental-cleaning days. Age, sex and other history inputs remain fixed; outcome and identifier fields are rejected entirely. Smoking changes between current and former are supported only without rewriting lifetime history. Cleaning days must be an explicit integer from 0 to 7.

The same model version, preprocessing and explanation code process both the original and the scenario. Reset recreates the original result. Editing the base profile invalidates a previous scenario. Invalid combinations, extra fields, non-finite values and stale model IDs are rejected.

Support warnings use development category counts and a smoking-cleaning pair count. Fewer than 20 cases triggers a disclosed heuristic warning. It is not a validated full-profile reliability estimate or a guarantee that a combination above 20 is safe.

The verified fictional demonstration has approximately **21.41%** original output. Changing cleaning days from 2 to 7 gives approximately **24.41%**, then reset returns to 21.41%. This increase must remain visible. It is not proof that cleaning harms health: the outcome is reported past treatment and the model captures associations, not an intervention. Changing both smoking and cleaning is a different scenario with a different result.

**Tamil English speaking note:** “What-if actual health improve aagum prediction illa. Answer change panna model output eppadi maarudhu-nu mattum kaattrom. SHAP values log-odds; direct percentage changes illa.”

## 08 Vision labels and image processing

Three caption variants accompany each image. The label parser looks for supported MGI phrases and extracts grades in 0 to 4. The image target is the maximum mentioned grade, not a mean. For an illustrative caption with grades 1, 2 and 4, the image target would be 4. This example explains the rule; it is not a new dataset record.

Unclear or conflicting captions go to review. Missing labels are not grade 0. A non-inflamed phrase is not automatically a complete healthy-image label. A normal tooth in an image containing an inflamed tooth does not make the whole image MGI 0.

The published TXT mapping is ROI classes 0 and 1, then MGI grades 0 to 4 under class IDs 2 to 6. TXT files contribute to annotation consistency and eligibility checks. Existing classifier training uses RGB-derived arrays and caption-derived provisional image labels; it did **not** train a bounding-box detector. Box-count or grade-histogram agreement alone does not establish clinical truth.

The current B1 pathway checks explicit RGB, image dimensions, orientation and a qualified embedded ICC profile. It interprets supported colour information into signed extended-sRGB floats, retains values outside ordinary 0 to 1 when required, forms a 224 square with aspect-preserving content and mean-colour padding, then applies ImageNet mean and standard deviation. Model data and display previews are separate.

For the actual source geometry, content is roughly 224 by 150 inside the square. Original full-resolution files are preserved. Display-only previews may be clipped to ordinary sRGB; they must not be described as numerically identical model inputs or clinically validated colour reproductions.

Generated checks found aliasing in the frozen half-pixel bilinear sampler, which deliberately has no antialias filter. That demonstrates a sampling mechanism on a synthetic pattern, not a proven cause of dental errors. A candidate antialias primitive has numerical limitations and was not activated. Historical arrays were not silently replaced.

**Why the 181 holds matter:** qualification of colours or file integrity does not approve clinical labels, resolve repeated participants, or clear protected groups. Those decisions need their own evidence. [E1, E8]

## 09 Vision experiments and results

ResNet-50 is the baseline architecture and EfficientNet-B0 the compact candidate. Both start from documented ImageNet weights. A majority baseline checks whether a model merely exploits the common grade. Grad-CAM is explained separately from predictive performance. [S6, S7]

### The same 53 Validation records

| Provisional experiment | Accuracy | Macro-F1 | What was trained |
|---|---:|---:|---|
| Balanced ResNet head v2 | 33.96% | 0.2294 | Classification head |
| ResNet last bottleneck v3 | 50.94% | 0.3259 | Head plus layer4.2 convolution weights |
| Local seed43 follow-up | 43.40% | 0.2697 | Same declared layer subset, different seed and runtime |

The v3 increase traded away Grade 2 recognition: correct Grade 2 fell from 12/13 to 1/13. The seed43 comparison also moved from Tesla T4 CUDA to Apple MPS and changed runtime versions. It does not isolate seed as the cause. These repeatedly used 53 records are development evidence, not final Test performance. [E9]

### Training only out of fold comparisons on 680 records

| Workflow | Accuracy | Macro-F1 | Important interpretation |
|---|---:|---:|---|
| Frozen ResNet features and balanced LR | 47.50% | 0.2951 | No neural fine-tuning |
| Frozen EfficientNet features and balanced LR | 52.65% | 0.3410 | Same old folds and fixed linear-head recipe |
| Frozen EfficientNet features and unweighted LR | 53.24% | 0.3374 | Higher accuracy traded against some Grade 2 recognition |
| Nested EfficientNet features and selected LR head | 52.21% | 0.3464 | 95 Logistic fits; zero neural optimiser steps |
| New neural head-only control | 46.32% | 0.3362 | Five epochs per fold on MPS |
| New head plus final feature block | 46.76% | 0.3416 | Same matched procedure; final pointwise convolution also trained |
| Fold majority | 53.09% | 0.1734 | Always predicts the majority grade; weak balanced recognition |

The frequently discussed 52.21% is 355/680 correct in nested cross-validation. It is not the only recorded image accuracy, a final five-grade Test score, or a fully fine-tuned EfficientNet. Different workflows have different trade-offs; none is an approved final winner. Historical 53-Validation and 680-OOF scores must not be ranked directly against each other. [E10]

The new authorised matched experiment completed exactly ten fits, fifty epochs, with identical starting states and fitting order, frozen BatchNorm, fitting-only weights and final-epoch OOF scoring. Final-block adaptation improved the matched control by a net three correct records and 0.005384 macro-F1. It did not beat the prior nested workflow. Only `features.8`, a final pointwise convolution, was released; the entire backbone was not fine-tuned.

Grade 1 remained 1/12 correct in both new arms. Grade 2 moved 31/84 to 33/84. No supported whole-image Grade 0 exists in this cohort. These results do not reach the original five-grade macro-F1 target.

The original run hit a Brier-key reporting error after all checkpoints and OOF scores were saved. The report helper was repaired; metrics were recovered from those saved outputs with zero new fits or inference. The original failure and execution source remain preserved. Timing and peak RSS were not saved before that exception and are recorded as unknown, not invented. [E11]

## 10 Grad CAM and the actual application

Grad-CAM takes the gradient of one class score with respect to a final convolutional activation map, averages gradients into channel weights, combines the activation channels, and retains positive evidence. The map is normalised and aligned back to the displayed image after removing input padding. The prediction and explanation use the same selected class. [S7]

The three views are an original display preview, a pseudocolour heatmap, and an overlay. They illustrate model attention. They are not clinician-drawn inflammation boundaries and do not prove a correct grade. Failure states include no positive signal, no spatial contrast and attention lost to padding.

The live application is **React with a local FastAPI and Uvicorn backend**. React renders the questionnaire, SHAP bars, What-if/reset, saved Vision evidence and photo views. FastAPI validates requests and calls the existing scientific functions. Python does the ML work; Node and esbuild build the frontend bundle. MongoDB, Express, an LLM predictor and production hosting are not part of this implemented component.

| Request | Function |
|---|---|
| GET /api/schema | Twelve input definitions, example profile and model ID |
| POST /api/predict | Treatment-history probability and checked log-odds SHAP |
| POST /api/what-if | Restricted scenario with same model version |
| POST /api/reset | Reproduce original profile |
| GET /api/questionnaire/evidence | Frozen aggregate results; cannot rerun final Test |
| GET /api/vision and /api/vision/evidence | Saved examples and explicitly separated experiment populations |
| GET /api/vision/runtime | Whether the restricted photo adapter is active |
| POST /api/vision/photo | Registered JPEG prediction and aligned Grad-CAM when explicitly enabled |

Default startup leaves the photo runtime inactive. The restricted live mode needs a checkpoint path, registration file and trusted registration SHA together. It admits only hash-registered, source-confirmed non-study RGB JPEGs with the qualified ICC profile, identity orientation, at most 8 MiB and 40 million pixels.

End-to-end verification used a generated JPEG and the real pinned v3 checkpoint. It did not establish successful inference on an independently sourced clinical photo. Unknown-source PNGs and arbitrary phone images are not accepted by this scope. The trained checkpoint remains the earlier provisional ResNet v3; the new ten-fit experiment was not promoted into the demo. [E6]

## 11 Technologies and repository navigation

Repository root: `/Users/vinuthanvinuthan/Desktop/RP-J26-IT-458`. The active project branch is `vinuthan`. Open the following paths relative to that root; clickable Markdown links target the actual local files.

| Technology | Actual role |
|---|---|
| Python | Audits, preprocessing, training, inference, explanations and backend |
| pandas and NumPy | XPT/tabular processing, image arrays, checks and metrics |
| scikit-learn | Pipelines, encoding, scaling, splits, Logistic and evaluation |
| XGBoost | Tree-based treatment-history model |
| SHAP and SciPy | TreeSHAP and logistic conversion for reconstruction checks |
| PyTorch and torchvision | CNNs, gradients, training and model loading |
| Pillow | Image decoding, previews, alignment and rendering |
| FastAPI, Pydantic, Uvicorn | Validated local HTTP API and server |
| React and CSS | Frontend state, results, controls and display |
| Node and esbuild | Frontend build only |
| joblib, JSON, NPZ and PyTorch files | Saved pipeline, provenance, numeric evidence and checkpoints |
| pytest and Playwright | Focused numerical/API tests and browser verification |
| Git, manifests and SHA256 | Version tracking, input identity and reproducibility |
| Colab CUDA and Mac MPS | Declared experimental compute environments |

The declared frontend package uses React 19.2.0 and esbuild 0.25.10. Saved local scientific runs record Python 3.13.5, PyTorch 2.11.0 and torchvision 0.26.0; other experiments, especially Colab, have separate runtime versions. Do not assume one global environment covers all old runs.

`requirements.txt` currently lists pandas, numpy, scikit-learn, xgboost, shap and pytest. Actual source also imports the runtime libraries above. A complete pinned reproducible dependency lock is a remaining packaging task; an installed local environment is not proof that the minimal requirements file recreates the full application.

`data/` holds raw sources, manifests, numeric views and experiment evidence; `models/` holds local weights and fitted pipelines. They are ignored and must not be committed. `docs/` holds aggregate reports and logs, `tests/` holds checks, and `src/tabular/ui/` holds the frontend.

The planned `api/` and `src/explain/` folders are not where the current application lives. The actual backend is `src/tabular/api.py`; explanation code lives with each branch. Do not search a proposed folder layout and conclude the endpoint is missing.

## 12 Important code files to open

### Questionnaire and application files

| Actual file | Responsibility |
|---|---|
| [audit_nhanes.py](/Users/vinuthanvinuthan/Desktop/RP-J26-IT-458/src/tabular/audit_nhanes.py) | XPT loading, source-verified zero repair, valid outcome cohort, one-to-one left joins and count report |
| [preprocess_nhanes.py](/Users/vinuthanvinuthan/Desktop/RP-J26-IT-458/src/tabular/preprocess_nhanes.py) | Smoking derivation, exclusions, twelve-input allowlist, frozen split and preprocessing |
| [baseline_nhanes.py](/Users/vinuthanvinuthan/Desktop/RP-J26-IT-458/src/tabular/baseline_nhanes.py) | Logistic and constant-rate development baselines |
| [logistic_comparison_nhanes.py](/Users/vinuthanvinuthan/Desktop/RP-J26-IT-458/src/tabular/logistic_comparison_nhanes.py) | Regularisation, class-weight and awareness-ablation comparisons |
| [xgboost_comparison_nhanes.py](/Users/vinuthanvinuthan/Desktop/RP-J26-IT-458/src/tabular/xgboost_comparison_nhanes.py) | Fixed XGBoost settings and matched development folds |
| [calibration_threshold_nhanes.py](/Users/vinuthanvinuthan/Desktop/RP-J26-IT-458/src/tabular/calibration_threshold_nhanes.py) | Development-only calibration and operating-point studies |
| [questionnaire_explain.py](/Users/vinuthanvinuthan/Desktop/RP-J26-IT-458/src/tabular/questionnaire_explain.py) | Input validation, TreeSHAP, support warnings, What-if and reset |
| [pp1_questionnaire_workflow.py](/Users/vinuthanvinuthan/Desktop/RP-J26-IT-458/src/tabular/pp1_questionnaire_workflow.py) | Saved development workflow and demonstration artifacts |
| [finalise_development.py](/Users/vinuthanvinuthan/Desktop/RP-J26-IT-458/src/tabular/finalise_development.py) | Frozen candidate, cutoffs and preparation receipt |
| [evaluate_frozen_tabular.py](/Users/vinuthanvinuthan/Desktop/RP-J26-IT-458/src/tabular/evaluate_frozen_tabular.py) | One authorised final Test evaluation; read for viva, do not rerun |
| [local_demo.py](/Users/vinuthanvinuthan/Desktop/RP-J26-IT-458/src/tabular/local_demo.py) | Load verified saved questionnaire model and Vision assets |
| [questionnaire_evidence.py](/Users/vinuthanvinuthan/Desktop/RP-J26-IT-458/src/tabular/questionnaire_evidence.py) | Expose matching frozen aggregate results without invoking evaluation |
| [api.py](/Users/vinuthanvinuthan/Desktop/RP-J26-IT-458/src/tabular/api.py) | FastAPI routes, validation, local boundary and optional photo startup |
| [App.jsx](/Users/vinuthanvinuthan/Desktop/RP-J26-IT-458/src/tabular/ui/App.jsx) | Editable React application source and interaction state |
| [style.css](/Users/vinuthanvinuthan/Desktop/RP-J26-IT-458/src/tabular/ui/style.css) | Layout and visual styling |
| [build.sh](/Users/vinuthanvinuthan/Desktop/RP-J26-IT-458/src/tabular/ui/build.sh) | esbuild frontend generation; app.js is generated output |

### Vision files

| Actual file | Responsibility |
|---|---|
| [extract_audit_gingivitis.py](/Users/vinuthanvinuthan/Desktop/RP-J26-IT-458/src/vision/extract_audit_gingivitis.py) | Dataset extraction and initial integrity workflow |
| [audit_gingivitis.py](/Users/vinuthanvinuthan/Desktop/RP-J26-IT-458/src/vision/audit_gingivitis.py) | Image inventory, filenames, hashes and initial labels |
| [verify_caption_labels.py](/Users/vinuthanvinuthan/Desktop/RP-J26-IT-458/src/vision/verify_caption_labels.py) | Caption parsing, comparison with TXT and review status |
| [content_groups.py](/Users/vinuthanvinuthan/Desktop/RP-J26-IT-458/src/vision/content_groups.py) | Exact and near-content group analysis; not participant identity proof |
| [model_pipeline.py](/Users/vinuthanvinuthan/Desktop/RP-J26-IT-458/src/vision/model_pipeline.py) | ResNet/EfficientNet factories, class gradients, CAM alignment and three views |
| [train_pipeline.py](/Users/vinuthanvinuthan/Desktop/RP-J26-IT-458/src/vision/train_pipeline.py) | General training scaffold, metrics, frozen layers, checkpoints and final research gates |
| [colour_b1_prototype.py](/Users/vinuthanvinuthan/Desktop/RP-J26-IT-458/src/vision/colour_b1_prototype.py) | Signed float colour interpretation, letterbox and normalisation |
| [colour_b1_streaming.py](/Users/vinuthanvinuthan/Desktop/RP-J26-IT-458/src/vision/colour_b1_streaming.py) | Bounded-memory view generation and derivative verification |
| [b1_development_bundle_v1.py](/Users/vinuthanvinuthan/Desktop/RP-J26-IT-458/src/vision/b1_development_bundle_v1.py) | Validate/read the pinned provisional development bundle |
| [exploratory_pilot_b1_lastblock_v3.py](/Users/vinuthanvinuthan/Desktop/RP-J26-IT-458/src/vision/exploratory_pilot_b1_lastblock_v3.py) | Historical ResNet partial fine-tuning and saved CAM run |
| [frozen_feature_probe.py](/Users/vinuthanvinuthan/Desktop/RP-J26-IT-458/src/vision/frozen_feature_probe.py) | Training-only fixed encoder, grouped folds and baseline metrics |
| [efficientnet_feature_probe.py](/Users/vinuthanvinuthan/Desktop/RP-J26-IT-458/src/vision/efficientnet_feature_probe.py) | Matched frozen EfficientNet feature comparison |
| [nested_feature_probe.py](/Users/vinuthanvinuthan/Desktop/RP-J26-IT-458/src/vision/nested_feature_probe.py) | Nested LR-head selection giving the discussed 52.21% result |
| [efficientnet_adaptation_v1.py](/Users/vinuthanvinuthan/Desktop/RP-J26-IT-458/src/vision/efficientnet_adaptation_v1.py) | Latest two-arm ten-fit neural adaptation comparison |
| [photo_explanation.py](/Users/vinuthanvinuthan/Desktop/RP-J26-IT-458/src/vision/photo_explanation.py) | Checked photo adapter, existing checkpoint and same-class Grad-CAM |
| [live_photo_demo.py](/Users/vinuthanvinuthan/Desktop/RP-J26-IT-458/src/vision/live_photo_demo.py) | Immutable registration, SHA and permitted-input startup |
| [vision_evidence.py](/Users/vinuthanvinuthan/Desktop/RP-J26-IT-458/src/vision/vision_evidence.py) | Historical aggregate cards; it does not automatically include or promote every later experiment |

### Three code blocks to defend first

In `audit_nhanes.py`, `merge(on="SEQN", how="left", validate="one_to_one")` links the same respondent without silently dropping valid outcome rows or multiplying people. Counts before and after verify that claim.

In `preprocess_nhanes.py`, `ColumnTransformer` and `Pipeline` keep learned median/scaler parameters inside the fitting data. In `questionnaire_explain.py`, `EDITABLE` and the SHAP reconstruction checks enforce what the interface claims.

In `efficientnet_adaptation_v1.py`, `requires_grad_(False)` plus selected re-enabling controls actual training. In `model_pipeline.py`, `torch.autograd.grad` computes explanation gradients without an optimiser update. An explanation call does not retrain the model.

**Suggested first reading:** questionnaire_explain, preprocess_nhanes, api, App.jsx, model_pipeline, verify_caption_labels, photo_explanation, and the actual results report for each branch. Then study training/evaluation guards. Read executable code before presenting ownership of its details.

## 13 Research novelty and honest contribution

The signed proposal describes a bounded interface and evaluation contribution, not a world-first algorithm. EfficientNet, ResNet, XGBoost, Logistic Regression, Grad-CAM and SHAP are existing methods. Reusing them is a methodological choice, not a claim to have invented them. [P, pages 15 to 16 and 46; S6 to S8]

**Proposed contribution:** an explainable, independently evaluated two-branch component that presents visible-inflammation grading and treatment-history modelling together without unsupported patient-level fusion, and lets users explore a tightly constrained questionnaire scenario while exposing endpoint and uncertainty limitations.

The research content is the question, target specification, auditable cohort construction, controlled baseline comparisons, explanation checks and planned measurement of whether users understand the system. A React page with two models alone does not prove a scientific contribution. The formative study is intended to test the understanding claim; it remains pending.

| Contribution claim | Present support | What is still needed |
|---|---|---|
| Separate outputs from unrelated public sources | Implemented separation and explicit target names | Full final validation for each branch |
| Explanations with correct units and failure handling | SHAP reconstruction and Grad-CAM software checks | Qualified localisation assessment and user interpretation evidence |
| Constrained What-if without causal promises | Editable-field restrictions, history checks, support warnings and reset | Actual user understanding and usability evaluation |
| Reproducible comparative evidence | Frozen IDs/folds, baselines, hashes, logs and negative results | Final Vision label/group protocol and final scientific evaluation |

The colour and provenance engineering helps make the workflow inspectable. It is not, by itself, evidence of clinically preserved appearance or a new colour-science algorithm. Likewise, an image-maximum label rule is a project target definition, not automatically a novel clinical grading standard.

**Safe novelty statement:** “My proposed contribution is the design and evaluation of an explainable two-branch interface with independently defined outcomes, checked explanations and constrained model-sensitivity exploration. The predictive algorithms are established methods; I compare them transparently and evaluate whether users understand their outputs.”

**Do not claim:** first system in the world; a new CNN architecture; proven superior XGBoost; clinically validated periodontal diagnosis; causal personalised treatment advice; or an achieved 80% understanding rate. These require evidence not currently established.

## 14 Verification risks and unfinished work

The project contains focused scientific, generated, API and browser checks. Test counts describe specific executions and overlap across versions. They are not a cumulative full-repository pass count or a clinical validation score.

| Saved evidence group | Actual recorded verification |
|---|---|
| Frozen questionnaire final evaluation | 109 saved-evidence assertions passed |
| Registered-photo integration | 101 selected tests and 24 unique browser checks passed; generated photo |
| New matched EfficientNet trial | 27 current generated tests and 135 independent saved-output assertions passed |
| Checkpoint verification for the new trial | Ten checkpoints, 360 tensors each checked against receipts and official initialisation |

The initial 26 new-run tests and the later 27-test source version must not be added together as 53 unique tests. A software pass proves the tested property under declared conditions. It does not prove every grade is recognised, that labels are clinically correct, or that the system generalises to a new population.

Main remaining risks are missing whole-image MGI 0 support, sparse Grade 1 data, weak minority recognition, provisional clinical labels, unresolved participant identity, repeated development selection, and no final Vision Test result. Questionnaire risks include the historical self-report endpoint, awareness-associated inputs, US-only definitions, incomplete design-based uncertainty and unvalidated local transportability.

Final Grad-CAM clinical relevance review, parameter-randomisation explanation assessment under a declared protocol, calibrated image confidence, genuine user feedback and proposal-level performance measurements are not claimed complete. The unknown-source photo was not legitimised by changing its file format.

Engineering follow-up includes complete dependency packaging, broader supported input contracts if approved, shared-system authentication/deployment and team integration. Component 2's local host and same-origin checks are useful boundaries, not a production medical-security certification.

The latest trial is a mixed/negative result. Reporting it honestly is necessary research evidence. We did not change a label, move a difficult example, repeat Test, or select a favourable seed to manufacture improvement.

## 15 PP1 demonstration and five minute speech

### Start the standard local demonstration

Use the existing environment. Starting the API must not trigger training or a final evaluation.

```sh
cd /Users/vinuthanvinuthan/Desktop/RP-J26-IT-458
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m src.tabular.api --port 8770
```

Open http://127.0.0.1:8770/. This is a startup instruction, not a claim that the server is currently running. Standard mode keeps new-photo inference inactive. For the generated registered-photo upload demonstration, follow the exact three-argument command and permitted generated JPEG in [the live runbook](/Users/vinuthanvinuthan/Desktop/RP-J26-IT-458/docs/vision_registered_photo_live_demo_v1.md). Do not substitute an unapproved dental/Test/held photo.

### A five minute sequence

**0 to 45 seconds — purpose.** Introduce your component, two independent outcomes and why they are not fused. Say the image output concerns visible inflammation and the questionnaire concerns previous treatment.

**45 to 120 seconds — questionnaire.** Show the fictional profile, probability, twelve grouped SHAP rows and their log-odds unit. Show the frozen Test card: AUROC 0.7607, Brier 0.1509 and the Logistic comparator. Explain that the 0.80 goal was not achieved.

**120 to 180 seconds — What-if.** Change cleaning days from 2 to 7 and show approximately 21.41% to 24.41%, then reset. Explain why the direction is not a treatment-effect result. Identify the two permitted fields and protected history.

**180 to 255 seconds — Vision.** Show a saved original, heatmap and overlay. Explain that the heatmap is model attention. Identify the experiment population before giving a score: 50.94% on 53 provisional Validation records, or 52.21% nested OOF on 680 Training records. Do not call either final Test accuracy. Disclose the latest fine-tuning trial's negative overall result when discussing experiments.

**255 to 300 seconds — contribution and limitations.** State the bounded novelty, what was tested and what remains. Missing Grade 0, scarce Grade 1, qualified review and final Vision evaluation are ongoing. The generated upload check demonstrates engineering, not clinical performance.

### Your opening in simple English

“My component has two independent branches. The image branch estimates the highest visible gingival inflammation grade and provides Grad-CAM. The questionnaire branch models self-reported previous gum treatment and provides TreeSHAP and a constrained What-if interaction. I do not combine the two datasets into one person-level score. I have implemented the prototype and comparative experiments; the questionnaire has a completed frozen Test evaluation, while final five-grade Vision validation and user-understanding evaluation remain incomplete.”

### Your opening in Tamil English

“Naan Component 2 work pannirukken. Photo branch MGI grade-um Grad-CAM-um kaattum. Questionnaire branch previous gum-treatment probability, SHAP explanation, controlled What-if kaattum. Rendu datasets different people; athanala combined score illa. Working prototype irukku; Vision five-grade scientific validation innum complete aagala.”

## 16 Viva questions and short answers

**1 Why two independent branches?** The source people are unrelated, and the outcomes differ. Artificially pairing them would invent patient-level evidence. A shared interface can show separate results without score fusion.

**2 Why is OHQ850 not current disease risk?** It asks about previous gum treatment. Our label measures reported treatment history, not a current periodontal examination or future disease progression.

**3 Why left join on SEQN?** SEQN links the same respondent. A left join preserves eligible labelled participants even if a module has a structural skip; one-to-one validation prevents duplicate-person expansion.

**4 Why fit preprocessing inside each fold?** Medians and scales learned from scoring data would leak information. A fresh Pipeline learns only from fitting participants, then transforms the scoring fold.

**5 What do the thirteen raw fields and twelve inputs mean?** Two smoking questions become one smoking-status variable. One-hot columns and missing indicators later create 47 numeric representation columns for the full feature set.

**6 What is the image label?** The maximum supported MGI grade in the image captions. It represents the most severe visible annotated unit in the photo, not an average or periodontitis stage.

**7 Did you train TXT boxes?** No detector was trained. TXT supports annotation QA. Current classifiers use image arrays and image-level grades. Predicted tooth boxes would require a separate approved supervised detector experiment.

**8 What exactly is 52.21%?** It is 355 correct out of 680 Training-only out-of-fold predictions using frozen EfficientNet features and nested Logistic-head selection. It is not training accuracy, final Test accuracy or a new image's confidence.

**9 Did fine-tuning improve the model?** The matched final-block arm improved its head-only control from 46.32% to 46.76%, but did not beat the prior workflow. Only the final pointwise block was released; the full backbone was not trained.

**10 Why macro-F1 as well as accuracy?** Grade 4 is common. A majority prediction reaches 53.09% accuracy while ignoring all other grades. Macro-F1 and per-grade recall expose that failure.

**11 What does Grad-CAM prove?** It shows class-specific model attention and can be checked for alignment. It does not prove a correct grade, clinician-approved boundaries or clinical generalisation.

**12 What do SHAP values mean?** They reconstruct the raw log-odds output together with the base value. They are model contributions, not causal effects or calibrated probability percentage changes.

**13 Why can cleaning more increase this score?** The score concerns reported past treatment and reflects associations. A hypothetical input change does not change real history or demonstrate health benefit or harm.

**14 Is XGBoost better than Logistic?** Its point AUROC is slightly higher, but the paired interval includes zero. We have not established clear overall superiority, and the primary selection stays as frozen.

**15 Why not keep using Test until accuracy is higher?** That would turn Test into model-selection data and bias the result. The final questionnaire evaluation was used once; Vision Test remains protected pending its final protocol.

**16 What is your novelty if these models already exist?** The proposed contribution is the independently evaluated two-outcome interface, checked explanations and constrained sensitivity exploration, supported by auditable comparisons and a planned user-understanding study. The algorithms themselves are not new.

**17 Can you claim five-grade success?** No. The current exploratory model has four supported outputs, no supported whole-image Grade 0, and weak Grade 1 recognition. Original five-grade scope remains unresolved rather than silently changed.

**18 Where is the API?** In src/tabular/api.py. It serves both branch adapters and the React frontend. Explainability code is in the branch modules; the proposed api and src/explain folders are not the current implementation.

**19 What did AI do?** AI assisted development, investigation and documentation; the use is logged. I must personally explain and verify the code I present. I should not claim that I manually wrote or independently understood everything merely because an artifact exists.

**20 What remains before final research completion?** Qualified Vision labels/groups and class support, a frozen final image protocol and evaluation, appropriate uncertainty/calibration, expert explanation review and genuine user-understanding/usability evidence, followed by approved integration work.

## 17 Evidence sources and final preparation checklist

### Project and saved execution evidence

- **P** [Signed component proposal](/Users/vinuthanvinuthan/Downloads/RP-IT23311022%20(2).pdf), verified printed/PDF pages 15 to 24 and 25 to 29; novelty decision log on page 46. Local filenames may contain spaces; use the actual Downloads file when opening outside Codex.
- **E1** [Current handoff](/Users/vinuthanvinuthan/Desktop/RP-J26-IT-458/docs/component2_project_handoff.md) and [repository rules](/Users/vinuthanvinuthan/Desktop/RP-J26-IT-458/AGENTS.md).
- **E2** [NHANES audit](/Users/vinuthanvinuthan/Desktop/RP-J26-IT-458/docs/nhanes_audit.md).
- **E3** [Preprocessing rules](/Users/vinuthanvinuthan/Desktop/RP-J26-IT-458/docs/tabular_preprocessing_rules.md) and [preprocessing report](/Users/vinuthanvinuthan/Desktop/RP-J26-IT-458/docs/tabular_preprocessing.md).
- **E4** [Frozen questionnaire final Test results](/Users/vinuthanvinuthan/Desktop/RP-J26-IT-458/docs/tabular_final_test_results_v1.md).
- **E5** [Questionnaire development and explanation results](/Users/vinuthanvinuthan/Desktop/RP-J26-IT-458/docs/tabular_pp1_completion_results_v1.md). Its old pending-Test wording is superseded by E4.
- **E6** [Registered-photo integration and launch runbook](/Users/vinuthanvinuthan/Desktop/RP-J26-IT-458/docs/vision_registered_photo_live_demo_v1.md).
- **E7** [Practical PP1 delivery guide](/Users/vinuthanvinuthan/Desktop/RP-J26-IT-458/docs/component2_pp1_delivery_v3.md). Later restricted upload work in E6 supersedes its earlier completely inactive photo description.
- **E8** [Training 52 held-case triage](/Users/vinuthanvinuthan/Desktop/RP-J26-IT-458/docs/vision_training52_evidence_triage_v1.md).
- **E9** [Seed43 report and backend interpretation correction](/Users/vinuthanvinuthan/Desktop/RP-J26-IT-458/docs/vision_b1_seed43_replication_v1.md).
- **E10** [Nested EfficientNet results](/Users/vinuthanvinuthan/Desktop/RP-J26-IT-458/docs/vision_nested_feature_probe_results_v1.md).
- **E11** [Actual matched adaptation results](/Users/vinuthanvinuthan/Desktop/RP-J26-IT-458/docs/vision_efficientnet_adaptation_results_v1.md) and [135-check verification](/Users/vinuthanvinuthan/Desktop/RP-J26-IT-458/docs/vision_efficientnet_adaptation_verification_v1.json).
- [AI use log](/Users/vinuthanvinuthan/Desktop/RP-J26-IT-458/docs/ai_log.md) and [project diary](/Users/vinuthanvinuthan/Desktop/RP-J26-IT-458/docs/diary.md).

### Primary public references

- **S1** [CDC NHANES P_OHQ codebook](https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_OHQ.htm), especially OHQ850, OHQ860 and OHQ870.
- **S2** [CDC NHANES P_DEMO codebook](https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_DEMO.htm).
- **S3** [CDC NHANES P_SMQ codebook](https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_SMQ.htm).
- **S4** [CDC NHANES P_DIQ codebook](https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_DIQ.htm).
- **S5** [Mendeley gingivitis dataset version 1](https://data.mendeley.com/datasets/3253gj88rr/1), DOI 10.17632/3253gj88rr.1.
- **S6** [Tan and Le 2019 EfficientNet](https://proceedings.mlr.press/v97/tan19a.html).
- **S7** [Selvaraju and colleagues 2017 Grad CAM](https://openaccess.thecvf.com/content_ICCV_2017/papers/Selvaraju_Grad-CAM_Visual_Explanations_ICCV_2017_paper.pdf).
- **S8** [Lundberg and Lee 2017 SHAP](https://proceedings.neurips.cc/paper_files/paper/2017/hash/8a20a8621978632d76c43dfd28b67767-Abstract.html).

### Before presenting

1. Explain the two endpoints in your own words without reading the screen.
2. Open the eight priority code files and explain their input, processing, output and one failure check.
3. Rehearse the fictional questionnaire, SHAP, scenario and reset sequence.
4. Choose saved Vision views or the explicitly labelled generated upload demonstration; verify the intended server mode beforehand.
5. Put sample size, evaluation population and provisional status next to every model score.
6. State the negative fine-tuning result and the missing-class limitation honestly.
7. Confirm supervisor expectations for the incomplete five-grade Vision function and outstanding scientific approvals.
8. Draw the required architecture diagram yourself using the confirmed components and the textual flows in this report. Do not label a newly AI-drawn diagram as your manual work.
9. Record actual consent, feedback and approvals only after they occur; do not fill blank study slots as completed participants.
10. Fill the diary's understanding fields yourself. Keep raw data and weights out of Git, and keep the frozen final Test boundary intact.

**Owner rehearsal record:** What I can now explain: ____________________. What I still need to understand: ____________________. Supervisor feedback actually received: ____________________.
