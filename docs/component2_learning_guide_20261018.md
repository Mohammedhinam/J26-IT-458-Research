# Component 2 Complete Project Learning Guide

Simple English and Tamil English explanations for Vinuthan T

Project RP J26 IT 458 | IT23311022 | SLIIT | Status checked 18 October 2026 | PP1 22 October 2026

This is a learning report about your own project, from the first idea to the current demonstration. You do not need to know machine learning before reading it. Read a small section, explain the example aloud, then connect it to the actual project. The aim is understanding, not memorising difficult words.

The project has two separate jobs. A photograph gives a model estimate of visible gum inflammation. Questionnaire answers give a model estimate of whether someone reported previous gum treatment. Those are different questions. We keep their results separate.

**Latest correction:** EfficientNet-B0 is now integrated into the current local demonstration at http://127.0.0.1:8773/. Earlier chat messages saying its live integration was pending describe the older state. The current integration record confirms four Vision pipelines plus the independent questionnaire workflow. This report describes saved, verified project evidence; preparing this guide did not retrain or reevaluate any model. [L1, L2]

## 01 How to read this guide

Start with Sections 02 to 05 to understand the purpose and data. Read Sections 06 to 11 for image learning and explanations. Read Sections 12 to 16 for the questionnaire. Sections 17 to 22 explain the application, evidence and your next work. Sections 23 to 26 help you practise and find unfamiliar words.

Every number labelled as an actual result comes from a named project report. A classroom example is only an illustration. An illustration does not become a measured project result. A planned activity does not become completed work because it appears in a report.

**Four words to separate:** implemented means code exists; tested means a particular check ran; evaluated means performance was measured on a specified sample; clinically validated would require suitable clinical evidence. Passing software tests does not establish clinical validation.

**Tamil English:** "Code irukku, code correct-a run aagudhu, model evvalavu correct-a predict pannudhu, clinical-a nambalama: ivai naalu different questions."

## 02 The project in a small everyday story

Imagine a teacher gives two different tasks to two helpers. Helper A looks at a mouth photograph and chooses a visible-inflammation grade. Helper B reads a form and estimates whether a similar survey respondent reported previous gum treatment. A separate explanation shows what influenced each helper's answer.

Helper A does not have an X-ray or a full dental examination. Helper B does not know what will happen next year. Neither helper can replace a dentist. Their job is to demonstrate a carefully defined research prediction and help a person inspect model behaviour.

Your team project is AI Integrated Dental Health Assessment. Your responsibility is Component 2, titled Dual Branch Explainable AI and Interactive Risk Simulator for Periodontal Disease Screening. Other team components are outside this report. Their models and their accuracy do not count as your Component 2 results.

The useful research question is not simply whether we can print a number. We ask whether the number answers the intended question, how well it performs compared with simpler methods, whether the explanation is technically consistent, and whether users understand its limits.

Your contribution uses published models rather than inventing EfficientNet, ResNet or XGBoost. The component work is defining the targets, auditing the data, comparing complete workflows, preserving evaluation boundaries, checking explanations and building the restricted interactive demonstration. Any stronger claim of novelty must be supported by the literature and the signed proposal, not by the fact that the app runs.

**What you can say:** "My component has independent image and questionnaire workflows. I compare models, explain their outputs, and demonstrate restricted questionnaire changes."

## 03 The two branches and the exact meaning of each output

### Branch A Vision

**Dental words first:** gingiva means the gums around teeth; intraoral means inside the mouth; inflammation means a tissue response that can include redness and swelling. Periodontal refers to tissues around and supporting teeth. A visible-inflammation photo grade does not measure all periodontal support. Dental professionals may need examination, probing and X-rays to assess those other structures. Our MGI output is not a periodontitis stage. [W12]

Input means what we give the program: an intraoral photograph, meaning a photograph inside the mouth. Output means what the program returns: an estimated image-level Modified Gingival Index, or MGI, grade and model scores. The whole-photo models also produce Grad-CAM views.

The original research definition includes grades 0 through 4. Higher grades represent greater visible inflammation under the grading scheme. The photograph target is the maximum supported grade mentioned for that image. It is not an average of teeth. The precise clinical grading rubric must be applied by qualified people; this guide does not teach self-diagnosis.

Current whole-photo experiments have four outputs for grades 1 through 4 because approved whole-image grade-0 evidence is absent in the current provisional cohort. A tooth crop labelled 0 does not make its entire photograph a healthy grade-0 example. The original five-grade objective remains the research objective; the exploratory four-output implementation does not silently redefine it.

### Branch B Questionnaire

Input is 12 conceptual questionnaire fields. Output is a probability of **self-reported previous gum-disease treatment**, using NHANES outcome OHQ850. A probability of 0.21 means a model score of about 21% for this reported-history label. It does not mean the person has 21% gum disease.

OHQ850 is the answer the model learns to estimate. It must never be supplied as a predictor. Asking the user the target answer and then pretending to predict it would be like giving a student the answer key during an examination.

### Why the branches stay separate

The photograph dataset and questionnaire dataset describe different people. There is no verified person-to-person link between them. We cannot glue a random photograph to a random survey form and call them one patient. We do not average their outputs or produce a combined disease-risk score. [L1, L3, W1]

**Tamil English:** "Photo visible inflammation pathi. Form previous treatment history pathi. Ore person data illa; rendu scores-ai serkka maattom."

## 04 The simplest machine learning vocabulary

**Artificial intelligence**, or AI, is the broad area of making computers perform tasks associated with intelligent behaviour. **Machine learning**, or ML, learns patterns from examples rather than relying only on manually written decision rules. **Deep learning** is machine learning using multi-layer neural networks. Our image models use deep learning; Logistic Regression and XGBoost are also machine learning, but are not deep CNNs.

A **dataset** is a collection of examples. A **sample** is one example: one photograph or one survey respondent. A **label** is the answer attached to an example. A **feature** is information the program uses to estimate that answer. A **model** is the learned rule that connects features to a prediction.

A **parameter** is a number the model learns, such as a neural network weight. A **hyperparameter** is a setting we choose, such as learning rate or tree depth. Learning adjusts parameters inside a fixed experiment; comparing hyperparameters means running distinct settings under a controlled plan.

**Training** means showing examples and using their labels to adjust the model. **Inference** means applying an already trained model to an input. Clicking Predict in the current demo performs inference. It does not secretly retrain the model on the uploaded photograph.

A **prediction** is an estimate. It is not automatically a verified label. A model can be confidently wrong. A dentist's recorded assessment also needs appropriate scope and provenance before it becomes a research training label.

A **baseline** is a comparison method. Think of checking whether a new calculator does better than a very simple rule. A **candidate** is the method we are investigating. Candidate means "the proposed method to assess", not "the winner before the experiment".

**Check yourself:** If the program shows a new image but changes no weights, is that training? Answer: no, it is inference.

## 05 Our image data and why we did not train on every file

The Mendeley source dataset contains 1,096 intraoral photographs with annotations and three caption variants per image. The published folders contain 732 Training, 182 Validation and 182 Test images. The source is version 1, published in 2024 and licensed CC BY 4.0. Giving credit and preserving source identity matter. An open licence does not by itself settle every patient-privacy or external-service question. [W2, L4]

We audited filenames, file integrity, labels and possible repeated content. A **caption** is text describing tooth grades. An **annotation** is a recorded label or region. A **regular expression**, or regex, helps find grade phrases in captions. It can extract text patterns; it cannot resolve a clinical disagreement.

**Classroom example:** if a clear caption says tooth grades 1, 2 and 3, the image's maximum-grade target is 3. If another caption conflicts or important information is missing, the record needs review. Missing evidence is not assigned grade 0.

YOLO annotation class IDs and MGI grades are different number systems. Source classes 0 and 1 describe arch regions. Classes 2 through 6 map to tooth MGI 0 through 4 in the audited experimental pathway. Class ID 2 therefore does not mean MGI 2. Caption evidence remains primary; TXT annotations are not automatically clinical truth.

| Current evidence unit | Count | Meaning |
| --- | ---: | --- |
| Published Training | 732 | Original folder membership |
| Provisional Training used in experiments | 680 | Published Training minus 52 held records |
| Published Validation | 182 | Original folder membership |
| Provisional Validation used in older pilots | 53 | Published Validation minus 129 held records |
| Held development records | 181 | 52 Training plus 129 Validation awaiting relevant decisions |
| Published Test | 182 | Protected final Vision evaluation material |

These are photograph records, not proven counts of different patients. A **duplicate** is repeated content. A **content group** collects linked photographs; a **participant group** identifies the same person. Similar images and different filenames cannot prove patient independence.

The review history includes 14 exact pairs and 54 near-duplicate candidate pairs. The owner's visual decisions were 47 distinct, six visually same content and one uncertain. Those are different evidence units; do not add them as independent groups or clinical approvals. NP015 remains uncertain. The 181 holds remain held. [L1, L4]

## 06 Training validation and Test using a school example

**Training is practice homework.** We allow the model to learn from the answers. **Validation is a practice exam.** We use it for development decisions such as selecting a checkpoint. **Test is the final exam.** We freeze the method first and use Test to measure it without adjusting the method from its answers.

Looking repeatedly at a final exam and changing your study answer to match it would make the result misleading. In machine learning this is a form of **data leakage** or Test-driven selection. The same problem happens if one person's near-identical images appear on both sides of a split.

A **split** is the rule assigning examples to these roles. A **manifest** is a saved membership list so tomorrow's run uses the intended examples. A **seed** controls certain random choices. Seed 42 helps repeat a specified split, but it does not make all hardware and software produce bit-identical results.

**Stratified** means trying to preserve label proportions across partitions. **Grouped** means keeping linked examples together. Image content grouping and known participant grouping address different risks; we still lack verified participant independence for Vision.

The old ResNet50 v3 pilot fitted 680 images and used 53 separate Validation images. That small Validation set contains only one grade-1 image and was reused during development. Its selected performance is optimistic evidence for a final claim.

Vision's protected Test has not established a final clinical or five-grade performance result. Questionnaire Test is a different dataset boundary: its one authorized final evaluation was completed. "We never tested anything" and "all final testing is complete" are both inaccurate. [L3, L5, L6]

## 07 Epoch batch fold and learning rate explained slowly

### Epoch and batch

An **epoch** is one full pass through the fitting examples for one model fit. Suppose a child practises all 100 cards once: that is one revision round. Practising the same cards five times is five rounds, not 500 different cards.

A **batch** is a small group processed together. **Batch size** is how many examples are in that group. In the EfficientNet trial, one fitting fold has 544 images and batch size 16. So one epoch has 34 batches. Five epochs process 170 batches for that fit. Images are reused during learning; this does not create new original photographs.

In a normal training batch the network predicts, the loss measures error, backpropagation computes gradients, and the optimizer updates permitted weights. Validation scoring calculates outputs without learning from its labels. This is the basic training cycle. [W3]

### Fold and out of fold

A **fold** is one part of a rotating evaluation plan. Our image five-fold plan divides the same 680 Training images into five scoring groups of 136. Each fit learns from the other 544. A photo is scored by a model that did not fit on that photo in that fold.

**OOF** means out-of-fold prediction. Collecting the five scoring groups gives 680 OOF predictions, one per image per workflow. It does not mean one model trained on all 680 then was evaluated independently on those same 680.

**Very important:** fold 0's saved model fitted 544 images. The current EfficientNet live demo loads that existing fold-0 checkpoint. The 46.76% accuracy describes the pooled five-fold experiment; it is not a measured accuracy for just that loaded checkpoint or one new uploaded photograph. [L2, L7, W4]

### Learning rate and epochs are different controls

The **learning rate** controls the size of an update. Think of moving a steering wheel a little or a lot. Too large can overshoot a useful solution; too small may learn slowly. A smaller rate is not automatically better.

**Early stopping** ends a run when the selected development measure stops improving under a stated rule. **Patience 2** means tolerating two consecutive non-improving checks under that rule. A **checkpoint** is a saved model state. A selected best checkpoint and a final-epoch checkpoint are not necessarily the same.

ResNet v3 reached its five-additional-epoch cap and selected epoch 5. It did not stop early. The EfficientNet matched trial used exactly five epochs per fit with final-epoch scoring, not an early-stopping search. Different experiments have different rules. [L5, L7]

## 08 How a neural image model learns

A photograph is a grid of **pixels**. RGB stores red, green and blue channel values. The model takes an array of numbers called a **tensor**. A convolutional neural network, or **CNN**, learns filters that respond to patterns. Early and later layers combine information at different levels; no layer is automatically a verified gum detector.

The **backbone** extracts a useful representation. A **feature map** is a set of spatial responses inside it. **Pooling** compresses spatial information. The **classifier head** turns the representation into class scores. A **logit** is a raw class score. **Softmax** converts the set of logits into nonnegative scores summing to one. Those scores are not guaranteed calibrated clinical probabilities.

**Transfer learning** starts from weights already learned on another dataset, here official ImageNet weights. It is like starting with a person who already recognises general shapes rather than teaching sight from nothing. ImageNet knowledge is not dental expertise. Dental performance still needs evaluation. [W5]

**Frozen weights** stay unchanged. In head-only learning we train the new classifier while the backbone remains fixed. **Fine-tuning** permits selected backbone weights to learn too. We used small bounded stages instead of assuming every layer should change.

**Loss** is the numerical training penalty. Cross-entropy penalizes predictions that disagree with the label. A **gradient** indicates how a small parameter change affects that loss. **Backpropagation** computes gradients through the network. An **optimizer**, such as Adam or AdamW, uses them to update weights.

**Class weights** make mistakes on scarce grades count more in the fitting loss. They do not create additional rare images. **Regularization** discourages overly complex solutions. **Weight decay** is one regularizing control. **Dropout** disables selected units during training. **BatchNorm** has learned parameters and running statistics; freezing one without the other can accidentally change behaviour. Our bounded protocols explicitly controlled both.

**Overfitting** means learning the training examples too specifically and failing to generalize. **Underfitting** means the chosen method has not learned useful structure well enough. A weak result alone does not prove which mechanism caused it. Label quality, representation, sampling, colour processing and optimization can all require investigation.

## 09 Why these model names appear in our project

**EfficientNet-B0** is the proposal's main Vision candidate. B0 identifies a member of the EfficientNet family. Choosing a smaller image model can be attractive for constrained compute, but "less data means EfficientNet must be more accurate" is not a scientific guarantee. We trained and measured it rather than treating the name as evidence.

**ResNet50** is the proposal baseline. Residual connections help information and gradients move through a deep network. The 50 refers to the named architecture's depth convention, not 50 photographs, 50 epochs or 50% accuracy. The current v3 is a particular experimental checkpoint, not every possible ResNet50.

**ResNet18** is the crop classifier in the extra ROI experiments. It is not the same model as the whole-photo ResNet50. **YOLO26n** is the detector used to locate tooth regions in the returned ROI experiment. Detection draws boxes; classification assigns grades. A pipeline can contain both a detector and a classifier.

**ROI** means region of interest. The ROI workflow detects tooth/perigingival regions, crops them, predicts each crop's grade, and takes the maximum predicted crop grade as the image-level output. Twelve crop predictions from one photograph are not twelve independently photographed patients.

**CORAL** is the ordered-threshold method in the v2 crop classifier. It asks threshold questions such as whether a grade is above 0, above 1, above 2 and above 3. This respects grade order in its model formulation. An ordinal method can still perform poorly; its actual trade-offs matter more than its name. The matched weighted-CE arm and CORAL arm also differ in weighting, so that comparison is not a pure loss-only experiment. [L8, L9]

## 10 Actual Vision experiments and what the numbers mean

### Experiments using the same 680 image pool and folds

| Workflow | Accuracy | Macro F1 | Important detail |
| --- | ---: | ---: | --- |
| ResNet50 frozen features plus balanced Logistic | 47.50% | 0.2951 | Not the live v3 checkpoint |
| EfficientNet frozen features plus nested Logistic | 52.21% | 0.3464 | Different classifier workflow from neural fine-tuning |
| EfficientNet neural head only | 46.32% | 0.3362 | New head trained; backbone fixed |
| EfficientNet neural final block plus head | 46.76% | 0.3416 | Current live candidate uses one saved fold |
| YOLO ROI v1 plus ResNet18 | 60.74% | 0.3384 | 413 correct out of 680 |
| ROI v2 matched weighted CE | 59.85% | 0.3241 | Companion arm in the v2 run |
| ROI v2 CORAL | 59.71% | 0.3279 | 406 correct out of 680 |
| Majority grade baseline | 53.09% | 0.1734 | Always predicts the fitting-fold majority grade |

These rows are different workflows, not eight different architecture families. They are exploratory development comparisons with provisional labels and unresolved participant identity. Same image membership makes comparisons more informative, but does not erase different training procedures or prior development selection. [L7, L8, L9, L10]

The highest accuracy in this table is ROI v1, but the highest Macro-F1 among these learned rows is the nested EfficientNet feature/Logistic workflow. ROI v1 identifies grade 2 in only 8/84 images; nested EfficientNet identifies 27/84. Both identify grade 1 in 0/12. Neural final-block EfficientNet identifies grade 1 in 1/12 and grade 2 in 33/84. The methods make different mistakes; no result fixes reliable across-grade assessment.

The neural EfficientNet trial completed 10 fits: two arms times five folds. Each fit ran five epochs, giving 50 fit-epochs in total. That is not a single model trained for 50 epochs. A reporting error happened after all fits and predictions were saved. The summary was recovered from saved outputs without new training. Original failure evidence was preserved. [L7]

### Separate ResNet experiments

| Experiment | Evaluation | Accuracy | Macro F1 |
| --- | --- | ---: | ---: |
| ResNet v1 unweighted head | 53 reused Validation images | 32.08% | 0.1214 |
| ResNet v2 weighted head | Same 53 Validation images | 33.96% | 0.2294 |
| ResNet v3 last bottleneck plus head | Same 53 Validation images | 50.94% | 0.3259 |
| New controlled fold 0 arm A last bottleneck | 136 scoring images | 40.44% | 0.2341 |
| New controlled fold 0 arm B full layer4 | Same 136 scoring images | 45.59% | 0.3175 |

The new fold-0 pilot used a shared warm-up and matched follow-up arms. The full-layer4 arm improved over its paired arm but remained below that fold's 52.94% majority accuracy; grade 1 stayed 0/3. It did not replace the live v3 checkpoint. These 136-image values, the 53-image values and 680 OOF values cannot be ranked as one leaderboard. [L5, L11]

**The direct answer to the earlier confusion:** EfficientNet is the proposal candidate; ROI v1 has the highest accuracy in the specified 680-image table; exact ResNet v3 versus neural EfficientNet superiority is not established by their different evaluation setups. Those three statements can all be true.

## 11 Accuracy precision recall and the other score words

**Accuracy** is correct predictions divided by all evaluated examples. ROI v1 has 413 correct out of 680, giving 60.74%. It does not mean each future patient's prediction has a 60.74% chance of being right.

**Class imbalance** means some labels occur much more often. Our 680-image provisional supports for grades 1, 2, 3 and 4 are 12, 84, 223 and 361. Always guessing grade 4 gives 53.09% accuracy while recognizing no grade-1, grade-2 or grade-3 cases. That is why accuracy alone is inadequate.

**Recall** asks: among examples truly in a grade, how many did we find? **Precision** asks: among examples predicted as a grade, how many really belong there? **Classroom example:** if ten real grade-2 examples exist and a model finds six, recall is 6/10. If it predicted eight examples as grade 2 and six were correct, precision is 6/8. These are illustrative counts, not project results.

**F1** combines precision and recall using a harmonic mean. **Macro-F1** calculates an F1 for each evaluated grade and gives each grade equal weight. **Balanced accuracy** averages per-grade recall. These measures help stop the common grade from hiding failure on scarce grades.

A **confusion matrix** is a table of actual versus predicted labels. A grade-2 example predicted as grade 4 appears off the diagonal. An **ordinal MAE** measures average absolute grade distance. A mistake from 1 to 4 is farther than 3 to 4. **Quadratic weighted kappa**, or QWK, measures ordered agreement relative to a chance reference and penalizes larger disagreements more strongly.

**AUROC** measures ranking across classification thresholds. Binary AUROC 0.76 is not 76% accuracy. **Macro AUROC** combines defined per-class ranking measures. **PR-AUC** summarizes a precision-recall curve. **Average precision**, or AP, uses a different summary rule; it should not be silently substituted for trapezoidal PR-AUC.

**Brier score** measures squared probability error, lower being better. Multiclass Brier uses the complete class-score vector under the stated convention. **Calibration** asks whether groups of predictions around a probability match observed label frequencies. Low error in one metric does not automatically prove calibration.

**Sensitivity** is recall for the binary positive class. **Specificity** is the proportion of actual negatives correctly classified. **Threshold** is the cutoff turning a probability into a Yes/No decision. Lowering it usually detects more positives and also raises more false alarms.

**mAP** measures detection quality, including box overlap and confidence ranking. ROI v1 detector mean mAP50 was 0.9598; that is not 95.98% image-grade accuracy. The v1 annotated-crop diagnostic accuracy was 46.67%, also not its photo accuracy. Box detection, tooth grading and whole-photo grading are separate evaluation tasks. [L8]

## 12 Grad CAM explained as a model attention picture

**Grad-CAM** means Gradient-weighted Class Activation Mapping. It uses a selected class's gradients and a convolutional feature map to produce a coarse spatial importance view. A useful child-level analogy is highlighting parts of a page that influenced an answer. It is not a photograph of the model's thoughts or proof of a medical reason. [W6]

Our whole-photo demonstration shows three views: the original preview, a heatmap, and an overlay combining heatmap and preview. They refer to the same input and predicted class. EfficientNet targets its final feature block, features.8. ResNet targets its last convolutional block. Alignment removes model padding before mapping attention back to the original image geometry.

**Preprocessing** means preparing pixels before prediction. We use a defined colour-aware B1 route, a 224 by 224 model input and the required normalization. **Letterboxing** fits a photo into the square with padding rather than silently distorting its shape. **Normalization** puts channel numbers into the scale expected by the trained model. The same trained input contract must be preserved at inference.

**ICC profile** describes colour interpretation. **EXIF** can contain orientation and other metadata. **sRGB** is a common colour space. A missing-ICC assumption must be explicit; arbitrary stripping, clipping or changing resize rules can change the model's inputs. Earlier B1 work qualified a narrow colour-processing pathway; it did not certify every camera or clinical colour interpretation.

Our genuine example heatmaps still include irrelevant peripheral, lip or retractor attention. We preserve that output. Painting the gums red by hand would create a fake explanation. A numerically correct heatmap can still be clinically unhelpful.

**What you can say:** "Grad-CAM shows model attention for the predicted class. We checked its computation and alignment. Qualified clinical localization review remains pending." [L2, L11]

## 13 Questionnaire data from raw files to the modelling cohort

NHANES is a US health survey. Our files cover 2017 through March 2020 pre-pandemic data. A **row** is a respondent record; a **column** is a field. An XPT file is a SAS transport data format, not a model file.

We use P_DEMO for demographic information, P_OHQ for oral-health answers, P_SMQ for smoking and P_DIQ for diabetes. **SEQN** is the respondent linkage identifier. We merge the same person's records on SEQN, not on row position or name.

A **left join** preserves eligible oral-health rows even if another module has no row for a respondent. An all-inner join would retain only people present in every file and could silently change the cohort. We checked unique identifiers and one-to-one membership to prevent row multiplication.

| Actual audit and cleaning stage | Count |
| --- | ---: |
| Oral-health file rows | 14,986 |
| Valid OHQ850 Yes responses | 1,941 |
| Valid OHQ850 No responses | 5,876 |
| Valid outcome cohort | 7,817 |
| After each of three left joins | 7,817 |
| Excluded under main-analysis OHQ870 range rule | 3 |
| Cleaned modelling cohort | 7,814 |
| Frozen development participants | 6,251 |
| Frozen held-out Test participants | 1,563 |

The earlier 11,137 all-inner-join count is not the modelling sample. Eligible respondents must be at least 30 and have a valid outcome. This valid-label cohort had no missing ages or ages below 30. OHQ850 codes 1 and 2 map to binary 1 and 0; missing and don't-know outcomes are excluded, never guessed. [L6, L12, W1]

Three OHQ870 answers of 9 violated our stated integer 0-to-7 main-analysis rule. The CDC released range includes 0 to 9, so we documented the discrepancy rather than pretending 9 was a refusal code. Those three were excluded from the main analysis and retained for separate review. Cleaning those records is not the same as dropping every person with a missing predictor.

A source-byte audit also found that the installed XPT reader decoded certain actual zero values as an extremely tiny nonzero number. The loader restored zero only after checking the source bytes for the affected fields. That is a decoding correction, not inventing a missing answer. [L12, L13]

## 14 All twelve questionnaire inputs and preprocessing

| Input | Simple meaning |
| --- | --- |
| RIDAGEYR | Age; 80 means age 80 or older |
| RIAGENDR | Recorded sex category in NHANES |
| DMDEDUC2 | Adult education category |
| DMDMARTZ | Marital-status category |
| INDFMPIR | US family income relative to poverty threshold |
| OHQ030 | Time since last dental visit |
| OHQ845 | Self-rated teeth and gum health |
| OHQ860 | Previously told by a dental professional about bone loss around teeth |
| OHQ870 | Days of interdental cleaning during the previous seven days |
| OHQ835 | Respondent thinks they might have gum disease |
| DIQ010 | Self-reported diabetes category |
| SMOKING_STATUS | Derived smoking category |

These meanings and legal codes were checked against CDC documentation. OHQ850 is not in the input table. SEQN and survey-design fields are also not predictors. [W1, W7, W8, W9, L13]

We start with 13 raw predictor fields. SMQ020 and SMQ040 become one smoking field, leaving 12 conceptual inputs. Fewer than 100 lifetime cigarettes, former smoking and current smoking are the three known smoking states. Fewer than 100 lifetime cigarettes is not identical to never having smoked. Respondents who answer No to the lifetime question skip the follow-up by design; a skipped question is not a random unanswered current-smoking question.

**Missing value** means an answer is unavailable. **Median imputation** fills a numeric input using the middle observed fitting value. A **missing indicator** records that an input was missing. For categories we retain an explicit unknown category. We never impute the outcome.

**One-hot encoding** turns a category into separate numeric flags. If smoking has known categories plus unknown, the model receives category indicators rather than interpreting arbitrary category numbers as distances. Together with numeric fields and missing indicators, the pipeline produces 47 encoded columns. That does not mean the user answers 47 questions.

**Scaling** adjusts numeric ranges using fitted statistics. Logistic Regression benefits from a common scale; the shared explicit pipeline preserves a reproducible input contract. It is not a new clinical transformation. Imputer, scaler and encoder fitting occurs only inside the appropriate development fitting data, never using scoring/Test answers.

The two awareness-related inputs OHQ835 and OHQ860 may be closely associated with receiving or remembering treatment. We therefore also compared an **ablation** removing them: 10 conceptual inputs and 41 encoded columns. Performance changed, showing dependence on those inputs. It does not prove those questions cause treatment. [L13, L14]

## 15 Questionnaire models training and final evaluation

**Logistic Regression** is a regularized binary prediction model. It combines encoded inputs into a score and uses a sigmoid to produce a probability. Despite the word regression, here it estimates a binary label. Its regularization helps control overly large coefficients. It is an understandable baseline, not a deliberately weak opponent.

**XGBoost** builds an ensemble of decision trees sequentially. Later trees improve the objective using information about earlier errors. A tree contains conditional decisions; tree depth limits how complex each tree can become. The frozen primary was Full profile A: depth 2, learning rate 0.05, 200 trees and reg_lambda 1.0. Two hundred trees is not two hundred neural epochs. [L14, W10]

The **training-rate baseline** returns the same probability for every person, using 1,553 Yes labels among 6,251 development participants, about 24.84%. A useful method should be compared with such a simple reference.

We first compared settings on development folds, investigated full versus awareness-ablated features, and examined calibration and threshold workflows. That history does not mean every explored option was deployed. The final frozen primary remained raw XGBoost A and the comparator raw full Logistic C1, with no additional calibration mapping.

**Freeze** means recording the exact models, preprocessing, membership, cutoffs and protocol before final evaluation. With separate owner approval, the final Test ran once on 1,563 people: 388 reported Yes and 1,175 No. Do not rerun this final evaluation or change settings because of its results. [L3]

| Frozen Test model | AUROC | Brier | Cutoff | Sensitivity | Specificity |
| --- | ---: | ---: | ---: | ---: | ---: |
| XGBoost primary | 0.7607 | 0.1509 | 0.26 | 0.5593 | 0.8357 |
| Logistic comparator | 0.7561 | 0.1514 | 0.28 | 0.5412 | 0.8315 |
| Constant training rate | 0.5000 | 0.1866 | 0.50 | 0.0000 | 1.0000 |

At the frozen XGBoost cutoff, true negatives are 982, false positives 193, false negatives 171 and true positives 217. These concern reported treatment history. They are not counts of clinically examined periodontal disease.

The 0.26 and 0.28 cutoffs were selected from development data using a stated Youden-J rule. They are statistical demonstration cutoffs, not clinical operating recommendations. The interface can show probabilities without making a clinical Yes/No decision.

The XGBoost AUROC conditional 95% interval is 0.7334 to 0.7889. The paired XGBoost-minus-Logistic interval includes zero, so a clear overall winner is not established. The overall 0.80 feasibility target was not achieved. AUROC is not percent accuracy.

**Bootstrap** means repeatedly resampling evaluation records to inspect variation in a statistic. The report used 1,000 paired participant resamples. These intervals are conditional on the fitted models and do not include all development-selection, complex-survey or external-population uncertainty.

**Calibration slope and intercept** were examined descriptively: XGBoost slope 1.2441 and intercept 0.2473. These diagnostics did not change any predictions. The constant baseline's trapezoidal PR-AUC looks high because of tied-score curve interpolation; it is not useful ranking skill. Its AUROC remains 0.5. [L3]

**Survey sensitivity and subgroups:** a separate development-only survey-weight point analysis was already completed on 6,251 respondents, using saved predictions with no new fits. Its design coverage was 24 strata and 49 stratum-PSU pairs. A stratum is a survey sampling layer; a PSU is a primary sampling unit. This analysis was not survey-weighted model training or nationally representative inference. Complex-survey variance remains unresolved. Development age/recorded-sex reports and predefined final-Test subgroup diagnostics also exist; group scores do not certify fairness, and a good subgroup cannot replace the overall score. [L3, L18]

## 16 SHAP and what if explained with the actual demo

### SHAP

**SHAP** assigns feature contributions to a model output relative to a defined base. A classroom analogy is explaining which parts of a bill add to its total. The allocation depends on the model and explanation formulation; it is not proof of a biological cause. **TreeSHAP** calculates these contributions for tree models. [W11]

Our XGBoost explanation uses raw log-odds. **Odds** compares probability of Yes to probability of No. **Log-odds** is the logarithm of that ratio. **Sigmoid** converts log-odds back to a probability. You do not need to memorize the algebra to understand that these are different units.

The important reconstruction is: base log-odds plus all contributions equals the model's raw log-odds, within a stated numerical tolerance. Then sigmoid gives the displayed probability. We group the encoded columns into 12 conceptual input contributions, retaining their total.

The existing fictional example has base approximately -1.1117 and final raw log-odds approximately -1.3005. The resulting probability is 0.21408096, displayed as 21.41%. Twelve contribution rows were verified. A SHAP value of +0.20 log-odds does not mean +20 probability percentage points. [L15]

### What if

A **what-if scenario** changes selected answers and runs the same frozen model again. It does not learn a new model or forecast future health. The original profile stays separate so we can compare and reset it.

Only smoking status and interdental-cleaning days may change. Age, recorded sex, other history and the original lifetime-smoking information stay fixed. The simulator checks whether a requested smoking change is consistent with that original information. It rejects illegal fields, missing model identity, stale requests and invalid cleaning days.

In the verified fictional example, original probability is 21.41%. Setting cleaning days to 7 gives 24.41%. Reset restores exactly 21.41%. The difference is about +3.00 percentage points. It does not show cleaning worsens health: the model learned observational treatment-history patterns, not the causal effect of cleaning.

**Support warning** means a requested category or smoking/cleaning pair has few development examples. The current count threshold of 20 is a UI heuristic, not a validated clinical reliability rule. Seeing many examples of that pair alone also does not prove the whole profile is well represented. [L15, L16]

**Tamil English:** "Answer maathina model number maarudhu. Adhu namma future health maariyachu-nu artham illa."

## 17 The software tools and what each one is doing

**Python** is the main data/model language. **pandas** reads and joins tables. **NumPy** handles numeric arrays. **scikit-learn** supplies preprocessing, Logistic Regression, folds and metrics. **XGBoost** supplies boosted trees. **SHAP** supplies tree explanations. **joblib** stores and loads the tabular pipeline.

**PyTorch** builds neural networks, calculates gradients and updates weights. **torchvision** provides the named image architectures and official weight definitions. **Pillow** reads and prepares image files. The project also has colour-processing and annotation helpers; installing a package alone does not mean every API is used by every model.

**CPU** is the general processor. **GPU** accelerates suitable tensor work. **CUDA** is NVIDIA's GPU platform. **MPS** is Apple's acceleration backend. Google Colab supplied Tesla T4 execution for selected runs. The current EfficientNet live adapter uses CPU; original EfficientNet adaptation ran on Mac MPS. Hardware differences can affect numerical details and cannot be treated as an isolated model-quality explanation.

**FastAPI** provides local HTTP endpoints. **Uvicorn** serves the application. **React** implements the interactive page. **JSX** is the React source syntax. A **frontend bundle** is browser-ready JavaScript generated from that source. The real backend, not a hardcoded browser number, runs the predictions.

**API** means an agreed way for programs to exchange requests and responses. **JSON** is the structured text format used for many responses. A **schema** declares required fields and legal shapes. **HTTP 200** indicates a successful request; an expected 422 can mean the application correctly rejected invalid input. A green HTTP status alone does not prove the prediction is clinically correct.

**Virtual environment** keeps Python dependencies together. The current local launch uses .venv even though the initial plan called the environment venv. **Git** tracks source history; a **branch** isolates a line of work; a **commit** records a snapshot. Dataset files and model weights remain outside commits under ignored directories. This report task did not commit or push.

## 18 The current application and exact demonstration identity

Current proposal demo address: **http://127.0.0.1:8773/**. The local host address means this computer. Use the versioned launcher from the repository root: `zsh scripts/run_pp1_proposal_demo.sh`. This is a launch instruction, not a training command. Earlier 8770 and 8771 instructions describe previous demo versions. [L2]

| Current live workflow | Role | Explanation or extra output |
| --- | --- | --- |
| EfficientNet-B0 neural fold 0 | Main Vision candidate | Original, predicted-class heatmap and overlay |
| ResNet50 v3 | Vision baseline | Original, predicted-class heatmap and overlay |
| YOLO ROI v1 plus ResNet18 | Additional experiment | Tooth boxes and crop grades |
| ROI v2 CORAL | Additional experiment | Tooth boxes and ordinal crop grades |
| Questionnaire XGBoost | Independent tabular workflow | SHAP, restricted what-if and reset |

So there are **four live Vision pipelines plus one questionnaire pipeline**, five live end-to-end workflows. This is not five independent model architecture names: the ROI workflows each contain a detector and classifier. The original proposal model families are four: EfficientNet, ResNet, XGBoost and Logistic, plus two simple reference baselines. Different folds, saved epochs and training arms create multiple checkpoints, not automatically new architecture families.

The live EfficientNet is an existing fold0_last_block/final.pt checkpoint. It fitted 544 images. Its saved SHA begins b557f52e and all 360 training-state tensor hashes matched during integration verification. This is the 46.76% pooled neural workflow, not the 52.21% frozen-feature Logistic workflow. The latter has no packaged final fitted Logistic classifier for arbitrary new-photo use. [L2]

On one permitted owner photo the four Vision outputs were EfficientNet grade 3, ResNet grade 3, ROI v1 maximum grade 3 with 12 boxes, and CORAL maximum grade 2 with 12 boxes. Those predictions do not tell us which model was correct; a qualified reference label was not established for that demonstration.

**Doctor Review Mode** asks for an independent assessment before showing AI outputs. **Developer Mode** marks an unreviewed demonstration. A mode label does not verify professional credentials. Genuine clinician review remains pending. One model's failure should not erase the other models' results.

Photos are processed locally under the current consent gate and are not automatically retained by the application. Feedback export is explicit and excludes photo content and identifying input fields under its allowlist. Free text still requires care: do not type patient identifiers. Local processing is not a claim of comprehensive privacy certification or production readiness.

## 19 Important code files explained by blocks

### Tabular data blocks

**src/tabular/audit_nhanes.py:** loads the source tables, checks fields and SEQN, repairs only source-verified zero decoding, selects valid outcomes, performs checked joins, and writes aggregate counts. The reason is to know exactly who entered the study before fitting a model. Its report is audit history; do not rerun it merely to reopen the project.

**src/tabular/preprocess_nhanes.py:** derive_smoking_status implements skip logic; clean_cohort applies known special-code and range rules; model_inputs uses an explicit predictor allowlist; split_participants preserves the frozen split; make_preprocessor constructs fitting-only imputing, encoding and scaling. Its key idea is that output labels and scoring data cannot sneak into the predictor pipeline.

**src/tabular/logistic_comparison_nhanes.py and xgboost_comparison_nhanes.py:** create fresh pipelines inside folds, fit prespecified settings and report OOF results. Fresh preprocessing per fold prevents scoring rows from influencing imputation and scaling. Historical result reports remain records, not orders to repeat those experiments.

### Tabular prediction blocks

**src/tabular/questionnaire_explain.py:** validate_profile checks the 12 inputs and rejects IDs/outcome fields; explain_frame runs preprocessing, probability and TreeSHAP; encoded_groups collects encoded contributions into conceptual fields; support_warnings describes sparse observed input support. The simulator restricts editable fields and reset reuses the original profile.

**src/tabular/finalise_development.py and evaluate_frozen_tabular.py:** preparation/freezing and final evaluation have separate roles. The evaluation path uses frozen models and an already-consumed one-run authorization. Do not remove its persistent claim to make the final exam run again.

### Vision and application blocks

**src/vision/efficientnet_adaptation_v1.py:** implements the separately authorized two-arm, five-fold neural experiment. Protocol bindings, allowed memberships, frozen states, epoch limits and saved OOF records make the experiment reviewable. A reporting-only fix recovered its completed outputs; it did not improve learned weights.

**src/vision/efficientnet_live.py:** loads the pinned fold-0 neural checkpoint, checks expected hashes/provenance, builds the known architecture and shares the existing decoding/Grad-CAM runtime. The main idea is to load the intended model rather than any file with a plausible name. It does not train on import or on upload.

**src/vision/local_photo_upload_demo.py and photo_explanation.py:** prepare the supported uploaded pixels, preserve the trained input pathway, run the model and align the genuine explanation. Altering preprocessing would change the experiment, so model and input identity are kept explicit.

**src/vision/roi_tooth_v1_live.py and roi_ordinal_v2_live.py:** adapt the verified returned detector/classifier pairs for independent local research inference. They do not turn boxes into clinical segmentation masks or blend their grades with the whole-photo models.

**src/tabular/api.py:** defines prediction, what-if, reset and separate photo routes; checks consent/input errors; returns structured results; isolates unavailable runtimes. Main endpoints include /api/predict, /api/what-if, /api/reset and /api/vision/efficientnet-photo. The API is communication code, not a separate scientific model.

**src/tabular/ui/DoctorVision.jsx and App.jsx:** control the page, questionnaire, candidate/baseline ordering, independent model states and feedback. Clearing stale results is important: an old image's answer must not stay visible as if it belonged to a newly selected photo.

**scripts/run_pp1_proposal_demo.sh:** checks the intended local port and launches the current existing checkpoints. **docs/** stores reports and logs. **data/** and **models/** hold ignored local artifacts. **notebooks/** contains Colab workflows. The owner's architecture diagram should be drawn manually from this understanding, as required by AGENTS.md.

## 20 What was verified and what was not

A **unit test** checks a small behaviour. An **integration test** checks interacting parts. A **browser check** exercises what a user can click and see. A **smoke test** checks basic operation. An independent metric recomputation checks saved predictions using a separate calculation. A **synthetic fixture** is deliberately artificial test input, not a new real dental example.

The latest EfficientNet integration report records 40 focused tests and 40 browser assertions passed. It also records 39 protected artifact hashes unchanged. These are checks for that integration task; do not sum every historical suite as if they were unique independent scientific experiments. The final questionnaire evaluation has its own 109 saved-evidence checks. [L2, L3]

A **hash** is a content fingerprint. Matching SHA-256 hashes support file identity and integrity. They do not prove that a label is clinically right. **CRC** checks archive integrity. **Provenance** records where a source/checkpoint/result came from. Those checks help reproduce and defend our work.

**Tolerance** allows small expected numerical differences. The integration originally failed an overly strict ordinary-inference versus gradient-enabled threshold of 1e-7. Final checks used independent gradient parity and the existing 1e-6 float32 inference bound. Model weights, inputs and heatmaps were not modified to manufacture a pass. Preserving that failure record is part of honest research.

We have not established healthy whole-image detection, robust grade-1/2 recognition, verified participant independence, clinically valid heatmap localization, a completed human study, or production deployment. Software checks cannot supply those missing kinds of evidence.

## 21 What failed and what we learned

The earliest ResNet head-only pilot predicted grade 4 for all 53 Validation cases. Weighted loss changed the distribution but did not solve recognition. Fine-tuning v3 increased correct predictions yet remained weak on scarce grades. These experiments show measured behaviour, not proof of one causal explanation for all errors.

EfficientNet adaptation slightly improved its matched head-only control, from 315 to 318 correct OOF images. It did not beat the historical feature/Logistic workflow. A new architecture or extra training stage does not guarantee better overall performance.

CORAL raised grade-2 recognition compared with its matched CE arm but reduced grade-3 recognition and got one fewer whole image correct overall. Ordered classification is a reasonable research idea; the actual trade-off remains mixed.

The ROI context diagnostic reproduced 48 training crops from four fitting-only photos. Existing crops already contained visible gum margins in examples. Expanding padding from 15% to 30% on one fixed scoring fold increased correct photos from 84 to 85 out of 136, but Macro-F1 fell from 0.3347 to 0.2980 and grade-2 recall fell from 1/17 to 0/17. The expanded setting was not adopted. Its 62.50% is not a new 680-image accuracy. [L17]

The local 15% diagnostic matched 128/136 historical hard predictions; the cause of eight disagreements across hardware/runtime remains unisolated. We do not describe it as exact historical replication. A future matched training study would answer a different question from this frozen-weight input change.

The most important research habit is to report a negative or mixed result honestly. We cannot keep inspecting Test, invent healthy images, clear uncertain labels ourselves or try endless settings until a preferred percentage appears.

## 22 What is complete what is pending and what you should do

| Area | Completed evidence | Still needed |
| --- | --- | --- |
| Questionnaire | Audit, cleaning, comparisons, final evaluation, SHAP, what-if and development survey point sensitivity | Rehearsal, genuine feedback, external validation and complex-survey variance |
| Vision data | Source preparation, annotation checks and provisional cohort | Qualified label decisions, participant/group resolution and missing whole-image grade-0 evidence |
| Vision models | Bounded ResNet, EfficientNet and ROI experiments | Approved final cohort/protocol and valid final evaluation |
| Current demo | Four Vision routes and questionnaire flow integrated | Owner rehearsal, genuine doctor/user review and handling any observed failures |
| Explanations | Numerical Grad-CAM and TreeSHAP consistency checks | Clinical attention assessment and demonstrated user understanding |
| Research records | Reports, preserved failures and provenance | Owner's own understanding notes and supervisor decisions |

The 76-case fitting review queue contains nine grade-1 and 67 grade-2 cases. Reviewer and verified-grade fields are blank. A queue is preparation for review, not 76 new labels. Qualified reviewers must supply real decisions. The 181 holds and protected Test boundary remain intact. [L17]

**Your immediate work before PP1:** open the current 8773 demo; rehearse one permitted photo through all four cards; explain why outputs stay independent; run the fictional questionnaire, SHAP, scenario and reset; record genuine feedback without identifiers; read the result tables aloud; and prepare honest answers about weak grades and unverified explanations.

**Research work after the demonstration:** obtain qualified annotation and group decisions, resolve feasibility of all intended grades, freeze a defensible cohort/protocol, and run only separately authorized experiments. A final all-development refit and final Vision Test need their own scientific decision. More epochs alone are not the default next step.

**External images or AI services:** do not assume an internet photo is permitted clinical data or that Personal Gemini processing has been authorized. Earlier external-release/privacy questions were unresolved. Verify source rights, consent, metadata, participant tracking and any institutional requirements before a new external-data or upload workflow.

**Your responsibility:** understand the purpose, input/output, important blocks, results and limits; run the existing demo; make owner decisions truthfully; obtain qualified help where required; and explain accepted AI assistance. An assistant can prepare code and explanations, but cannot truthfully fill "what I understood" or a clinician's review for you.

## 23 A simple five minute presentation script

**Minute 1 purpose:** "My Component 2 has two independent branches. One estimates visible gingival inflammation from a photograph. The other estimates self-reported previous gum treatment from questionnaire answers. These are different outcomes and are never fused."

**Minute 2 Vision:** "EfficientNet-B0 is our proposal candidate and ResNet50 the baseline. Both were trained in bounded exploratory experiments. The current demo loads an existing EfficientNet fold-0 checkpoint and ResNet v3. ROI v1 and CORAL v2 are additional experiments. Grades and model attention are shown separately."

**Minute 3 results:** "The live EfficientNet neural workflow has 46.76% pooled 680-image OOF accuracy. Its 52.21% feature-plus-Logistic result is a different workflow. ROI v1 has 60.74% accuracy in that matched image table, but it still fails scarce grades. ResNet v3's 50.94% uses 53 Validation images and is not directly ranked with those OOF scores."

**Minute 4 questionnaire:** "The cleaned NHANES cohort has 7,814 participants. We froze 6,251 for development and 1,563 for final evaluation. XGBoost AUROC was 0.7607, not 76% accuracy. TreeSHAP explains log-odds contributions. The scenario changes only smoking or cleaning and demonstrates model sensitivity, not a health benefit."

**Minute 5 limitations and next work:** "The local software works, but qualified image labels, participant independence, healthy-image support and clinical attention remain unresolved. I will present actual results and the two functioning workflows, obtain genuine review and proceed to final Vision work under an approved protocol."

**Tamil English short version:** "Namma AI number mattum kaattala; andha number enna meaning, evvalavu correct, edhai vechu sonnadhu, enna limitations irukku-nu explain pannrom."

## 24 Viva questions with short answers

**What is your exact contribution?** Component 2's independent Vision and questionnaire pipelines, evaluation, explanations, restricted scenario interaction and local interface, with recorded data/protocol limits.

**Why two branches?** They answer different questions using unpaired datasets. Combining them would invent patient linkage and a combined target that our data do not support.

**What is an epoch?** One complete pass through a fit's training examples. Repeating the same examples is not collecting more unique images.

**What is the difference between a batch and a fold?** A batch is a small processing group within fitting. A fold defines which examples fit and which score one model in cross-validation.

**Did both image architectures actually train?** Yes. ResNet head and fine-tuning experiments completed; EfficientNet head-only and final-block/head experiments also completed. Their outputs and identities were preserved.

**How many images trained the live EfficientNet?** Its fold-0 checkpoint fitted 544. The experiment's pooled OOF report covers the same 680 Training images across five folds, not a final all-680 refit.

**Why is 52.21% not displayed as live EfficientNet accuracy?** That result belongs to frozen features plus nested Logistic Regression. The live neural arm's pooled result is 46.76%.

**Which model has the highest measured image accuracy?** ROI v1 at 60.74% in the specified same-680 comparison. This is not an across-grade reliability or clinical-best claim.

**Why keep EfficientNet as candidate?** It is the proposed method being investigated. Candidate role does not guarantee it will beat the baseline. We must report the measured result.

**Why not compare 50.94% and 46.76% directly?** The former uses 53 reused Validation images and the latter 680 OOF images with different fitting/evaluation procedures. A fair comparison must control the evaluation boundary.

**Why use Macro-F1?** It gives each evaluated grade equal weight, so frequent grade-4 examples cannot hide failure on rare grades as easily as overall accuracy.

**What is the purpose of a majority baseline?** It reveals how well a trivial class-frequency rule scores. A complex model should not be credited merely for exploiting imbalance.

**Why no grade-0 claim?** The current whole-image experimental cohort has no supported grade-0 examples. A normal-looking individual tooth does not establish a healthy photograph.

**Is Grad-CAM a segmentation mask?** No. It is coarse model attention for a selected class. Attention computation can pass while clinical localization remains poor.

**What if the heatmap highlights the lip?** Show it honestly and explain the unresolved attention problem. Do not repaint it to suggest anatomical correctness.

**What does OHQ850 mean?** A respondent's report of previous gum-disease treatment. It is our outcome only, not an input or current-disease label.

**Why did we use left joins?** To preserve eligible outcome respondents when a secondary questionnaire module is absent, while checking identifiers to prevent duplicate rows.

**Why 12 inputs but 47 features?** Encoding categorical answers and adding missing indicators expand the model's numeric representation; the user still supplies 12 conceptual fields.

**Why not fill missing outcomes?** Guessing the answer we are learning would invent labels and distort evaluation. Missing predictors are handled separately with fitting-only rules.

**What does AUROC 0.7607 mean?** It summarizes binary score ranking across thresholds for the treatment-history outcome. It is not 76.07% accuracy or diagnostic certainty.

**Did XGBoost clearly beat Logistic?** Its point AUROC was slightly higher, but the paired uncertainty interval includes zero. A clear overall superiority was not established.

**What unit does SHAP use here?** Raw log-odds. We check that the base plus contributions reconstructs the raw output and sigmoid reproduces probability.

**Does a positive SHAP value prove a cause?** No. It describes the fitted model's contribution under the explanation formulation, not a causal intervention effect.

**Why can more cleaning produce a higher score?** The model estimates observational treatment-history patterns. Changing a form answer is not a future-health experiment.

**Why freeze before final Test?** To avoid choosing settings from final evaluation answers. The questionnaire final Test permission was consumed; it must not be repeated for tuning.

**Are Vision labels clinically approved?** Final qualified decisions are still pending. Existing experiments are provisional and the held cases remain held.

**Do software tests prove medical accuracy?** No. They establish specified computational and interface behaviours. Clinical and generalization evidence require other studies.

**Did the current UI integration improve accuracy?** No. It exposed an existing verified checkpoint through the interface without retraining or changing the scientific results.

**What do you still need to do yourself?** Explain the work in my own words, rehearse, inspect actual outputs, record genuine feedback and obtain needed qualified/supervisor decisions.

## 25 A to Z project word dictionary

Use this as a lookup section. The fuller explanations and project examples are in the earlier sections.

### A

**Ablation:** remove or change one declared component to inspect its contribution. Our awareness ablation removes two questionnaire inputs; it does not prove causality.

**Accuracy:** fraction of evaluated labels predicted correctly. Always name the sample and evaluation method beside it.

**Activation:** an internal network response to an input. A response is not automatically a medically meaningful feature.

**Adam and AdamW:** optimizers that update trainable neural weights using gradients; AdamW includes a decoupled weight-decay formulation.

**Annotation:** recorded label or spatial region supplied with data. Annotation quality still needs audit.

**API:** interface letting the browser request a prediction from backend code.

**Artificial intelligence:** broad area of computer systems performing tasks associated with intelligent behaviour; our project uses specific learned prediction methods within it.

**Architecture:** the model's structural design, such as EfficientNet-B0; not a particular trained checkpoint.

**AUROC:** area under the receiver-operating-characteristic curve, describing ranking across thresholds.

**Augmentation:** deliberate training-image transformations. Our specified bounded experiments did not automatically use arbitrary augmentation.

### B

**B1:** the project's versioned image colour/input preparation pathway. Its identity matters because changing inputs can change predictions.

**Backbone:** image network part extracting representations before the final classifier.

**Backpropagation:** calculating gradients backward through operations so permitted weights can be updated.

**Baseline:** a reference method used to judge whether a candidate provides useful improvement.

**Batch and batch size:** a group processed together and its number of examples; different from a fold or epoch.

**BatchNorm:** normalization layers with learned parameters and running statistics that must be handled correctly when freezing/evaluating.

**Binary classification:** prediction between two labels, here reported treatment Yes versus No.

**Bootstrap:** repeated resampling to inspect uncertainty in a statistic; does not manufacture new real participants.

**Brier score:** a probability-error measure; lower is better under the same definition and task.

### C

**Calibration:** agreement between predicted probabilities and observed label frequencies in appropriate evaluation groups.

**Candidate:** method proposed for investigation, not a predeclared performance winner.

**Caption:** descriptive text accompanying an image; our primary image-grade evidence comes from captions.

**Checkpoint:** saved model state from a specific fit/epoch, with identity and provenance.

**Class and class imbalance:** an output category and unequal numbers of examples across categories.

**Class weight:** fitting-loss emphasis assigned to classes; it does not create scarce examples.

**Classifier head:** final network part mapping extracted features to class scores.

**CNN:** convolutional neural network, a network using spatial filters on images.

**Cohort:** the defined group of people or records included under stated eligibility rules.

**Confusion matrix:** counts showing actual labels against predicted labels.

**Consent:** genuine permission for a stated use; a software checkbox does not supply missing research ethics or data rights.

**CORAL:** ordinal classification using ordered threshold questions in our crop-model experiment.

**CPU CUDA and cross validation:** respectively a general processor, NVIDIA GPU computing platform, and a controlled rotating fitting/scoring procedure.

### D

**Data leakage:** evaluation information influencing fitting or selection in a way that overstates independent performance.

**Dataset:** a collection of examples; repeated epochs over it do not increase its unique size.

**Decoder:** software converting stored image/data bytes into usable numbers. A decoding error is different from a missing answer.

**Deep learning:** machine learning using multi-layer neural networks, including our image CNNs.

**Detection:** locating regions with boxes; different from assigning disease grades or outlining gum tissue.

**Development set:** records available for model development, including internal folds and appropriate selection.

**Dropout:** training-time stochastic deactivation used as regularization; evaluation must use the intended mode.

### E

**Early stopping:** stopping under a declared development-improvement rule rather than always reaching the epoch cap.

**EfficientNet B0:** the named proposal image candidate architecture; actual dental performance must be measured.

**Encoding:** transforming category values into a numeric representation a model can use.

**Ensemble:** multiple components combined under a specified method; XGBoost's trees form an ensemble. Our two research branches are not fused.

**Epoch:** one pass through a fit's training examples.

**Evaluation:** measuring a fixed method on a named dataset boundary using stated metrics.

**EXIF:** image metadata that can include orientation and other information requiring appropriate handling.

### F

**F1 and Macro F1:** precision/recall combination, and its equal-grade average over the evaluated grade set.

**False positive and false negative:** an actual No predicted Yes, and an actual Yes predicted No, for the defined binary label.

**Feature:** input information or a learned representation; a feature is not necessarily a user-visible question.

**Fine tuning:** allowing selected pretrained neural weights to adapt to the new fitting task.

**Fit:** one execution of learning parameters from a specified fitting dataset.

**Float32:** a finite-precision numeric representation; tiny arithmetic differences need justified tolerances.

**Fold:** one partition role in cross-validation; our five-fold image experiment scores 136 of 680 per fit.

**Freeze:** keep a protocol or parameter state fixed. Say which one: frozen backbone, frozen model choice and frozen Test protocol are different uses.

### G

**Generalization:** useful performance on suitable new observations beyond fitting examples.

**Git and Gitignore:** version control and rules excluding local artifacts such as data and weights from tracking.

**GPU:** processor designed for parallel numerical work; speed does not imply greater clinical accuracy.

**Gingiva:** gums; gingival inflammation is not by itself a measurement of all supporting tissue damage.

**Grad CAM:** a gradient-based coarse attention view for a selected predicted class.

**Gradient:** local sensitivity of an objective/output to a numeric input or parameter.

**Ground truth:** a reference answer used for evaluation; provisional annotations are not automatically unquestionable clinical truth.

**Grouped split:** partitioning linked observations together to reduce overlap leakage under the known grouping evidence.

### H

**Hash:** content fingerprint used to check file/model identity, not medical correctness.

**Head only:** train the classifier while the feature-extracting backbone stays fixed.

**Held out:** reserved from the relevant fitting/selection process. Identify whether it is a fold score, Validation or final Test boundary.

**Heatmap:** coloured display of spatial values; our Grad-CAM heatmap shows model attention, not clinical borders.

**HTTP:** request/response protocol used by the local browser and server.

**Hyperparameter:** an experiment setting such as learning rate or tree depth, rather than a number learned directly inside one fit.

### I

**ICC:** profile information defining image colour interpretation.

**ImageNet:** source of general pretrained image weights, not our dental training dataset.

**Imputation:** explicit handling of missing predictor values using fitting-only information; never used to invent our outcome.

**Inference:** generating outputs with fixed learned weights, including current demo predictions.

**Input and output:** what goes into the function and what comes back.

**Integration:** connecting existing components, such as a trained checkpoint to an API and page; not automatically new training.

**IoU:** intersection over union, an overlap measure for predicted and reference regions.

### J

**Joblib:** a Python persistence tool used for serialized tabular pipelines.

**Join:** matching records using a linkage key; SEQN joins the same NHANES respondent across files.

**JSON:** a structured text format for requests, responses and some metadata files.

### K

**K fold:** cross-validation with K scoring partitions; here K equals five in the discussed image OOF experiments.

**Kappa:** agreement relative to a chance reference; our QWK also accounts for ordered disagreement size.

### L

**Label:** the answer a model is fitted or evaluated against; must have known meaning and provenance.

**Layer:** one stage of network computation. More layers do not guarantee better results on this cohort.

**Learning rate:** optimizer step-size control; not accuracy or number of epochs.

**Left join:** preserve the starting cohort while attaching matched secondary fields.

**Letterbox:** fit an image into a required canvas with padding while retaining shape proportions.

**Logistic Regression:** regularized binary model that maps an encoded-input score through a sigmoid.

**Logit and log odds:** raw model scores; binary log-odds and probability use different units.

**Loss:** numerical penalty optimized during fitting; training loss and held-out classification accuracy answer different questions.

### M

**Macro:** equal averaging across the defined classes, not weighting each class by its frequency.

**Machine learning:** learning a prediction rule from examples; includes our tree, Logistic and neural methods.

**Manifest:** saved source or split-membership description that makes the intended records explicit.

**mAP:** detection-quality summary; cannot be relabelled as MGI classification accuracy.

**Median:** middle observed fitting value used by our numeric missing-input handling.

**Metric:** a defined evaluation measure; changing metrics can change what looks best.

**MGI:** Modified Gingival Index, the visible-inflammation grade scheme underlying our image target.

**Model and model weights:** a prediction rule and its learned parameter values; code architecture and trained weights are different artifacts.

**MPS:** Apple's numerical acceleration backend, used for specified local runs.

### N

**NaN:** a common missing-numeric marker; not the same as a real zero.

**Nested cross validation:** internal model-setting selection inside each outer fitting fold, followed by outer scoring.

**Neural network:** connected numerical operations with learnable parameters; a tool, not a source of clinical authority.

**NHANES:** the US survey supplying our independent questionnaire data.

**NMS:** non-maximum suppression, a detector step reducing overlapping competing box predictions.

**Normalization:** preparing numeric scales; image channel normalization and tabular scaling have different definitions.

### O

**OHQ850:** the previous-gum-treatment outcome, never a predictor in our model.

**One hot:** categorical encoding using separate indicator columns.

**OOF:** out-of-fold predictions, scored by a model that did not fit on that record within the declared fold.

**Optimizer:** algorithm updating trainable parameters from gradients.

**Ordinal:** categories with a meaningful order, such as our increasing MGI grades.

**Overfitting:** fitting details that fail to generalize adequately.

### P

**Padding:** added spatial context or canvas space; changing crop padding changes model inputs.

**Parameter:** a model number learned during fitting, such as a weight or tree score.

**Participant:** a person represented in the data; one person may have several image records.

**Patience:** number of tolerated non-improving checks under an early-stopping rule.

**Periodontal:** relating to tissues around and supporting teeth. Our photograph grade does not establish periodontitis diagnosis or staging.

**Pipeline:** defined sequence of preparation, model and output steps.

**Pixel and pooling:** an image location's channel values, and a spatial summarization operation in a network.

**Precision and recall:** how many predicted positives are right, and how many actual positives are found.

**Predictor:** allowed information used to estimate the outcome; outcome and linkage IDs are excluded.

**Preprocessing:** preparing raw inputs according to a fixed, reproducible contract.

**Pretrained:** initialized using earlier learning on another dataset; does not mean already trained for our dental target.

**PSU:** primary sampling unit in a survey design. Survey clustering is different from artificial model-training batches.

**Probability and percentage point:** a zero-to-one output scale, and the arithmetic difference between percentages. 21% to 24% is +3 percentage points.

**Provenance:** recorded source and processing history for evidence and artifacts.

### Q

**Quality assurance:** checks on data/code/output integrity, not automatic clinical label approval.

**Questionnaire:** the separate structured-answer branch; it does not estimate the same target as the image branch.

**QWK:** quadratic weighted kappa, an ordered agreement metric.

### R

**Raw margin:** XGBoost's score before conversion through sigmoid; TreeSHAP currently explains this log-odds scale.

**Recalibration:** fitting a mapping to adjust probability behaviour; no extra mapping was deployed in our final raw primary model.

**Regex:** text-pattern matching used to extract candidate grade mentions from captions.

**Regularization:** constraints or penalties intended to control excessive model complexity.

**Re inference:** predict again using the same model after a permitted input change; not retraining.

**ResNet:** residual neural architecture family; ResNet50 whole-photo and ResNet18 crop classifiers are distinct.

**RGB and ROI:** red-green-blue image channels, and a selected region of interest.

### S

**Schema:** required field/type/category definition for input or output.

**Seed:** controls specified random choices, while software/hardware details can still matter.

**Segmentation:** assigning region membership at pixel level; neither tooth boxes nor Grad-CAM alone are verified gum segmentation.

**Sensitivity and specificity:** correct-positive rate and correct-negative rate for the defined binary label/cutoff.

**SEQN:** NHANES respondent identifier used for linkage, not prediction.

**SHAP:** feature-contribution explanation relative to a defined base, not a causal-effect measure.

**Sigmoid and softmax:** mappings from raw scores to binary probability or multiclass score vectors respectively.

**SMOTE:** synthetic minority oversampling; not our default solution and not a source of real independent clinical observations.

**Split and stratification:** assigning observations to roles, and preserving label proportions where specified.

**Stratum:** a sampling layer in the survey design. This is a different concept from a stratified machine-learning label split.

**sRGB:** a common colour space; assuming it for an untagged image must be explicit.

**Survey weights:** quantities used in population-oriented survey analysis; different from class weights in model loss and not model predictors here.

**Synthetic fixture:** artificial test input; do not count it as a real patient or study photo.

### T

**Target:** the exact outcome being estimated, such as OHQ850 or image maximum MGI.

**Tensor:** a numeric array with dimensions, such as channel by height by width.

**Test set:** reserved final-evaluation records under a stated frozen protocol.

**Threshold:** cutoff converting a score into a binary decision; it changes sensitivity/specificity trade-offs.

**Tolerance:** justified numeric acceptance bound, not a way to hide a substantive model error.

**Training and transfer learning:** adjusting permitted parameters from labels, and starting from representations learned on a different dataset.

**TreeSHAP:** tree-specific SHAP computation; our implementation verifies raw-output additivity.

**True positive and true negative:** correctly predicted Yes and correctly predicted No for the defined label.

### U

**Underfitting:** insufficient learning of useful structure under the chosen method; not established from one weak score alone.

**Unknown category:** explicit representation for unavailable categorical input, not a newly observed known smoking state.

**UI and Uvicorn:** the user interface and the server process supporting our local FastAPI application.

### V

**Validation:** development scoring used under a stated selection rule; not automatically an untouched final Test.

**Version:** named identity for code, data policy or artifact so different results are not silently mixed.

**Virtual environment:** isolated Python dependency environment, currently .venv for the local launcher.

**Visualization:** display of values, such as attention; visual appearance alone cannot prove scientific correctness.

### W

**Weight and weight decay:** a learned neural parameter, and a regularization control; neither is the same as a NHANES survey weight.

**What if:** constrained model-sensitivity re-inference, not forecasting or treatment-effect estimation.

**Workflow:** the complete procedure being assessed; changing the classifier head or evaluation boundary can create a different workflow using the same backbone.

### X

**XGBoost:** sequential boosted-tree method used for the questionnaire candidate.

**XPT:** source table-file format used for the NHANES modules.

**XAI:** explainable artificial intelligence, methods helping inspect model behaviour without automatically proving its reasoning clinically right.

### Y

**YOLO:** object detector in the extra tooth-ROI experiments; its box quality is separate from crop/photo grade accuracy.

**Youden J:** sensitivity plus specificity minus one, the development threshold criterion used in our frozen questionnaire procedure.

### Z

**Zero decoding correction:** source-verified repair of a reader's interpretation of actual zero bytes; not missing-value imputation.

**Zero leakage claim:** a statement requiring precise evidence and scope. Saved split/hash checks reduce specific risks; they do not prove every unknown participant relationship has been resolved.

## 26 Evidence sources and a reading plan

The document uses short evidence IDs so you can find the underlying record in this repository. Local paths below are relative to the repository root. Status statements refer to 18 October 2026; historical reports retain their original dates and should not be silently rewritten.

### Local project evidence

- L1 AGENTS.md and docs/component2_project_handoff.md: scope, restrictions and latest reconciled project status.
- L2 docs/vision_efficientnet_live_integration_v1.md: current four-model proposal demo, exact EfficientNet checkpoint, actual outputs and verification.
- L3 docs/tabular_final_test_results_v1.md: frozen final questionnaire sample, performance, intervals and limitations.
- L4 docs/vision_dataset_integrity_audit.md and docs/vision_caption_label_qa.md: source and annotation audits; handoff records current holds and content-review decisions.
- L5 docs/vision_b1_lastblock_results_v3.md: actual ResNet v3 training and 53-Validation results.
- L6 docs/tabular_preprocessing.md: cleaned cohort and frozen participant split.
- L7 docs/vision_efficientnet_adaptation_results_v1.md: actual ten-fit EfficientNet neural comparison and reporting-only recovery.
- L8 docs/vision_roi_tooth_v1_colab_results.md: ROI v1 OOF, detector and annotated-crop results.
- L9 docs/vision_roi_ordinal_v2_colab_results.md: matched v2 CE/CORAL image/crop results and conditional uncertainty.
- L10 docs/vision_photo_model_comparison_v1.json and docs/vision_nested_feature_probe_results_v1.md: same-680 workflow comparison and nested EfficientNet feature/Logistic experiment.
- L11 docs/vision_resnet50_fold0_colab_results_v1.md: separate controlled 136-image ResNet pilot and matched CAM verification.
- L12 docs/nhanes_audit.md: raw module counts, joins, outcome counts and source-byte decoding audit.
- L13 docs/tabular_preprocessing_rules.md: special codes, smoking derivation, allowed fields and fold-local preprocessing.
- L14 docs/tabular_xgboost_comparison.md and docs/tabular_logistic_comparison.md: development configurations, feature ablation and comparison history.
- L15 docs/tabular_demo_rehearsal_v1.md: actual fictional 21.41% to 24.41% to reset demonstration and explanation units.
- L16 src/tabular/questionnaire_explain.py: input validation, additivity, support heuristic and constrained re-inference implementation.
- L17 docs/vision_roi_context_diagnostic_20261018.md: reproduced crops, padding diagnostic and pending grade-1/2 review queue.
- L18 docs/tabular_survey_sensitivity_v1.md and docs/tabular_subgroup_evidence_v1.md: completed development point-weight sensitivity and subgroup summaries, with survey-inference limitations.

### Official and primary references checked for this guide

- W1 [CDC oral health codebook](https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_OHQ.htm): oral-health question definitions and released codes.
- W2 [Mendeley dataset version 1](https://data.mendeley.com/datasets/3253gj88rr/1): dataset identity, description and licence.
- W3 [PyTorch optimization tutorial](https://docs.pytorch.org/tutorials/beginner/basics/optimization_tutorial.html): basic fitting loop terminology.
- W4 [scikit learn cross validation](https://scikit-learn.org/stable/modules/cross_validation.html): fitting/scoring separation and cross-validation concepts.
- W5 [PyTorch transfer learning tutorial](https://docs.pytorch.org/tutorials/beginner/transfer_learning_tutorial.html): pretrained networks and adaptation.
- W6 [Original Grad CAM paper](https://arxiv.org/abs/1610.02391): gradient-based class activation explanation method.
- W7 [CDC demographics codebook](https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_DEMO.htm): demographic fields and survey context.
- W8 [CDC smoking codebook](https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_SMQ.htm): lifetime/follow-up smoking questions and skip logic.
- W9 [CDC diabetes codebook](https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_DIQ.htm): diabetes categories.
- W10 [XGBoost boosted trees introduction](https://xgboost.readthedocs.io/en/stable/tutorials/model.html): tree-ensemble model terminology.
- W11 [SHAP TreeExplainer reference](https://shap.readthedocs.io/en/latest/generated/shap.TreeExplainer.html): tree explanations and output-unit options.
- W12 [NIH NIDCR periodontal disease overview](https://www.nidcr.nih.gov/health-info/gum-disease): basic gum terminology and the distinction between a photo output and professional examination of supporting structures.

### Your learning sessions

**Session 1:** explain the two targets and why there is no fusion. Write your own three sentences.

**Session 2:** use 544 images and batch size 16 to explain batch, epoch and five folds. Say why 50 fit-epochs are not 50 new datasets.

**Session 3:** read the Vision tables. Explain why 60.74% and the minority-grade failures can both be true. Name the exact live EfficientNet workflow.

**Session 4:** follow the NHANES counts from 14,986 rows to 7,814 cleaned participants. Explain outcome versus predictor and 12 versus 47 inputs/features.

**Session 5:** run the fictional questionnaire demonstration and explain log-odds, probability, what-if and reset in your own words.

**Session 6:** rehearse the five-minute script, answer ten random viva questions and record genuine feedback. Put your own understanding in docs/diary.md; leave unanswered concepts as questions rather than copying this report as proof of understanding.

**My explanation in my own words:** ______________________________________________

**The terms I still need help with:** _____________________________________________

**A question I can now answer without reading:** _________________________________
