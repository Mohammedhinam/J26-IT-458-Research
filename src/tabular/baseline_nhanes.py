"""First fixed-configuration baseline, using development-only out-of-fold predictions.

Run: .venv/bin/python -m src.tabular.baseline_nhanes
"""

from datetime import date
from io import BytesIO
import hashlib
import json
import platform
import warnings

import numpy as np
import pandas as pd
import sklearn
from pandas.io.sas.sas_xport import _parse_float_vec
from sklearn.dummy import DummyClassifier
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    auc, average_precision_score, brier_score_loss, confusion_matrix,
    precision_recall_curve, roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline

from .audit_nhanes import DATA_DIR, FILES, ROOT, join_valid_outcomes, markdown_table, restore_xport_zeros
from .preprocess_nhanes import FEATURES, LOCAL_DIR, SEED, clean_cohort, make_preprocessor, model_inputs


THRESHOLD = 0.50  # Fixed before the first run; never selected from these results.
N_FOLDS = 5
MODELS = ("Training-rate dummy", "L2 logistic regression")


def read_development_xpt(path, development_ids):
    """Decode only selected records; scan linkage bytes, not held-out predictors.

    pandas has no row filter for XPORT. Its existing header metadata and IBM
    number decoder let us select SEQN records before normal read_sas decoding.
    These small private-API dependencies are covered by a synthetic XPT test.
    """
    with pd.read_sas(path, format="xport", iterator=True) as metadata:
        start = metadata.record_start
        width = metadata.record_length
        fields = metadata.fields
        seqn = next(field for field in fields if field["name"] == b"SEQN")
        if seqn["ntype"] != "numeric" or seqn["field_length"] != 8 or width <= 80:
            raise ValueError("Unsupported XPT layout for selective development loading")
        total_rows = metadata.nobs

    # Read only the eight linkage bytes per row; seek over all predictor bytes.
    with path.open("rb") as source:
        header = source.read(start)
        identifiers = []
        for row in range(total_rows):
            source.seek(start + row * width + seqn["npos"])
            identifiers.append(source.read(8))
        ids = _parse_float_vec(np.array(identifiers, dtype="S8"))
        if not np.isfinite(ids).all() or (ids <= 0).any() or (ids != np.floor(ids)).any():
            raise ValueError("Invalid SEQN bytes in XPT")
        selected = np.flatnonzero(np.isin(ids, list(development_ids)))
        payload = []
        for row in selected:
            source.seek(start + int(row) * width)
            payload.append(source.read(width))

    # Reuse the original header in memory. No filtered dataset is written.
    records = b"".join(payload)
    padding = b" " * (-len(records) % 80)
    table = pd.read_sas(BytesIO(header + records + padding), format="xport")
    if len(table) != len(selected) or not np.array_equal(table["SEQN"], ids[selected]):
        raise ValueError("Selective XPT decoding changed row membership")
    # Original record indices are needed for the audited source-byte zero check.
    table.index = selected
    restore_xport_zeros(table, path, start, width, fields)
    return table


def load_development(manifest_path=LOCAL_DIR / "split_manifest.json", data_dir=DATA_DIR):
    """Require the existing split; never create a new split or load held-out rows."""
    raw_manifest = manifest_path.read_bytes()
    manifest = json.loads(raw_manifest)
    dev_ids, held_ids = manifest["development"], manifest["held_out"]
    if manifest["seed"] != SEED or manifest["test_size"] != 0.2:
        raise ValueError("Unexpected frozen split settings")
    if not dev_ids or len(set(dev_ids)) != len(dev_ids) or len(set(held_ids)) != len(held_ids):
        raise ValueError("Frozen membership must be nonempty and unique")
    if set(dev_ids) & set(held_ids):
        raise ValueError("Frozen development and held-out IDs overlap")

    tables = {name: read_development_xpt(data_dir / f"{name}.xpt", dev_ids) for name in FILES}
    _, cohort, _ = join_valid_outcomes(tables)
    cleaned, review, log = clean_cohort(cohort)
    if set(cleaned["SEQN"]) != set(dev_ids) or not review.empty or log["age_exclusions"]:
        raise ValueError("Frozen development members no longer match cleaning/label rules")
    development = cleaned.set_index("SEQN").loc[dev_ids]
    x, y = model_inputs(development)
    if manifest_path.read_bytes() != raw_manifest:
        raise ValueError("Frozen split changed during loading")
    return x, y, hashlib.sha256(raw_manifest).hexdigest()


def make_baseline(name):
    """A fresh transformer and classifier for every fold, with fixed settings."""
    if name == MODELS[0]:
        classifier = DummyClassifier(strategy="prior")
    elif name == MODELS[1]:
        # Default L2 (l1_ratio=0); leave class weights unset for this first run.
        classifier = LogisticRegression(C=1.0, solver="lbfgs", max_iter=1000,
                                        class_weight=None, random_state=SEED)
    else:
        raise ValueError(f"Unknown baseline: {name}")
    return Pipeline([("preprocess", make_preprocessor()), ("classifier", classifier)])


def score_predictions(y, probability):
    """Pool one unseen-fold prediction per participant; no threshold tuning."""
    probability = np.asarray(probability)
    if probability.shape != (len(y),) or not np.isfinite(probability).all():
        raise ValueError("Missing or invalid out-of-fold predictions")
    if not np.isin(y, (0, 1)).all() or len(np.unique(y)) != 2:
        raise ValueError("Metrics require both binary outcome classes")
    if ((probability < 0) | (probability > 1)).any():
        raise ValueError("Predictions must be probabilities")
    tn, fp, fn, tp = confusion_matrix(y, probability >= THRESHOLD, labels=[0, 1]).ravel()
    precision, recall, _ = precision_recall_curve(y, probability)
    return {
        "AUROC": float(roc_auc_score(y, probability)),
        "PR-AUC (trapezoidal)": float(auc(recall, precision)),
        "Average precision": float(average_precision_score(y, probability)),
        "Brier": float(brier_score_loss(y, probability)),
        "Sensitivity @0.50": float(tp / (tp + fn)),
        "Specificity @0.50": float(tn / (tn + fp)),
        "TN": int(tn), "FP": int(fp), "FN": int(fn), "TP": int(tp),
    }


def run_oof(x, y):
    """Fit within each training fold, predict its validation fold exactly once."""
    if tuple(x.columns) != FEATURES or not x.index.equals(y.index) or not x.index.is_unique:
        raise ValueError("Expected aligned unique participants and the 12-input allowlist")
    if not y.isin((0, 1)).all() or y.value_counts().reindex([0, 1], fill_value=0).min() < N_FOLDS:
        raise ValueError("Each outcome class needs at least five participants")
    folds = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=SEED)
    probabilities = {name: np.full(len(y), np.nan) for name in MODELS}
    coverage = np.zeros(len(y), dtype=int)
    fold_rows = []
    for number, (train, validation) in enumerate(folds.split(x, y), start=1):
        coverage[validation] += 1
        fold_rows.append((number, len(train), int(y.iloc[train].sum()),
                          len(validation), int(y.iloc[validation].sum())))
        for name in MODELS:
            model = make_baseline(name)
            # A failed/nonconverged fit stops reporting instead of hiding warnings.
            with warnings.catch_warnings():
                warnings.simplefilter("error", ConvergenceWarning)
                model.fit(x.iloc[train], y.iloc[train])
            positive_column = list(model.classes_).index(1)
            probabilities[name][validation] = model.predict_proba(x.iloc[validation])[:, positive_column]
        fold_rows[-1] += (len(model.named_steps["preprocess"].get_feature_names_out()),)
    if not np.all(coverage == 1):
        raise ValueError("Every development participant needs exactly one validation prediction")
    metrics = {name: score_predictions(y, values) for name, values in probabilities.items()}
    return metrics, fold_rows, probabilities


def main():
    x, y, manifest_hash = load_development()
    metrics, folds, _ = run_oof(x, y)
    positive = int(y.sum())
    headers = ("Model", *next(iter(metrics.values())).keys())
    report = [
        f"# First development-only NHANES baseline — {date.today().isoformat()}", "",
        "Command: `.venv/bin/python -m src.tabular.baseline_nhanes`.",
        "Outcome: self-reported previous gum treatment, OHQ850 Yes=1 / No=0. These are internal validation results, not diagnosis or current disease risk.", "",
        "## Fixed experiment design", "",
        "Frozen development membership reused in its saved order. Only SEQN bytes are scanned across source files; only development record payloads are decoded. No held-out labels/predictors are loaded, transformed or evaluated. Original audit/preprocessing reports and split manifest are unchanged.",
        f"Development N={len(y)}; Yes={positive} ({positive / len(y):.6%}); No={len(y)-positive} ({1-positive / len(y):.6%}). Inputs={len(FEATURES)}; encoded column counts across fitted folds={sorted(set(row[5] for row in folds))}.",
        f"Frozen split manifest SHA-256: `{manifest_hash}`.",
        "5-fold StratifiedKFold(shuffle=True, random_state=42); identical folds for both models. Each participant has one out-of-fold probability; metrics pool those probabilities rather than averaging fold metrics.",
        "Every model/fold has a fresh Pipeline: existing numeric median/scaling/missing flags and categorical unknown/one-hot preprocessing, then classifier. No pre-fitted matrix is used.",
        "DummyClassifier(strategy='prior') uses its training-fold positive proportion. LogisticRegression uses fixed L2, C=1.0, lbfgs, max_iter=1000, class_weight=None, random_state=42. No tuning, oversampling or post-hoc calibration; class weighting and regularisation search remain future development experiments.",
        f"Threshold fixed before execution at {THRESHOLD:.2f}; positive if probability >= threshold. It is a demonstration operating point, not a clinical or selected final threshold.",
        "PR-AUC below is trapezoidal area under the precision-recall curve. Average precision is also reported because its step-weighted definition differs from trapezoidal area. Brier is mean squared probability error; lower is better.", "",
        "## Actual pooled out-of-fold results", "",
        markdown_table(headers, [(name, *[f"{value:.6f}" if isinstance(value, float) else value for value in scores.values()]) for name, scores in metrics.items()]), "",
        "## Fold class balance", "",
        markdown_table(("Fold", "Training N", "Training Yes", "Validation N", "Validation Yes", "Encoded columns"), folds), "",
        "## Limits and next step", "",
        "Fold prior probabilities differ slightly, so pooled dummy ranking metrics need not equal exactly 0.5/prevalence; PR trapezoidal interpolation can also exaggerate a constant predictor's area. Compare average precision alongside PR-AUC. No uncertainty intervals, calibration slope/intercept, survey weighting or awareness-feature ablation are claimed in this first experiment.",
        "Next: review these development results, then predefine further development-only regularisation/class-weight/calibration and awareness-feature ablation comparisons. Keep final held-out evaluation deferred until all choices are fixed.",
        f"Runtime: Python {platform.python_version()}; pandas {pd.__version__}; numpy {np.__version__}; scikit-learn {sklearn.__version__}.",
        "XPT selection uses pandas XPORT header metadata/private IBM decoder; unsupported layouts fail explicitly. Synthetic tests guard participant selection and the audited zero repair.",
        "Metric definitions: [sklearn PR curve](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.precision_recall_curve.html), [average precision](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.average_precision_score.html).", "",
    ]
    output = "\n".join(report)
    (ROOT / "docs" / "tabular_baseline.md").write_text(output, encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
