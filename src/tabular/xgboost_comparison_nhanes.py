"""Run the approved eight-setting development-only XGBoost comparison.

Run: .venv/bin/python -B -m src.tabular.xgboost_comparison_nhanes
"""

from datetime import datetime
import hashlib
import json
import platform
import re
import warnings
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import sklearn
import xgboost
from sklearn.model_selection import StratifiedKFold
from xgboost import XGBClassifier

from .baseline_nhanes import N_FOLDS, ROOT, SEED, THRESHOLD, load_development, markdown_table, score_predictions
from .logistic_comparison_nhanes import FEATURE_SETS, historical_metrics, input_columns, make_comparison_pipeline, metric_text
from .preprocess_nhanes import FEATURES


PROFILES = {
    "A": dict(max_depth=2, learning_rate=0.05, n_estimators=200, reg_lambda=1.0),
    "B": dict(max_depth=3, learning_rate=0.05, n_estimators=200, reg_lambda=1.0),
    "C": dict(max_depth=3, learning_rate=0.10, n_estimators=100, reg_lambda=1.0),
    "D": dict(max_depth=3, learning_rate=0.05, n_estimators=200, reg_lambda=5.0),
}
FIXED_SETTINGS = dict(
    booster="gbtree", objective="binary:logistic", tree_method="hist", device="cpu",
    random_state=42, n_jobs=1, eval_metric="logloss", reg_alpha=0.0, gamma=0.0,
    min_child_weight=1.0, max_delta_step=0.0, subsample=1.0,
    colsample_bytree=1.0, colsample_bylevel=1.0, colsample_bynode=1.0,
    scale_pos_weight=1.0, grow_policy="depthwise", max_bin=256, base_score=None,
    early_stopping_rounds=None, validate_parameters=True, verbosity=1,
)
CONFIGURATIONS = tuple((feature_set, profile) for feature_set in FEATURE_SETS for profile in PROFILES)
PLAN = ROOT / "docs" / "tabular_xgboost_plan.md"
BASELINE_REPORT = ROOT / "docs" / "tabular_baseline.md"
LOGISTIC_REPORT = ROOT / "docs" / "tabular_logistic_comparison.md"
REPORT = ROOT / "docs" / "tabular_xgboost_comparison.md"


def verify_plan(text):
    """Fail on a changed approved profile or fixed-settings table before training."""
    for profile, settings in PROFILES.items():
        row = next(line for line in text.splitlines() if line.startswith(f"| {profile} |"))
        values = [cell.strip() for cell in row.split("|")[2:6]]
        actual = [int(values[0]), float(values[1]), int(values[2]), float(values[3])]
        if actual != list(settings.values()):
            raise ValueError(f"Written plan differs from approved profile {profile}")
    required_rows = (
        "| booster / objective | gbtree / binary:logistic |",
        "| tree_method / device | hist / cpu |",
        "| random_state / n_jobs | 42 / 1 |",
        "| eval_metric | logloss |",
        "| reg_alpha / gamma | 0.0 / 0.0 |",
        "| min_child_weight / max_delta_step | 1.0 / 0.0 |",
        "| subsample | 1.0 |",
        "| colsample_bytree / colsample_bylevel / colsample_bynode | 1.0 / 1.0 / 1.0 |",
        "| scale_pos_weight | 1.0 (unweighted first comparison) |",
        "| grow_policy / max_bin | depthwise / 256 |",
        "| base_score | None; installed-version automatic estimation from training-fold labels only |",
        "| early_stopping_rounds | None; fixed tree counts, no validation eval_set |",
        "| validate_parameters / verbosity | True / 1 |",
    )
    if any(row not in text for row in required_rows):
        raise ValueError("Written fixed settings differ from the approved plan")
    if xgboost.__version__ != "3.4.1":
        raise ValueError("Installed XGBoost differs from the approved 3.4.1 environment")


def make_xgboost_pipeline(configuration):
    """Keep existing fold preprocessing/ablation; replace only the classifier."""
    if configuration not in CONFIGURATIONS:
        raise ValueError("Configuration is outside the approved eight settings")
    feature_set, profile = configuration
    model = make_comparison_pipeline((feature_set, 1.0, None))
    classifier = XGBClassifier(**FIXED_SETTINGS, **PROFILES[profile])
    return model.set_params(classifier=classifier)


def fold_fingerprint(x, folds):
    membership = [[int(x.index[position]) for position in validation] for _, validation in folds]
    return hashlib.sha256(json.dumps(membership).encode()).hexdigest()


def run_comparison(x, y, expected_fold_hash):
    """Verify original folds, then fit forty fresh train-only Pipelines."""
    if tuple(x.columns) != FEATURES or not x.index.equals(y.index) or not x.index.is_unique:
        raise ValueError("Expected aligned development participants and the existing input allowlist")
    if not y.isin((0, 1)).all() or y.value_counts().reindex([0, 1], fill_value=0).min() < N_FOLDS:
        raise ValueError("Each binary class needs at least five participants")
    folds = tuple(StratifiedKFold(N_FOLDS, shuffle=True, random_state=SEED).split(x, y))
    if fold_fingerprint(x, folds) != expected_fold_hash:
        raise ValueError("Fold membership differs from Logistic evidence; refusing to train")

    results, predictions, widths = {}, {}, {}
    for configuration in CONFIGURATIONS:
        selected = x.loc[:, input_columns(configuration[0])]
        probability = np.full(len(y), np.nan)
        coverage = np.zeros(len(y), dtype=int)
        encoded_counts = []
        for train, validation in folds:
            model = make_xgboost_pipeline(configuration)
            # Scored validation rows are never passed to fit or early stopping.
            with warnings.catch_warnings():
                warnings.simplefilter("error", UserWarning)
                model.fit(selected.iloc[train], y.iloc[train])
            classifier = model.named_steps["classifier"]
            if classifier.get_booster().num_boosted_rounds() != PROFILES[configuration[1]]["n_estimators"]:
                raise ValueError("Fitted estimator count differs from the approved profile")
            positive = list(model.classes_).index(1)
            probability[validation] = model.predict_proba(selected.iloc[validation])[:, positive]
            coverage[validation] += 1
            encoded_counts.append(len(model.named_steps["preprocess"].get_feature_names_out()))
        if not np.all(coverage == 1) or len(set(encoded_counts)) != 1:
            raise ValueError("Expected one OOF prediction per participant and a fixed feature schema")
        results[configuration] = score_predictions(y, probability)
        predictions[configuration] = probability
        widths[configuration] = encoded_counts[0]
    return results, predictions, widths, folds


def reference_row(text, header_prefix, row_prefix, metric_names):
    """Read existing rounded reference results; do not rerun or rewrite them."""
    header = next(line for line in text.splitlines() if line.startswith(header_prefix))
    row = next(line for line in text.splitlines() if line.startswith(row_prefix))
    names = [cell.strip() for cell in header.split("|")[1:-1]]
    values = [cell.strip() for cell in row.split("|")[1:-1]]
    if len(names) != len(values):
        raise ValueError("Reference report table is malformed")
    cells = dict(zip(names, values))
    return [cells[name] for name in metric_names]


def main():
    plan_text = PLAN.read_text()
    verify_plan(plan_text)
    historical, logistic = BASELINE_REPORT.read_text(), LOGISTIC_REPORT.read_text()
    metric_names = tuple(historical_metrics(historical))
    reference_rows = [
        ("Logistic Full C=1/None (primary)", *reference_row(logistic, "| Features |", "| Full | 1.0 | None |", metric_names)),
        ("Logistic Ablated C=1/None (primary)", *reference_row(logistic, "| Features |", "| Awareness-ablated | 1.0 | None |", metric_names)),
        ("Prior Dummy (feature-independent)", *reference_row(historical, "| Model |", "| Training-rate dummy |", metric_names)),
        ("Logistic Full C=0.1/balanced (secondary development-selected AP leader)", *reference_row(logistic, "| Features |", "| Full | 0.1 | balanced |", metric_names)),
    ]
    fold_match = re.search(r"Ordered validation-fold SEQN membership SHA-256: `([a-f0-9]{64})`", logistic)
    if fold_match is None:
        raise ValueError("Missing historical fold fingerprint")
    x, y, manifest_hash = load_development()
    if manifest_hash not in historical or manifest_hash not in logistic:
        raise ValueError("Frozen split differs from baseline/Logistic evidence")
    results, _, widths, folds = run_comparison(x, y, fold_match.group(1))
    profile_rows = [(name, *settings.values()) for name, settings in PROFILES.items()]
    result_rows = [(feature_set, profile, len(input_columns(feature_set)), widths[(feature_set, profile)],
                    *[metric_text(value) for value in results[(feature_set, profile)].values()])
                   for feature_set, profile in CONFIGURATIONS]
    balances = [(i, len(train), int(y.iloc[train].sum()), len(validation), int(y.iloc[validation].sum()))
                for i, (train, validation) in enumerate(folds, start=1)]
    reached = [f"{feature_set}/{profile}" for (feature_set, profile), scores in results.items() if scores["AUROC"] >= 0.80]
    remaining_defaults = {name: value for name, value in XGBClassifier().get_params().items()
                          if name not in FIXED_SETTINGS and name not in PROFILES["A"]}
    report = [
        f"# Approved development-only XGBoost comparison — {datetime.now(ZoneInfo('Asia/Kolkata')).date()}", "",
        "Command: `.venv/bin/python -B -m src.tabular.xgboost_comparison_nhanes`.",
        "Owner approved profiles A–D, both feature sets and the plan's fixed settings before implementation. The original proposal-plan file is preserved; its pending status describes the pre-approval stage.",
        "Outcome: self-reported previous gum treatment, OHQ850 Yes=1 / No=0; binary:logistic produces probabilities. No diagnosis or current-disease-risk claim.", "",
        "## Approved settings and validation", "",
        markdown_table(("Profile", "max_depth", "learning_rate", "n_estimators", "reg_lambda"), profile_rows), "",
        f"Participants: {len(y)} development; Yes={int(y.sum())} ({y.mean():.6%}); No={int((y == 0).sum())}. Full/ablated inputs exclude only OHQ835/OHQ860 for ablation. Five-fold StratifiedKFold(shuffle=True, random_state=42), original saved order; 8 configurations × 5 folds = 40 XGBoost fits.",
        f"Frozen manifest SHA-256: `{manifest_hash}`. Ordered validation-fold membership SHA-256: `{fold_fingerprint(x, folds)}` — MATCH to Logistic evidence before training.",
        "Every fit reused fresh existing preprocessing/ablation steps with a fresh XGBClassifier. Medians/scaling/encoding and automatic base score learned from training rows only. No validation eval_set, early stopping, class-weight search, resplitting or pre-fitted development matrix. Errors/warnings stop reporting instead of silently changing approved settings.",
        "Reused selective XPT loading/zero repair; no held-out predictor/label payload loaded, decoded, transformed or evaluated. Historical reports and manifest remain unchanged. OOF predictions/models stay in memory; no datasets or model artifacts are written.",
        f"All metrics use the existing scorer and pooled OOF predictions, one per participant/configuration. Threshold={THRESHOLD:.2f} for comparison only; PR-AUC is trapezoidal, Average Precision is separately defined. No final threshold selection or calibration.", "",
        "Shared explicit settings:", "", "```json", json.dumps(FIXED_SETTINGS, indent=2, sort_keys=True), "```", "",
        "Other installed classifier defaults (null delegates to XGBoost defaults; NaN denotes the missing-value marker):", "",
        "```text", json.dumps(remaining_defaults, indent=2, sort_keys=True), "```", "",
        "## Actual XGBoost OOF results — all eight configurations", "",
        markdown_table(("Features", "Profile", "Inputs", "Encoded", *metric_names), result_rows), "",
        "## Preserved Logistic and Dummy references", "",
        "Historical rounded OOF measurements reused below, not retrained. Both primary Logistic rows are C=1/None; all twelve original Logistic results remain in docs/tabular_logistic_comparison.md. The secondary AP-leading row is development-selected, not a final model. Dummy uses training-fold priors and is feature-independent.",
        markdown_table(("Reference", *metric_names), reference_rows), "",
        "## Identical fold class balance", "",
        markdown_table(("Fold", "Training N", "Training Yes", "Validation N", "Validation Yes"), balances), "",
        "## Limitations and remaining work", "",
        "All eight settings are reported. Choosing between these settings or between XGBoost and the development-selected Logistic configurations using the same OOF results introduces selection optimism. These are internal point estimates, not unbiased final-test estimates or evidence of clinical validity. No final winning model is declared.",
        "Probability calibration is unverified: Brier measures probability error, but calibration slope/intercept and reliability curves are not evaluated here. No calibrated personal-probability claim. Awareness ablation is a dependence comparison, not causal evidence; profile C jointly changes learning rate/tree count and cannot isolate either effect.",
        f"Measured development configurations with AUROC >=0.80: {', '.join(reached) if reached else 'none'}. This is a provisional feasibility target, not clinical validation or a final-test result.",
        "Remaining proposal work: development-only calibration/operating-point decisions, uncertainty and survey-weighted sensitivity analysis, SHAP/what-if and independent vision work. Keep final held-out evaluation reserved until configurations/calibration/threshold are frozen.",
        f"Runtime: Python {platform.python_version()}; pandas {pd.__version__}; numpy {np.__version__}; scikit-learn {sklearn.__version__}; XGBoost {xgboost.__version__}.",
        "Sources: owner-approved docs/tabular_xgboost_plan.md; supplied Component 2 proposal pages 21–22; historical baseline/Logistic reports. No installation, commit or push.", "",
    ]
    output = "\n".join(report)
    REPORT.write_text(output, encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
