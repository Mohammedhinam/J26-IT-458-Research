# EfficientNet cached-feature class-weight comparison — prospective v1

2026-10-16 · branch vinuthan. Owner explicitly asked to continue the proposed balanced-versus-unweighted comparison. One bounded local execution; not clinical label/final model approval.

Freeze before fitting: exactly 680 original Training records, provisional MGI 1–4 support 12/84/223/361, known content groups and prior five folds (SHA e202132b8b7ee38ec4041ea399bccb0b538ef75ce1861faec044292c11cf90d4). No source images, 53 Validation, 181 held, NP015, CAM or Test payloads. Read only the existing numeric EfficientNet cache and saved OOF evidence.

Reference: EfficientNet_B0_Weights.IMAGENET1K_V1 frozen 1,280 features; saved balanced C=1 OOF. Features SHA d8cda6807e7954e2dd8d7cf20be77b46e5063f89910436df294381901231d838; prior results SHA d450ea6a9e21d560a3e21b51df707a538b676783575e9ebe25b4d3ca84bf0eb8; OOF SHA c78fd5be1507c0e4b18b9cafff2a8f63ef12fac2d584c1fea52d1ae1b863d8cb.

Only new setting: class_weight=None. Keep C=1, lbfgs, max_iter=2000, seed42; fresh StandardScaler and classifier within each fitting fold. Exactly five new fits; no balanced refit, neural optimization, hyperparameter search, thresholds, calibration or automatic retry. Stop on convergence/non-finite/hash/fold failures.

Report pooled OOF accuracy, macro-F1, balanced accuracy, QWK, ordinal MAE, within-one accuracy, per-grade recall/confusion, macro OVR AUROC and multiclass Brier. Compare new unweighted predictions against cached balanced/majority/prior. Show 1,000 seed42 paired content-group bootstrap differences for accuracy, macro-F1, balanced accuracy, QWK and Brier. Conditional intervals omit refitting, unknown participants and prior selection; no automatic winner or promise that accuracy will improve.

Freeze current code/config/cache/reference/fold/path bindings in a truthful new scope before reading feature values. Use a fresh ignored output directory. Record focused generated tests and independent saved-result checks. Keep old evidence and final research-training gates unchanged; no commit/push, installation/download or new image inference.
