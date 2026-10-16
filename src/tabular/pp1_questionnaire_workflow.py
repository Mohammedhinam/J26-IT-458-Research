"""Bounded development comparison, cross-fitted SHAP and local reference bundle.

Run once: .venv/bin/python -B -m src.tabular.pp1_questionnaire_workflow
Existing reports and frozen membership are never overwritten.
"""

from datetime import datetime
import hashlib
import json
from pathlib import Path
import platform
import time
from zoneinfo import ZoneInfo

import joblib
import numpy as np
import pandas as pd
import shap
import sklearn
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.model_selection import StratifiedKFold
import xgboost

from .baseline_nhanes import ROOT, load_development, score_predictions, markdown_table
from .calibration_threshold_nhanes import calibration_diagnostic, reliability_rows
from .logistic_comparison_nhanes import metric_text, verify_reproduction
from .preprocess_nhanes import FEATURES
from .questionnaire_explain import (
    EXAMPLE_PROFILE, NOTICE, QuestionnairePrototype, explain_frame, fit_support,
)
from .xgboost_comparison_nhanes import make_xgboost_pipeline, fold_fingerprint, reference_row


MANIFEST_HASH = "4d0f82149cb20485186ad929fca0a070a72fe4e4a3032b1cf8da37954c131551"
FOLD_HASH = "0822ca63d5ffa57375141ae15d97ca08333a207463eae909237892dbe9e3adb0"
SETTINGS = {
    "A_reference": {},
    "A_short": {"n_estimators": 100},
    "A_long": {"n_estimators": 400},
    "A_long_regularized": {"n_estimators": 400, "reg_lambda": 5.0},
    "A_long_child5": {"n_estimators": 400, "min_child_weight": 5.0},
    "A_balanced": {"scale_pos_weight": "training_fold_ratio"},
}
PLAN = ROOT / "docs/tabular_pp1_completion_plan_v1.md"
REPORT = ROOT / "docs/tabular_pp1_completion_results_v1.md"
AGGREGATE = ROOT / "docs/tabular_pp1_completion_results_v1.json"
LOCAL = ROOT / "data/tabular_pp1_v1"
MODEL_DIR = ROOT / "models/questionnaire_pp1_v1"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def make_model(name, training_y):
    if name not in SETTINGS:
        raise ValueError("Setting is outside the frozen bounded comparison")
    model = make_xgboost_pipeline(("Full", "A"))
    parameters = dict(SETTINGS[name])
    if name == "A_balanced":
        positives = int(np.sum(np.asarray(training_y) == 1))
        negatives = int(np.sum(np.asarray(training_y) == 0))
        if min(positives, negatives) == 0:
            raise ValueError("Class weighting needs both training classes")
        parameters["scale_pos_weight"] = negatives / positives
    model.named_steps["classifier"].set_params(**parameters)
    return model


def run_bounded(x, y, expected_fold_hash, historical=None, progress=False):
    """One fixed fold map, one fresh pipeline per fit; scored labels never fit."""
    if tuple(x.columns) != FEATURES or not x.index.equals(y.index) or not x.index.is_unique:
        raise ValueError("Expected aligned unique participants and the existing allowlist")
    if not y.isin((0, 1)).all() or y.value_counts().reindex([0, 1], fill_value=0).min() < 5:
        raise ValueError("Each binary class needs five development participants")
    folds = tuple(StratifiedKFold(5, shuffle=True, random_state=42).split(x, y))
    if fold_fingerprint(x, folds) != expected_fold_hash:
        raise ValueError("Frozen fold membership mismatch")
    scores, probabilities, fold_settings = {}, {}, []
    shap_values = np.full((len(x), len(FEATURES)), np.nan)
    shap_checks = []
    for name in SETTINGS:
        started = time.monotonic()
        p, coverage = np.full(len(y), np.nan), np.zeros(len(y), dtype=int)
        for fold, (train, validation) in enumerate(folds, 1):
            if np.intersect1d(train, validation).size:
                raise ValueError("Train/validation overlap")
            model = make_model(name, y.iloc[train])
            model.fit(x.iloc[train], y.iloc[train])
            p[validation] = model.predict_proba(x.iloc[validation])[:, 1]
            coverage[validation] += 1
            fold_settings.append({"configuration": name, "fold": fold,
                                  "positive_weight": model.named_steps["classifier"].get_params()["scale_pos_weight"]})
            if name == "A_reference":
                explanation = explain_frame(model, x.iloc[validation])
                shap_values[validation] = explanation["contributions"]
                shap_checks.append(explanation["checks"])
        if not np.all(coverage == 1):
            raise ValueError("Missing or repeated OOF predictions")
        scores[name] = score_predictions(y, p)
        probabilities[name] = p
        if name == "A_reference" and historical is not None:
            verify_reproduction(scores[name], historical)
        if progress:
            print(name, json.dumps(scores[name]), f"seconds={time.monotonic()-started:.2f}", flush=True)
    if not np.isfinite(shap_values).all():
        raise ValueError("Incomplete cross-fitted explanation coverage")
    return scores, probabilities, shap_values, shap_checks, fold_settings


def paired_intervals(y, predictions, repetitions=1000):
    """Paired, stratified prediction resampling; no model refitting or tuning."""
    y = np.asarray(y)
    strata = [np.flatnonzero(y == label) for label in (0, 1)]
    if not all(len(group) for group in strata) or repetitions < 1:
        raise ValueError("Bootstrap needs two classes and positive repetitions")
    generator = np.random.default_rng(42)
    draws = {name: [] for name in predictions if name != "A_reference"}
    for _ in range(repetitions):
        ids = np.concatenate([generator.choice(group, len(group), replace=True) for group in strata])
        labels = y[ids]
        ref = np.asarray(predictions["A_reference"])[ids]
        reference = (roc_auc_score(labels, ref), brier_score_loss(labels, ref))
        for name in draws:
            probability = np.asarray(predictions[name])[ids]
            draws[name].append((roc_auc_score(labels, probability) - reference[0],
                                brier_score_loss(labels, probability) - reference[1]))
    return {name: {"delta_auroc_95": np.quantile(values, [0.025, 0.975], axis=0)[:, 0].tolist(),
                   "delta_brier_95": np.quantile(values, [0.025, 0.975], axis=0)[:, 1].tolist()}
            for name, values in draws.items()}


def main():
    # Refuse accidental repeats and freeze evidence before reading development rows.
    if any(path.exists() for path in (REPORT, AGGREGATE, LOCAL, MODEL_DIR)):
        raise FileExistsError("Version v1 already has output; inspect it rather than rerunning")
    if not PLAN.exists():
        raise ValueError("The prospective recipe must exist before execution")
    protected = [ROOT / "data/preprocessing/split_manifest.json"]
    protected += [ROOT / "docs" / name for name in (
        "nhanes_audit.md", "tabular_preprocessing.md", "tabular_logistic_comparison.md",
        "tabular_xgboost_comparison.md", "tabular_calibration_threshold_results.md")]
    before = {str(path.relative_to(ROOT)): sha256(path) for path in protected}
    if before["data/preprocessing/split_manifest.json"] != MANIFEST_HASH:
        raise ValueError("Manifest hash mismatch before development loading")
    x, y, manifest_hash = load_development()
    if manifest_hash != MANIFEST_HASH or len(y) != 6251 or int(y.sum()) != 1553:
        raise ValueError("Frozen development cohort mismatch")
    old = (ROOT / "docs/tabular_xgboost_comparison.md").read_text()
    metric_names = tuple(score_predictions([0, 1], [0.2, 0.8]))
    historical = dict(zip(metric_names, reference_row(old, "| Features |", "| Full | A |", metric_names)))
    scores, predictions, contributions, checks, fold_settings = run_bounded(x, y, FOLD_HASH, historical, True)
    print("Comparison complete; paired prediction-only intervals...", flush=True)
    intervals = paired_intervals(y, predictions)
    # The demonstration remains the predeclared reference, never an automatic winner.
    reference = make_model("A_reference", y)
    reference.fit(x, y)
    source_paths = sorted((ROOT / "src/tabular").glob("*.py"))
    source_hashes = {str(path.relative_to(ROOT)): sha256(path) for path in source_paths}
    provenance = {"role": "development reference only", "manifest_sha256": manifest_hash,
                  "fold_sha256": FOLD_HASH, "plan_sha256": sha256(PLAN),
                  "source_hashes": source_hashes, "final_model": False, "held_out_evaluated": False}
    prototype = QuestionnairePrototype(reference, fit_support(x), provenance)
    example = prototype.predict(EXAMPLE_PROFILE)
    scenario = prototype.simulate(EXAMPLE_PROFILE, {"SMOKING_STATUS": "former", "OHQ870": 7}, prototype.model_id)
    reset = prototype.reset(EXAMPLE_PROFILE, prototype.model_id)
    if reset["scenario"]["probability"] != example["probability"]:
        raise ValueError("Reset did not reproduce the original probability")
    after = {str(path.relative_to(ROOT)): sha256(path) for path in protected}
    if before != after:
        raise ValueError("Historical evidence or frozen manifest changed")

    LOCAL.mkdir(parents=True)
    MODEL_DIR.mkdir(parents=True)
    np.savez_compressed(LOCAL / "development_oof.npz", SEQN=x.index.to_numpy(), y=y.to_numpy(), **predictions)
    model_path = MODEL_DIR / "model.joblib"
    joblib.dump(prototype, model_path)
    model_hash = sha256(model_path)
    loaded = joblib.load(model_path)  # Only our own newly written local artifact.
    if loaded.predict(EXAMPLE_PROFILE) != example:
        raise ValueError("Saved reference failed exact reload verification")
    mean_absolute = np.abs(contributions).mean(axis=0)
    result = {
        "date": str(datetime.now(ZoneInfo("Asia/Kolkata")).date()), "notice": NOTICE,
        "development_n": len(y), "positive_n": int(y.sum()), "scores": scores,
        "bootstrap": {"repetitions": 1000, "method": "paired outcome-stratified prediction-only", "deltas": intervals},
        "shap": {"rows": len(x), "input_count": len(FEATURES), "encoded_count": 47,
                 "units": "raw log-odds", "fold_checks": checks,
                 "mean_absolute_grouped_contribution": dict(zip(FEATURES, mean_absolute.tolist()))},
        "calibration_diagnostics": {name: calibration_diagnostic(y, p) for name, p in predictions.items()},
        "reference_reliability_bins": reliability_rows(y, predictions["A_reference"]),
        "fictional_example": example, "fictional_scenario": scenario,
        "reset_exact": True, "saved_model_reload_exact": True, "model_sha256": model_hash,
        "oof_sha256": sha256(LOCAL / "development_oof.npz"), "provenance": provenance,
        "protected_evidence_unchanged": before == after, "fold_settings": fold_settings,
        "runtime": {"python": platform.python_version(), "numpy": np.__version__,
                    "pandas": pd.__version__, "sklearn": sklearn.__version__,
                    "xgboost": xgboost.__version__, "shap": shap.__version__},
    }
    AGGREGATE.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    (MODEL_DIR / "provenance.json").write_text(json.dumps({**provenance, "model_sha256": model_hash}, indent=2) + "\n")
    rows = [(name, *[metric_text(value) for value in measured.values()]) for name, measured in scores.items()]
    leading = max(scores, key=lambda name: scores[name]["AUROC"])
    report = [
        "# Questionnaire PP1 development completion — " + result["date"], "", NOTICE, "",
        "Prospective recipe: `tabular_pp1_completion_plan_v1.md`. Historical files and frozen manifest unchanged.",
        "6,251 development participants (1,553 Yes); original five folds; 30 CV fits plus one reference demonstration fit. No held-out payloads decoded/evaluated. All ten XGBoost A reference metrics reproduced to six decimals/counts exactly.", "",
        markdown_table(("Configuration", *metric_names), rows), "",
        f"Numerical AUROC leader: {leading}; difference versus A = {scores[leading]['AUROC']-scores['A_reference']['AUROC']:.6f}. This is development selection, not a final winner or independent superiority finding.",
        "No final threshold selected; 0.50 is the existing comparison only. AUROC 0.80 is " + ("reached internally, not final validation." if scores[leading]["AUROC"] >= 0.8 else "not achieved."), "",
        "## Paired prediction-only 95% intervals", "",
        markdown_table(("Configuration", "AUROC delta interval", "Brier delta interval"),
                       [(name, interval["delta_auroc_95"], interval["delta_brier_95"]) for name, interval in intervals.items()]),
        "1,000 fixed-seed outcome-stratified draws. Positive AUROC / negative Brier differences favour a candidate. Conditional intervals omit model refitting, search selection, multiplicity and complex survey uncertainty; no national-population or clinical claims.", "",
        "## Working explanation and What-if", "",
        "TreeSHAP computed on all 6,251 unseen-fold rows for reference A, 47 encoded columns grouped to 12 inputs. All raw-margin, probability and native-contribution checks pass 1e-5; raw log-odds units are explicit. No calibrated-percentage or causal attribution claim.",
        markdown_table(("Input", "Mean absolute grouped log-odds contribution"), sorted(zip(FEATURES, mean_absolute), key=lambda row: -row[1])), "",
        f"Fictional example probability: {example['probability']:.8f}; hypothetical former smoking/7 cleaning days: {scenario['scenario']['probability']:.8f}. This is model response, not an expected health improvement or evidence that past treatment can change.",
        "Reset and saved-model reload reproduce the original exactly. Only the existing reference A powers the demo. Age/history/outcome remain protected; unsupported lifetime-smoking changes are rejected; development category/pair support warnings are disclosed.",
        "The reference is raw, not separately calibrated; the existing calibration study showed no automatic XGBoost Brier improvement. Calibration diagnostics/reliability bins are in the aggregate JSON, not applied as a new probability mapping.", "",
        f"Local model: `models/questionnaire_pp1_v1/model.joblib`, SHA256 `{model_hash}`. Local OOF rows: `data/tabular_pp1_v1/development_oof.npz`. Both ignored; no data/model commit.",
        "## Remaining scientific completion", "",
        "Final model/calibration/threshold freeze, untouched held-out evaluation, complex-survey sensitivity, subgroup checks and user comprehension/usability measurement remain pending. Working functions do not establish validated personal probability or Sri Lankan transportability. Original research proposal remains unchanged.", "",
        "Runtime: " + json.dumps(result["runtime"]), "",
    ]
    REPORT.write_text("\n".join(report))
    print("Saved", REPORT, "\nModel SHA256", model_hash, flush=True)


if __name__ == "__main__":
    main()
