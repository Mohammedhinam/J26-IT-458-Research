"""Compare 12 logistic settings on the frozen development participants only.

Run: .venv/bin/python -B -m src.tabular.logistic_comparison_nhanes
"""

from datetime import datetime
import hashlib
import json
import platform
import warnings
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import sklearn
from sklearn.exceptions import ConvergenceWarning
from sklearn.model_selection import StratifiedKFold

from .baseline_nhanes import (
    MODELS, N_FOLDS, ROOT, SEED, THRESHOLD, load_development,
    make_baseline, markdown_table, score_predictions,
)
from .preprocess_nhanes import FEATURES


EXCLUDED = ("OHQ835", "OHQ860")
FEATURE_SETS = ("Full", "Awareness-ablated")
CONFIGURATIONS = tuple(
    (feature_set, c, weight)
    for feature_set in FEATURE_SETS
    for c in (0.1, 1.0, 10.0)
    for weight in (None, "balanced")
)
BASELINE_CONFIGURATION = ("Full", 1.0, None)
HISTORICAL_REPORT = ROOT / "docs" / "tabular_baseline.md"
REPORT = ROOT / "docs" / "tabular_logistic_comparison.md"


def input_columns(feature_set):
    """Keep the established order; remove only the two authorised awareness fields."""
    if feature_set not in FEATURE_SETS:
        raise ValueError("Unknown feature set")
    if feature_set == "Full":
        return list(FEATURES)
    return [name for name in FEATURES if name not in EXCLUDED]


def make_comparison_pipeline(configuration):
    """Reuse fresh baseline steps; adapt only categories/selectors for ablation."""
    if configuration not in CONFIGURATIONS:
        raise ValueError("Configuration is outside the predefined 12 settings")
    feature_set, c, weight = configuration
    model = make_baseline(MODELS[1])
    model.named_steps["classifier"].set_params(C=c, class_weight=weight)
    if feature_set == "Awareness-ablated":
        processor = model.named_steps["preprocess"]
        transformers = []
        for name, transformer, columns in processor.transformers:
            if name == "categorical":
                encoder = transformer.named_steps["encode"]
                kept = [i for i, column in enumerate(columns) if column not in EXCLUDED]
                encoder.set_params(categories=[encoder.categories[i] for i in kept])
                columns = [columns[i] for i in kept]
            transformers.append((name, transformer, columns))
        processor.set_params(transformers=transformers)
    return model


def metric_text(value):
    """Match the historical report's six decimals and integer confusion counts."""
    return f"{value:.6f}" if isinstance(value, float) else str(value)


def historical_metrics(text):
    """Read the recorded logistic row without rewriting historical evidence."""
    header = next(line for line in text.splitlines() if line.startswith("| Model |"))
    row = next(line for line in text.splitlines() if line.startswith("| L2 logistic regression |"))
    keys = [value.strip() for value in header.split("|")[2:-1]]
    values = [value.strip() for value in row.split("|")[2:-1]]
    if len(keys) != 10 or len(values) != 10:
        raise ValueError("Expected all ten historical baseline metrics/counts")
    return dict(zip(keys, values))


def verify_reproduction(actual, expected):
    """Stop before other configurations if any historical result differs."""
    if set(actual) != set(expected):
        raise ValueError("Baseline metric names differ from historical evidence")
    rows = [(name, expected[name], metric_text(value),
             "MATCH" if metric_text(value) == expected[name] else "MISMATCH")
            for name, value in actual.items()]
    differences = [f"{name}: expected {old}, found {new}" for name, old, new, result in rows
                   if result == "MISMATCH"]
    if differences:
        raise ValueError("Baseline reproduction failed; remaining configurations not run:\n" + "\n".join(differences))
    return rows


def fit_configuration(x, y, folds, configuration):
    """Fresh train-fold fit, then one unseen-fold probability per participant."""
    columns = input_columns(configuration[0])
    selected = x.loc[:, columns]
    probability = np.full(len(y), np.nan)
    coverage = np.zeros(len(y), dtype=int)
    encoded_counts = []
    for train, validation in folds:
        if np.intersect1d(train, validation).size:
            raise ValueError("Training and validation rows overlap")
        model = make_comparison_pipeline(configuration)
        with warnings.catch_warnings():
            warnings.simplefilter("error", ConvergenceWarning)
            model.fit(selected.iloc[train], y.iloc[train])
        positive = list(model.classes_).index(1)
        probability[validation] = model.predict_proba(selected.iloc[validation])[:, positive]
        coverage[validation] += 1
        encoded_counts.append(len(model.named_steps["preprocess"].get_feature_names_out()))
    if not np.all(coverage == 1) or len(set(encoded_counts)) != 1:
        raise ValueError("Expected one OOF prediction per participant and a fixed feature schema")
    return score_predictions(y, probability), probability, encoded_counts[0]


def run_comparison(x, y, reference):
    """Materialise the original folds once; gate all other fits on reproduction."""
    if tuple(x.columns) != FEATURES or not x.index.equals(y.index) or not x.index.is_unique:
        raise ValueError("Expected aligned development participants and the existing input allowlist")
    if not y.isin((0, 1)).all() or y.value_counts().reindex([0, 1], fill_value=0).min() < N_FOLDS:
        raise ValueError("Each binary class needs at least five participants")
    folds = tuple(StratifiedKFold(N_FOLDS, shuffle=True, random_state=SEED).split(x, y))
    results, predictions, widths = {}, {}, {}

    # Run the reproduction setting first; reuse its result as one of the twelve.
    baseline, probability, width = fit_configuration(x, y, folds, BASELINE_CONFIGURATION)
    reproduction = verify_reproduction(baseline, reference)
    results[BASELINE_CONFIGURATION] = baseline
    predictions[BASELINE_CONFIGURATION] = probability
    widths[BASELINE_CONFIGURATION] = width
    for configuration in CONFIGURATIONS:
        if configuration == BASELINE_CONFIGURATION:
            continue
        scores, probability, width = fit_configuration(x, y, folds, configuration)
        results[configuration] = scores
        predictions[configuration] = probability
        widths[configuration] = width
    return results, predictions, widths, folds, reproduction


def main():
    historical = HISTORICAL_REPORT.read_text()
    reference = historical_metrics(historical)
    x, y, manifest_hash = load_development()
    if manifest_hash not in historical:
        raise ValueError("Frozen membership hash differs from the historical baseline report")
    results, _, widths, folds, reproduction = run_comparison(x, y, reference)
    fold_rows = [(i, len(train), int(y.iloc[train].sum()), len(validation), int(y.iloc[validation].sum()))
                 for i, (train, validation) in enumerate(folds, start=1)]
    membership = [[int(x.index[position]) for position in validation] for _, validation in folds]
    fold_hash = hashlib.sha256(json.dumps(membership).encode()).hexdigest()
    headers = ("Features", "C", "Class weight", "Inputs", "Encoded", *reference.keys())
    rows = [(setting[0], setting[1], str(setting[2]), len(input_columns(setting[0])), widths[setting],
             *[metric_text(value) for value in results[setting].values()]) for setting in CONFIGURATIONS]
    # A development candidate only: the plan's AP/Brier/C/weight tie-break order.
    candidate = min(CONFIGURATIONS, key=lambda setting: (
        -results[setting]["Average precision"], results[setting]["Brier"],
        setting[1], setting[2] is not None, FEATURE_SETS.index(setting[0]),
    ))
    report = [
        f"# Development-only logistic comparison — {datetime.now(ZoneInfo('Asia/Kolkata')).date()}", "",
        "Command: `.venv/bin/python -B -m src.tabular.logistic_comparison_nhanes`.",
        "Outcome: self-reported previous gum treatment (OHQ850 Yes=1 / No=0). Internal development comparison only.", "",
        "## Configuration and preservation", "",
        f"Development participants: {len(y)}; Yes: {int(y.sum())} ({y.mean():.6%}); No: {int((y == 0).sum())}.",
        "Twelve L2 settings: C=0.1/1/10 × class_weight=None/balanced × full/awareness-ablated inputs. Ablation excludes only OHQ835 and OHQ860; cohort and outcome are identical.",
        "Fresh baseline preprocessing + LogisticRegression inside each fold; lbfgs, max_iter=1000, random_state=42. Balanced weights are calculated by sklearn from training-fold labels only. No pre-fitted matrix, oversampling or calibration.",
        f"The existing five stratified folds are regenerated once using the same saved participant order, shuffle=True and seed={SEED}, then reused for every configuration. Every participant has one OOF probability per configuration. Metrics pool OOF predictions using the unchanged baseline scoring function; threshold={THRESHOLD:.2f}, positive if probability >= threshold.",
        f"Frozen split SHA-256: `{manifest_hash}`. Ordered validation-fold SEQN membership SHA-256: `{fold_hash}`.",
        "Reused selective XPT loading and source-byte-verified zero repair. No held-out predictor/label payload is loaded or evaluated; only linkage SEQN bytes are scanned to select development records. No manifest, historical code/report, dataset or model is written. Participant predictions remain in memory only.", "",
        "## Actual pooled OOF results", "", markdown_table(headers, rows), "",
        "PR-AUC is trapezoidal precision-recall area; Average precision uses its separate step-weighted definition. Sensitivity/specificity and confusion counts use the fixed comparison threshold 0.50.", "",
        "## Baseline reproduction gate", "",
        "Full inputs, C=1.0, class_weight=None ran first. All ten historical results MATCH at six decimals (counts exactly); only then were the other eleven configurations run.",
        markdown_table(("Metric", "Historical", "Reproduced", "Result"), reproduction), "",
        "## Identical fold class balance", "",
        markdown_table(("Fold", "Training N", "Training Yes", "Validation N", "Validation Yes"), fold_rows), "",
        "## Interpretation and future work", "",
        f"Highest pooled OOF Average Precision candidate: {candidate[0]}, C={candidate[1]}, class_weight={candidate[2]}. This is a development candidate, not the final model. The documented selection rule uses AP, then Brier, smaller C and no weights; an exact remaining feature-set tie prefers Full for deterministic ordering.",
        "Selecting among twelve configurations on the same development OOF results introduces selection optimism. These point estimates are not unbiased final-performance estimates or evidence of clinical validity. Awareness ablation is a model-dependence comparison, not a causal analysis. Balanced-weight outputs are not claimed to be calibrated.",
        "Threshold 0.50 remains comparison-only; no final threshold was selected or optimised. Uncertainty intervals, calibration slope/intercept and survey-weighted sensitivity are not evaluated here.",
        "Next according to the proposal: predefine and implement the controlled development-only XGBoost comparison against Logistic Regression and the training-rate baseline on the same folds and both feature sets. Calibration and threshold selection must remain development-only, with final held-out evaluation deferred until choices are frozen.",
        f"Runtime: Python {platform.python_version()}; pandas {pd.__version__}; numpy {np.__version__}; scikit-learn {sklearn.__version__}.",
        "Sources: comparison plan 8aa77fd; explicit 12-configuration task; supplied Component 2 proposal pages 20–22. Historical report: docs/tabular_baseline.md. Test/owner-review records: docs/diary.md and docs/ai_log.md.", "",
    ]
    output = "\n".join(report)
    REPORT.write_text(output, encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
