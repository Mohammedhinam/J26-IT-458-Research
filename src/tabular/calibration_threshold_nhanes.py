"""Approved development-only calibration and demonstration-threshold validation.

Run: .venv/bin/python -B -m src.tabular.calibration_threshold_nhanes
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
from sklearn.calibration import CalibratedClassifierCV
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, train_test_split

from .baseline_nhanes import ROOT, SEED, load_development, markdown_table, score_predictions
from .logistic_comparison_nhanes import input_columns, make_comparison_pipeline
from .preprocess_nhanes import FEATURES
from .xgboost_comparison_nhanes import fold_fingerprint, make_xgboost_pipeline, verify_plan as verify_xgboost_plan


CANDIDATES = tuple((family, features) for family in ("Logistic", "XGBoost")
                   for features in ("Full", "Awareness-ablated"))
VERSIONS = ("Raw", "Sigmoid")
WORKFLOWS = tuple((*candidate, version) for candidate in CANDIDATES for version in VERSIONS)
GRID = np.arange(101) / 100.0
EPSILON = 1e-6
BOOTSTRAPS = 1000
INTERVAL_METRICS = ("AUROC", "PR-AUC (trapezoidal)", "Average precision", "Brier",
                    "Sensitivity @0.50", "Specificity @0.50", "Sensitivity learned", "Specificity learned")
REPORT = ROOT / "docs" / "tabular_calibration_threshold_results.md"


def operating_metrics(y, predicted):
    """Score classifications without changing the historical 0.50 scorer."""
    y, predicted = np.asarray(y), np.asarray(predicted)
    if y.shape != predicted.shape or y.ndim != 1 or not np.isin(y, (0, 1)).all():
        raise ValueError("Expected aligned binary labels/predictions")
    if not np.isin(predicted, (0, 1)).all() or len(np.unique(y)) != 2:
        raise ValueError("Operating metrics require binary predictions and both classes")
    tn = int(np.sum((y == 0) & (predicted == 0)))
    fp = int(np.sum((y == 0) & (predicted == 1)))
    fn = int(np.sum((y == 1) & (predicted == 0)))
    tp = int(np.sum((y == 1) & (predicted == 1)))
    return {"Sensitivity": tp / (tp + fn), "Specificity": tn / (tn + fp),
            "TN": tn, "FP": fp, "FN": fn, "TP": tp}


def select_threshold(y, probability):
    """Maximise tuning-pool J; exact ties prefer recall then larger threshold."""
    y, probability = np.asarray(y), np.asarray(probability)
    if y.shape != probability.shape or not np.isfinite(probability).all():
        raise ValueError("Invalid tuning probabilities")
    if ((probability < 0) | (probability > 1)).any():
        raise ValueError("Tuning probabilities must be in [0, 1]")
    best = None
    for threshold in GRID:
        scores = operating_metrics(y, probability >= threshold)
        positives, negatives = scores["TP"] + scores["FN"], scores["TN"] + scores["FP"]
        # J = (TP * negatives - FP * positives) / (positives * negatives).
        numerator = scores["TP"] * negatives - scores["FP"] * positives
        key = (numerator, scores["TP"], float(threshold))
        if best is None or key > best[0]:
            best = (key, {"threshold": float(threshold), "J": numerator / (positives * negatives),
                          "useful": numerator > 0})
    return best[1]


def make_candidate(candidate):
    family, features = candidate
    if candidate not in CANDIDATES:
        raise ValueError("Candidate is outside the approved shortlist")
    if family == "Logistic":
        return make_comparison_pipeline((features, 1.0, None))
    return make_xgboost_pipeline((features, "A"))


def fit_fold(candidate, pool_x, pool_y, tuning_x, tuning_y, validation_x, inner_folds):
    """Outer validation labels are deliberately absent from this fit/tune API."""
    ids = (set(pool_x.index), set(tuning_x.index), set(validation_x.index))
    if any(ids[i] & ids[j] for i, j in ((0, 1), (0, 2), (1, 2))):
        raise ValueError("Pool, tuning and validation participants must be disjoint")
    if not pool_x.index.equals(pool_y.index) or not tuning_x.index.equals(tuning_y.index):
        raise ValueError("Pool/tuning labels are misaligned")
    calibrator = CalibratedClassifierCV(
        estimator=make_candidate(candidate), method="sigmoid", cv=inner_folds,
        ensemble=False, n_jobs=1,
    )
    with warnings.catch_warnings():
        warnings.simplefilter("error", UserWarning)
        calibrator.fit(pool_x, pool_y)
    if len(calibrator.calibrated_classifiers_) != 1:
        raise ValueError("Expected one refitted base/calibrator pair")
    # This exact fitted object is also the raw reference; never refit it separately.
    raw = calibrator.calibrated_classifiers_[0].estimator
    output = {}
    for version, estimator in (("Raw", raw), ("Sigmoid", calibrator)):
        positive = list(estimator.classes_).index(1)
        tuning_probability = estimator.predict_proba(tuning_x)[:, positive]
        decision = select_threshold(tuning_y, tuning_probability)
        probability = estimator.predict_proba(validation_x)[:, positive]
        output[version] = (probability, probability >= decision["threshold"], decision)
    return output, calibrator


def run_validation(x, y, expected_fold_hash):
    """Freeze outer/inner memberships once, shared by every candidate/version."""
    if tuple(x.columns) != FEATURES or not x.index.equals(y.index) or not x.index.is_unique:
        raise ValueError("Expected aligned unique development rows and the existing allowlist")
    if not y.isin((0, 1)).all() or y.value_counts().reindex([0, 1], fill_value=0).min() < 5:
        raise ValueError("Each class needs at least five participants")
    outer = tuple(StratifiedKFold(5, shuffle=True, random_state=SEED).split(x, y))
    if fold_fingerprint(x, outer) != expected_fold_hash:
        raise ValueError("Outer folds differ from historical evidence; refusing to fit")
    probabilities = {key: np.full(len(y), np.nan) for key in WORKFLOWS}
    learned = {key: np.zeros(len(y), dtype=bool) for key in WORKFLOWS}
    thresholds = {key: [] for key in WORKFLOWS}
    coverage = np.zeros(len(y), dtype=int)
    dummy = np.full(len(y), np.nan)
    partitions = []
    for number, (training, validation) in enumerate(outer, start=1):
        pool, tuning = train_test_split(training, test_size=0.2, random_state=SEED, stratify=y.iloc[training])
        inner = tuple(StratifiedKFold(3, shuffle=True, random_state=SEED).split(x.iloc[pool], y.iloc[pool]))
        membership = {"pool": x.index[pool].tolist(), "tuning": x.index[tuning].tolist(),
                      "inner_validation": [x.index[pool][indices].tolist() for _, indices in inner]}
        digest = hashlib.sha256(json.dumps(membership).encode()).hexdigest()
        partitions.append((number, len(pool), int(y.iloc[pool].sum()), len(tuning),
                           int(y.iloc[tuning].sum()), len(validation), int(y.iloc[validation].sum()), digest))
        dummy[validation] = y.iloc[pool].mean()
        coverage[validation] += 1
        for candidate in CANDIDATES:
            columns = input_columns(candidate[1])
            selected = x.loc[:, columns]
            output, fitted = fit_fold(candidate, selected.iloc[pool], y.iloc[pool],
                                     selected.iloc[tuning], y.iloc[tuning], selected.iloc[validation], inner)
            base = fitted.calibrated_classifiers_[0].estimator
            if len(base.named_steps["preprocess"].get_feature_names_out()) != (47 if candidate[1] == "Full" else 41):
                raise ValueError("Unexpected full/ablated feature schema")
            for version, (probability, predicted, decision) in output.items():
                key = (*candidate, version)
                probabilities[key][validation] = probability
                learned[key][validation] = predicted
                thresholds[key].append((number, decision["threshold"], decision["J"], decision["useful"]))
    if not np.all(coverage == 1) or any(not np.isfinite(p).all() for p in probabilities.values()):
        raise ValueError("Incomplete or duplicate outer-OOF prediction coverage")
    return probabilities, learned, thresholds, partitions, dummy


def workflow_metrics(y, probability, learned):
    result = score_predictions(y, probability)
    result.update({name + " learned": value for name, value in operating_metrics(y, learned).items()})
    return result


def calibration_diagnostic(y, probability):
    """Descriptive joint intercept/slope only; do not recalibrate scored outputs."""
    y, probability = np.asarray(y), np.asarray(probability)
    clipped = np.clip(probability, EPSILON, 1 - EPSILON)
    count = int(np.sum(clipped != probability))
    logit = np.log(clipped / (1 - clipped))
    result = {"intercept": np.nan, "slope": np.nan, "clipped": count, "status": "undefined"}
    if len(np.unique(y)) != 2 or np.ptp(logit) == 0:
        result["status"] = "undefined: one class or constant scores"
        return result
    if logit[y == 0].max() <= logit[y == 1].min() or logit[y == 1].max() <= logit[y == 0].min():
        result["status"] = "undefined: separation/quasi-separation"
        return result
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", ConvergenceWarning)
            model = LogisticRegression(C=np.inf, solver="lbfgs", max_iter=1000, random_state=SEED)
            model.fit(logit.reshape(-1, 1), y)
        result.update(intercept=float(model.intercept_[0]), slope=float(model.coef_[0, 0]), status="OK")
    except ConvergenceWarning:
        result["status"] = "undefined: nonconvergence"
    return result


def reliability_rows(y, probability):
    """Quantile bins with aggregate supports; retain fewer bins when scores tie."""
    y, probability = np.asarray(y), np.asarray(probability)
    bins = np.asarray(pd.qcut(probability, q=10, labels=False, duplicates="drop"))
    if np.isnan(bins).all():
        bins = np.zeros(len(y))
    rows = []
    for number, value in enumerate(np.unique(bins), start=1):
        selected = bins == value
        rows.append((number, int(selected.sum()), int(y[selected].sum()),
                     float(probability[selected].mean()), float(y[selected].mean())))
    return rows


def bootstrap_intervals(y, probabilities, learned, repetitions=BOOTSTRAPS, progress=False):
    """Paired prediction-only resampling: never fit, retune or recalibrate here."""
    y = np.asarray(y)
    keys = tuple(probabilities)
    draws = np.full((repetitions, len(keys), len(INTERVAL_METRICS)), np.nan)
    rng = np.random.default_rng(SEED)
    undefined = 0
    for repeat in range(repetitions):
        indices = rng.integers(0, len(y), len(y))
        labels = y[indices]
        if len(np.unique(labels)) != 2:
            undefined += 1
            continue
        for column, key in enumerate(keys):
            scores = workflow_metrics(labels, probabilities[key][indices], learned[key][indices])
            draws[repeat, column] = [scores[name] for name in INTERVAL_METRICS]
        if progress and (repeat + 1) % 250 == 0:
            print(f"Bootstrap progress: {repeat + 1}/{repetitions}", flush=True)
    if undefined == repetitions:
        raise ValueError("All bootstrap resamples are undefined")
    absolute = {key: np.nanpercentile(draws[:, column], [2.5, 97.5], axis=0).T
                for column, key in enumerate(keys)}
    paired = {}
    for candidate in CANDIDATES:
        raw, sigmoid = (*candidate, "Raw"), (*candidate, "Sigmoid")
        if raw in keys and sigmoid in keys:
            delta = draws[:, keys.index(sigmoid)] - draws[:, keys.index(raw)]
            paired[candidate] = np.nanpercentile(delta, [2.5, 97.5], axis=0).T
    return absolute, paired, undefined


def label(key):
    return " / ".join(key)


def interval_text(interval):
    return f"[{interval[0]:.6f}, {interval[1]:.6f}]"


def write_report(y, probabilities, learned, thresholds, partitions, dummy, manifest_hash, fold_hash, intervals, paired, undefined):
    metrics = {key: workflow_metrics(y, probabilities[key], learned[key]) for key in WORKFLOWS}
    diagnostics = {key: calibration_diagnostic(y, probabilities[key]) for key in WORKFLOWS}
    probability_names = INTERVAL_METRICS[:4]
    fixed_rows, learned_rows, diagnostic_rows, threshold_rows = [], [], [], []
    for key in WORKFLOWS:
        scores = metrics[key]
        fixed_rows.append((label(key), *[f"{scores[name]:.6f}" for name in (*probability_names, "Sensitivity @0.50", "Specificity @0.50")],
                           *[scores[name] for name in ("TN", "FP", "FN", "TP")]))
        learned_rows.append((label(key), *[f"{scores[name + ' learned']:.6f}" for name in ("Sensitivity", "Specificity")],
                             *[scores[name + " learned"] for name in ("TN", "FP", "FN", "TP")]))
        diagnostic = diagnostics[key]
        diagnostic_rows.append((label(key), f"{diagnostic['intercept']:.6f}", f"{diagnostic['slope']:.6f}",
                                diagnostic["clipped"], diagnostic["status"]))
        values = [row[1] for row in thresholds[key]]
        threshold_rows.append((label(key), ", ".join(f"{value:.2f}" for value in values),
                               f"{min(values):.2f}", f"{np.median(values):.2f}", f"{max(values):.2f}",
                               sum(not row[3] for row in thresholds[key])))
    ranking = sorted(WORKFLOWS, key=lambda key: (metrics[key]["Brier"], key[2] != "Raw", key[0] != "Logistic", key[1] == "Full"))
    report = [
        f"# Development-only calibration and demonstration-threshold validation — {datetime.now(ZoneInfo('Asia/Kolkata')).date()}", "",
        "Owner approved docs/tabular_calibration_threshold_plan.md before implementation. Its historical pending status is preserved. No final model or deployment threshold selected.",
        "Command: `.venv/bin/python -B -m src.tabular.calibration_threshold_nhanes`.",
        f"Development N={len(y)}; Yes={int(y.sum())} ({y.mean():.6%}); No={int((y == 0).sum())}. Outcome: self-reported previous gum treatment, not current disease risk/diagnosis.", "",
        "## Approved recipe and preservation", "",
        "Logistic C=1/no weights and approved XGBoost A, each Full/Awareness-ablated. Four candidates × Raw/Sigmoid = eight workflows. Existing preprocessing/feature selectors/model parameters reused without historical edits.",
        "Five original outer folds; each outer-training fold split 80/20 (stratified, seed 42) into model/calibration and tuning pools. Three inner stratified folds (seed 42), sigmoid ensemble=False; 3 inner base fits + 1 pool refit per candidate/outer fold. Raw uses the exact same refitted estimator object as sigmoid. No separate raw fit, eval_set or early stopping.",
        "Recipe budget executed: 80 base-estimator fits (40 Logistic/40 XGBoost), 20 binary sigmoid fits, eight joint diagnostic attempts. Inner OOF scores/labels train calibration; independent tuning labels select thresholds; outer labels used only for validation metrics/diagnostics.",
        f"Frozen manifest hash: `{manifest_hash}`. Outer-fold hash: `{fold_hash}` — MATCH to historical evidence before any fit. Final held-out payloads never loaded/decoded/transformed/evaluated; selective development loading/zero repair reused. Historical code/reports/plans/manifest and existing tracked/untracked work preserved.",
        "New raw controls use smaller pool training sizes than historical experiments; no exact historical-metric reproduction is expected or claimed. Reduced inner-fit sizes also affect calibration score distributions; validate, do not assume calibration success.", "",
        "## All eight workflows — fixed threshold 0.50", "",
        markdown_table(("Workflow", *probability_names, "Sensitivity", "Specificity", "TN", "FP", "FN", "TP"), fixed_rows), "",
        "PR-AUC is trapezoidal; AP is separately defined. Threshold 0.50 is a reference only.", "",
        "## Fold-learned Youden demonstration thresholds", "",
        "Tuning grid 0.00–1.00 in 0.01 steps; maximise J, ties higher sensitivity then larger threshold. Exact integer confusion-count comparison avoids floating-point tie ambiguity. These are statistical demonstration thresholds, NOT clinically approved cutoffs. Each validation row uses its own fold's learned threshold, never a global average.",
        markdown_table(("Workflow", "Sensitivity", "Specificity", "TN", "FP", "FN", "TP"), learned_rows), "",
        markdown_table(("Workflow", "Thresholds folds 1–5", "Min", "Median", "Max", "Nonpositive tuning-J folds"), threshold_rows), "",
        "Any nonpositive-J fold is flagged as no useful tuning improvement; fixed 0.50 remains a reference, not a hidden successful fallback.", "",
        "## Calibration diagnostics", "",
        "Joint unpenalised regression y ~ intercept + slope × logit(p) on outer-OOF predictions, clipping only diagnostic logits at 1e-6. Ideal intercept=0/slope=1; these descriptive coefficients do not recalibrate scored probabilities. Joint intercept is not intercept-only calibration-in-the-large. Separation/nonconvergence is flagged, not silently penalised. Slope/intercept CIs remain pending.",
        markdown_table(("Workflow", "Joint intercept", "Slope", "Clipped", "Status"), diagnostic_rows), "",
        "## Paired bootstrap 95% intervals", "",
        f"1,000 participant resamples, seed 42; same indices across workflows. Undefined one-class resamples: {undefined}. Prediction-only: no model/calibrator/threshold refits. Conditional intervals omit training/selection variability, overlapping CV training dependence and survey design; not nationally representative uncertainty.",
    ]
    for names in (INTERVAL_METRICS[:4], INTERVAL_METRICS[4:]):
        report += ["", markdown_table(("Workflow", *names), [(label(key), *[interval_text(intervals[key][INTERVAL_METRICS.index(name)]) for name in names]) for key in WORKFLOWS])]
    report += ["", "Paired changes are Sigmoid minus Raw; negative Brier change indicates lower probability error. No causal/clinical superiority claim."]
    for names in (INTERVAL_METRICS[:4], INTERVAL_METRICS[4:]):
        report += ["", markdown_table(("Candidate", *names), [(label(candidate), *[
            f"{metrics[(*candidate, 'Sigmoid')][name] - metrics[(*candidate, 'Raw')][name]:.6f} {interval_text(paired[candidate][INTERVAL_METRICS.index(name)])}" for name in names]) for candidate in CANDIDATES])]
    report += ["", "## Matched training-rate reference", "",
               "Prior probabilities computed from each model/calibration pool, assigned to its outer validation rows; five prior calculations, no extra model fits. Historical Dummy results remain untouched.",
               markdown_table(tuple(score_predictions(y, dummy)), [tuple(f"{value:.6f}" if isinstance(value, float) else value for value in score_predictions(y, dummy).values())]), "",
               "## Reliability tables — ten quantile bins requested", ""]
    for key in WORKFLOWS:
        rows = reliability_rows(y, probabilities[key])
        report += [f"### {label(key)} — {len(rows)} actual bins", "",
                   markdown_table(("Bin", "N", "Yes", "Mean probability", "Observed Yes fraction"),
                                  [(bin_id, n, yes, f"{mean:.6f}", f"{observed:.6f}") for bin_id, n, yes, mean, observed in rows]), ""]
    report += ["## Fold/inner-pool supports", "",
               markdown_table(("Fold", "Pool N", "Pool Yes", "Tuning N", "Tuning Yes", "Validation N", "Validation Yes", "Inner membership hash"), partitions), "",
               "## Provisional probability-error ordering and limitations", "",
               "Lowest pooled Brier is a provisional probability-calibration ranking ONLY, not automatic final-model selection. Lower Brier alone does not establish better calibration. Read discrimination, diagnostics, false positives/negatives and threshold trade-offs together.",
               "; ".join(f"{i}. {label(key)} ({metrics[key]['Brier']:.6f})" for i, key in enumerate(ranking, start=1)),
               "All workflows are reported. Earlier candidate shortlisting and choosing among these development results introduce selection optimism; nested calibration/tuning boundaries do not erase earlier selection. Bootstrap intervals do not fix that optimism. No clinically approved cutoff, final model, calibrated personal-risk claim or deployment threshold.",
               "Remaining work: owner review of all trade-offs; separately approved final development preparation/freeze; diagnostic intervals and survey sensitivity; SHAP/what-if and independent vision work. Final held-out evaluation remains reserved until all choices are frozen and separately authorised.",
               f"Runtime: Python {platform.python_version()}; pandas {pd.__version__}; numpy {np.__version__}; scikit-learn {sklearn.__version__}; XGBoost 3.4.1 verified before fitting. No installations, datasets/models written, commits or pushes.", ""]
    REPORT.write_text("\n".join(report), encoding="utf-8")
    print(markdown_table(("Workflow", *probability_names, "Sensitivity @0.50", "Specificity @0.50", "TN", "FP", "FN", "TP"), fixed_rows))
    print(markdown_table(("Workflow", "Sensitivity learned", "Specificity learned", "TN", "FP", "FN", "TP"), learned_rows))
    print(markdown_table(("Workflow", "Joint intercept", "Slope", "Clipped", "Status"), diagnostic_rows))
    print("Report:", REPORT, flush=True)


def main():
    verify_xgboost_plan((ROOT / "docs" / "tabular_xgboost_plan.md").read_text())
    historical = (ROOT / "docs" / "tabular_logistic_comparison.md").read_text()
    match = re.search(r"Ordered validation-fold SEQN membership SHA-256: `([a-f0-9]{64})`", historical)
    if match is None:
        raise ValueError("Missing historical outer-fold fingerprint")
    x, y, manifest_hash = load_development()
    if manifest_hash not in historical:
        raise ValueError("Frozen manifest differs from historical evidence")
    print("Fitting approved four-candidate nested validation recipe...", flush=True)
    probabilities, learned, thresholds, partitions, dummy = run_validation(x, y, match.group(1))
    print("Outer OOF predictions complete; starting 1,000 paired prediction-only bootstrap resamples...", flush=True)
    intervals, paired, undefined = bootstrap_intervals(y, probabilities, learned, progress=True)
    write_report(y, probabilities, learned, thresholds, partitions, dummy, manifest_hash, match.group(1), intervals, paired, undefined)


if __name__ == "__main__":
    main()
